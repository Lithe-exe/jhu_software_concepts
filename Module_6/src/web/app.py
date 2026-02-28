import os
from pathlib import Path
from flask import Flask, render_template, jsonify, flash, request
from src.web.publisher import publish_task
import psycopg

SRC_DIR = Path(__file__).resolve().parents[1]
BOARD_DIR = SRC_DIR / "board"

def get_db_connection():
    return psycopg.connect(os.environ["DATABASE_URL"])

def create_app():
    app = Flask(
        __name__,
        template_folder=str(BOARD_DIR / "templates"),
        static_folder=str(BOARD_DIR / "static"),
    )
    app.secret_key = 'secret'

    @app.route('/')
    @app.route('/analysis')
    def index():
        # Fetch latest analytics from the cache table (populated by worker)
        data = {}
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # We expect the worker to save analysis as a JSON blob or specific fields
                    # For simplicity, we'll try to read a stored JSON blob if it exists,
                    # or fallback to "Pending"
                    cur.execute("CREATE TABLE IF NOT EXISTS analysis_cache (id SERIAL PRIMARY KEY, data JSONB, updated_at TIMESTAMP DEFAULT NOW())")
                    cur.execute("SELECT data FROM analysis_cache ORDER BY updated_at DESC LIMIT 1")
                    row = cur.fetchone()
                    if row:
                        data = row[0]
        except Exception as e:
            print(f"DB Error: {e}")
            
        return render_template('index.html', data=data)

    @app.route('/pull-data', methods=['POST'])
    def pull_data():
        try:
            publish_task("scrape_new_data", {})
            return jsonify({"status": "queued", "task": "scrape_new_data"}), 202
        except Exception as e:
            return jsonify({"error": str(e)}), 503

    @app.route('/update-analysis', methods=['POST'])
    def update_analysis():
        try:
            publish_task("recompute_analytics", {})
            return jsonify({"status": "queued", "task": "recompute_analytics"}), 202
        except Exception as e:
            return jsonify({"error": str(e)}), 503

    return app
