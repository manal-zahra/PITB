import psycopg2

conn = psycopg2.connect(
    dbname="PITB",
    user="postgres",
    password="Right&92",  # <-- Put your actual PostgreSQL password here
    host="localhost",
    port="5432"
)
cur = conn.cursor()

print("Applying Star-Schema Warehouse Transformations...")

# 1. Orders => CTE Deduplication + UPSERT
cur.execute("""
WITH ranked_orders AS (
    SELECT 
        order_id, customer_id, product_id, amount, status, event_timestamp,
        ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY ingested_at DESC) AS rnk
    FROM stg_orders_stream
)
INSERT INTO fact_orders (order_id, customer_id, product_id, amount, status, order_timestamp)
SELECT order_id, customer_id, product_id, amount, status, event_timestamp
FROM ranked_orders
WHERE rnk = 1
ON CONFLICT (order_id) DO UPDATE 
SET amount = EXCLUDED.amount,
    status = EXCLUDED.status;
""")

# 2. activity => CTE Deduplication and Insert
cur.execute("""
WITH ranked_activity AS (
    SELECT 
        event_id, customer_id, page_url, session_duration, event_timestamp,
        ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY ingested_at DESC) AS rnk
    FROM stg_activity_stream
)
INSERT INTO fact_user_activity (event_id, customer_id, page_url, session_duration, event_timestamp)
SELECT event_id, customer_id, page_url, session_duration, event_timestamp
FROM ranked_activity
WHERE rnk = 1
ON CONFLICT (event_id) DO NOTHING;
""")

conn.commit()
print("Warehouse Fact tables populated successfully!")
cur.close()
conn.close()