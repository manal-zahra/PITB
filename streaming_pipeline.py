import time
import random
import queue
import threading
from datetime import datetime
import psycopg2
from faker import Faker

fake = Faker()

# Pointing to your local PITB database
DB_CONFIG = {
    "dbname": "PITB",
    "user": "postgres",
    "password": "Right&92",  
    "host": "localhost",
    "port": "5432"
}

# In-memory broker queues (simulating Kafka topics)
orders_topic = queue.Queue()
activity_topic = queue.Queue()

# --- WEEK 3 & 4: STREAM 1 (ORDERS PRODUCER) ---
def orders_producer():
    print("[Producer 1] Orders stream active...")
    req_count = 0
    while True:
        # Week 4 Rate Limiting simulation: throttle every 25 requests
        req_count += 1
        if req_count % 25 == 0:
            time.sleep(1.5)

        order_event = {
            "order_id": fake.uuid4(),
            "customer_id": random.randint(1, 100),
            "product_id": random.randint(1, 50),
            "amount": round(random.uniform(15.0, 450.0), 2),
            "status": random.choice(["COMPLETED", "PENDING", "CANCELLED"]),
            "timestamp": datetime.now().isoformat()
        }
        orders_topic.put(order_event)
        time.sleep(0.4)

# --- WEEK 4: STREAM 2 (WEB ACTIVITY PRODUCER WITH EDGE CASES) ---
def activity_producer():
    print("[Producer 2] Web activity stream active...")
    while True:
        # Simulate real-world bad data (10% chance of corrupt record)
        corrupt_record = random.random() < 0.10

        activity_event = {
            "event_id": fake.uuid4(),
            "customer_id": None if corrupt_record else random.randint(1, 100),
            "page_url": random.choice(["/home", "/catalog", "/product/detail", "/cart", "/checkout"]),
            "session_duration": -10 if corrupt_record else random.randint(5, 300),
            "timestamp": datetime.now().isoformat()
        }
        activity_topic.put(activity_event)
        time.sleep(0.6)

# --- STREAM CONSUMER (WRITES DIRECTLY TO POSTGRESQL LANDING TABLES) ---
def stream_consumer():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("[Consumer] Connected to PostgreSQL (PITB). Ingesting streaming events...")

    while True:
        # Process Orders stream
        while not orders_topic.empty():
            data = orders_topic.get()
            cur.execute("""
                INSERT INTO stg_orders_stream (order_id, customer_id, product_id, amount, status, event_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (data["order_id"], data["customer_id"], data["product_id"], data["amount"], data["status"], data["timestamp"]))
            conn.commit()
            print(f"[Stream 1] Ingested Order: {data['order_id'][:8]} | ${data['amount']}")

        # Process Activity stream (Week 4: Data Quality Cleaning)
        while not activity_topic.empty():
            data = activity_topic.get()
            
            # Reject invalid records before staging
            if data["customer_id"] is None or data["session_duration"] < 0:
                print(f"[DQ Filter] Dropped corrupt event: {data['event_id'][:8]}")
                continue

            cur.execute("""
                INSERT INTO stg_activity_stream (event_id, customer_id, page_url, session_duration, event_timestamp)
                VALUES (%s, %s, %s, %s, %s);
            """, (data["event_id"], data["customer_id"], data["page_url"], data["session_duration"], data["timestamp"]))
            conn.commit()
            print(f"[Stream 2] Ingested Page View: {data['event_id'][:8]} -> {data['page_url']}")

        time.sleep(0.3)

if __name__ == "__main__":
    t1 = threading.Thread(target=orders_producer, daemon=True)
    t2 = threading.Thread(target=activity_producer, daemon=True)
    t3 = threading.Thread(target=stream_consumer, daemon=True)

    t1.start()
    t2.start()
    t3.start()

    print("\n--- Pipeline Running. Streaming live events to PostgreSQL ---")
    print("Let it run for 40-60 seconds, then press Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStreaming paused.")