# generate_raw_data.py
from faker import Faker
import pandas as pd
import random

fake = Faker()

# customers_raw.csv
customers = []
for i in range(1, 301):
    customers.append({
        "customer_id": i,
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email() if random.random() > 0.05 else None,  # some missing emails
        "signup_date": fake.date_between(start_date="-2y", end_date="today"),
        "country": fake.country()
    })
pd.DataFrame(customers).to_csv("customers_raw.csv", index=False)

# products_raw.csv
categories = ["Electronics", "Clothing", "Home", "Beauty", "Sports"]
products = []
for i in range(1, 301):
    products.append({
        "product_id": i,
        "product_name": fake.catch_phrase(),
        "category": random.choice(categories),
        "price": round(random.uniform(5, 500), 2),
        "stock_quantity": random.randint(-5, 500)  # negative = intentional bad data
    })
pd.DataFrame(products).to_csv("products_raw.csv", index=False)

# orders_raw.csv (with intentional dirt: duplicates, bad FKs, nulls)
orders = []
for i in range(1, 351):  # extra rows so we can inject dupes below
    orders.append({
        "order_id": i,
        "customer_id": random.choice([random.randint(1, 300), random.randint(290, 320)]),  # some invalid FK
        "product_id": random.randint(1, 320),  # some invalid FK
        "quantity": random.choice([1, 2, 3, -1]),  # -1 = bad data
        "order_date": fake.date_between(start_date="-1y", end_date="today") if random.random() > 0.03 else None,
        "status": random.choice(["pending", "shipped", "delivered", "cancelled", None])
    })
# inject some exact duplicate rows
orders += random.sample(orders, 15)
pd.DataFrame(orders).to_csv("orders_raw.csv", index=False)

print("Raw CSVs generated.")