import requests
import psycopg2
import os
import random
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
cur = conn.cursor()


users = requests.get("https://dummyjson.com/users?limit=50").json()["users"]
for u in users:
    cur.execute("""
        INSERT INTO customers (customer_id, first_name, last_name, email, signup_date, country)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (customer_id) DO NOTHING
    """, (
        u["id"], u["firstName"], u["lastName"], u["email"],
        datetime.now() - timedelta(days=random.randint(30, 1000)),
        u["address"]["country"] if "country" in u["address"] else "Unknown"
    ))


products = requests.get("https://dummyjson.com/products?limit=0").json()["products"]
for p in products:
    cur.execute("""
        INSERT INTO products (product_id, product_name, category, price, stock_quantity)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (product_id) DO NOTHING
    """, (p["id"], p["title"], p["category"], p["price"], p["stock"]))


carts = requests.get("https://dummyjson.com/carts?limit=50").json()["carts"]
statuses = ["pending", "shipped", "delivered", "cancelled"]

for cart in carts:
    order_date = datetime.now() - timedelta(days=random.randint(0, 365))
    status = random.choice(statuses)
    cur.execute("""
        INSERT INTO orders (order_id, customer_id, order_date, status)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (order_id) DO NOTHING
    """, (cart["id"], cart["userId"], order_date, status))

    for item in cart["products"]:
        cur.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            VALUES (%s, %s, %s, %s)
        """, (cart["id"], item["id"], item["quantity"], item["price"]))

conn.commit()


cur.execute("""
    SELECT o.order_id, o.order_date, SUM(oi.quantity * oi.unit_price) as total
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY o.order_id, o.order_date
""")
methods = ["credit_card", "paypal", "bank_transfer", "cash_on_delivery"]

for order_id, order_date, total in cur.fetchall():
    cur.execute("""
        INSERT INTO payments (order_id, payment_date, amount, payment_method, payment_status)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        order_id, order_date + timedelta(hours=random.randint(1, 48)),
        total, random.choice(methods), random.choice(["completed", "failed", "refunded"])
    ))

conn.commit()
cur.close()
conn.close()
print("Data loaded successfully.")