import sys
import os
import json
import time
import pika
import psycopg
from datetime import datetime

# Path setup to import siblings
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.worker.etl.scrape import GradCafeScraper
from src.worker.etl.clean import DataCleaner
from src.worker.etl.query_data import DataAnalyzer
from src.db.load_data import load_from_list, get_last_seen_date, update_watermark, ensure_tables

RABBITMQ_URL = os.environ.get("RABBITMQ_URL")
DATABASE_URL = os.environ.get("DATABASE_URL")
SEED_JSON_PATH = os.environ.get("SEED_JSON_PATH")

def get_db_conn():
    return psycopg.connect(DATABASE_URL)


def auto_seed_if_needed():
    """
    Auto-load seed JSON into applicants on startup when table is empty.
    """
    if not SEED_JSON_PATH:
        print(" [*] Seed path not configured; skipping auto-seed.")
        return

    if not os.path.exists(SEED_JSON_PATH):
        print(f" [*] Seed file not found at {SEED_JSON_PATH}; skipping auto-seed.")
        return

    try:
        with open(SEED_JSON_PATH, "r", encoding="utf-8") as file_handle:
            seed_data = json.load(file_handle)
    except Exception as seed_read_error:  # pylint: disable=broad-except
        print(f" [!] Failed to read seed JSON: {seed_read_error}")
        return

    if not isinstance(seed_data, list):
        print(" [!] Seed JSON is not a list; skipping auto-seed.")
        return

    try:
        with get_db_conn() as conn:
            ensure_tables(conn)
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM applicants")
                existing_count = cur.fetchone()[0]

            if existing_count > 0:
                print(f" [*] Applicants already populated ({existing_count} rows); skipping seed.")
                return

            load_from_list(conn, seed_data)
            conn.commit()
            print(f" [*] Auto-seeded applicants with {len(seed_data)} rows from {SEED_JSON_PATH}")
    except Exception as seed_load_error:  # pylint: disable=broad-except
        print(f" [!] Failed to auto-seed DB: {seed_load_error}")

def handle_scrape_new_data(ch, method, properties, body):
    print(" [x] Handling scrape_new_data")
    
    # 1. Get Watermark (Last seen date)
    last_seen = get_last_seen_date()
    print(f"     Last seen date: {last_seen}")

    # 2. Scrape
    # Initialize scraper with shared volume path or just use memory
    scraper = GradCafeScraper(output_file=None, debug=True)
    # We pass the last_seen date to the scraper so it stops early
    raw_data = scraper.scrape_data(target_count=50, max_pages=5, stop_date=last_seen)
    
    if not raw_data:
        print("     No new data found.")
        return

    # 3. Clean
    cleaner = DataCleaner(input_file=None, output_file=None)
    cleaned_data = cleaner.clean_data(raw_data)

    # 4. Load to DB & Update Watermark
    with get_db_conn() as conn:
        with conn.transaction():
            load_from_list(conn, cleaned_data)
            
            # Update watermark to the most recent date found in this batch
            # Assuming raw_data is sorted or we find the max date
            # Simplified: just taking the first one if they are ordered by date desc
            if raw_data:
                newest_date = raw_data[0].get('raw_date')
                if newest_date:
                    update_watermark(conn, newest_date)
                    print(f"     Updated watermark to: {newest_date}")

def handle_recompute_analytics(ch, method, properties, body):
    print(" [x] Handling recompute_analytics")
    
    analyzer = DataAnalyzer()
    # Ensure tables exist just in case
    with get_db_conn() as conn:
        ensure_tables(conn)

    # Run queries
    results = analyzer.get_analysis(limit=100)
    
    # Save results to analysis_cache table
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO analysis_cache (data) VALUES (%s)", (json.dumps(results),))
            conn.commit()
    print("     Analytics recomputed and cached.")

def main():
    print(" [*] Connecting to RabbitMQ...")
    # Retry logic for startup
    while True:
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            break
        except pika.exceptions.AMQPConnectionError:
            print("     Broker not ready, retrying in 5s...")
            time.sleep(5)

    channel.exchange_declare(exchange='tasks', exchange_type='direct', durable=True)
    channel.queue_declare(queue='tasks_q', durable=True)
    channel.queue_bind(exchange='tasks', queue='tasks_q', routing_key='tasks')

    channel.basic_qos(prefetch_count=1)

    def on_request(ch, method, props, body):
        payload = json.loads(body)
        kind = payload.get("kind")
        
        try:
            if kind == "scrape_new_data":
                handle_scrape_new_data(ch, method, props, body)
            elif kind == "recompute_analytics":
                handle_recompute_analytics(ch, method, props, body)
            else:
                print(f" [!] Unknown task: {kind}")
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f" [!] Error processing {kind}: {e}")
            # Requeue=False to prevent infinite loop on poison messages
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(queue='tasks_q', on_message_callback=on_request)

    print(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == '__main__':
    # Initialize DB schema on startup
    try:
        with get_db_conn() as conn:
            ensure_tables(conn)
        auto_seed_if_needed()
    except Exception as e:
        print(f"Init DB Error: {e}")
        
    main()
