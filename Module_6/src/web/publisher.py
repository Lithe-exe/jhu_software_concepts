import os
import json
import pika
import datetime

EXCHANGE = "tasks"
QUEUE = "tasks_q"
ROUTING_KEY = "tasks"

def _open_channel():
    url = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F")
    params = pika.URLParameters(url)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    
    # Durable declarations
    ch.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    ch.queue_declare(queue=QUEUE, durable=True)
    ch.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)
    
    return conn, ch

def publish_task(kind: str, payload: dict = None):
    if payload is None:
        payload = {}
        
    msg = {
        "kind": kind,
        "ts": datetime.datetime.utcnow().isoformat(),
        "payload": payload
    }
    
    body = json.dumps(msg)
    conn, ch = _open_channel()
    
    try:
        ch.basic_publish(
            exchange=EXCHANGE,
            routing_key=ROUTING_KEY,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2, # Persistent
                content_type='application/json'
            )
        )
    finally:
        conn.close()