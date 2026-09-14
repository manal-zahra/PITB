import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

revenue_by_category = pd.read_sql("""
    SELECT p.category, SUM(oi.quantity * oi.unit_price) AS total_revenue
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.category
    ORDER BY total_revenue DESC
""", conn)
revenue_by_category["report_section"] = "revenue_per_category"

top_customers = pd.read_sql("""
    SELECT c.customer_id, c.first_name || ' ' || c.last_name AS customer_name,
           SUM(pay.amount) AS total_spent
    FROM payments pay
    JOIN orders o ON pay.order_id = o.order_id
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE pay.payment_status = 'completed'
    GROUP BY c.customer_id, c.first_name, c.last_name
    ORDER BY total_spent DESC
    LIMIT 5
""", conn)
top_customers["report_section"] = "top_5_customers"

orders_by_status = pd.read_sql("""
    SELECT status, COUNT(*) AS order_count
    FROM orders
    GROUP BY status
    ORDER BY order_count DESC
""", conn)
orders_by_status["report_section"] = "orders_by_status"

mom_revenue = pd.read_sql("""
    WITH monthly_revenue AS (
        SELECT DATE_TRUNC('month', payment_date) AS month, SUM(amount) AS revenue
        FROM payments
        WHERE payment_status = 'completed'
        GROUP BY DATE_TRUNC('month', payment_date)
    )
    SELECT month, revenue,
           LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue,
           ROUND(
               (revenue - LAG(revenue) OVER (ORDER BY month))
               / NULLIF(LAG(revenue) OVER (ORDER BY month), 0) * 100, 2
           ) AS pct_change
    FROM monthly_revenue
    ORDER BY month
""", conn)
mom_revenue["report_section"] = "month_over_month_revenue"

conn.close()

combined = pd.concat(
    [revenue_by_category, top_customers, orders_by_status, mom_revenue],
    ignore_index=True, sort=False
)

combined.to_csv("weekly_sales_report.csv", index=False)

print("Report sections generated:")
print(f"- Revenue per category: {len(revenue_by_category)} rows")
print(f"- Top 5 customers: {len(top_customers)} rows")
print(f"- Orders by status: {len(orders_by_status)} rows")
print(f"- Month-over-month revenue: {len(mom_revenue)} rows")
print("export_report.py finished -> weekly_sales_report.csv")