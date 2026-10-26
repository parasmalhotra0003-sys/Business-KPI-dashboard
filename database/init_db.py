import sys
import os
import bcrypt
from datetime import date, timedelta

# Add parent directory to path so we can import config and connection
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from database.connection import init_db_pool, execute_sql_file, execute_update, execute_query

def seed_database():
    print("Starting database seeding...")
    
    # 1. Seed Admin User if not exists
    admin_exists = execute_query("SELECT * FROM users WHERE username = 'admin'")
    if not admin_exists:
        password = "admin"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        execute_update(
            "INSERT INTO users (username, password_hash, email, role) VALUES (%s, %s, %s, %s)",
            ('admin', hashed, 'admin@bizkpi.com', 'admin')
        )
        print("Admin user seeded (Username: admin, Password: admin).")
    else:
        print("Admin user already exists.")

    # 2. Seed Customers if empty
    customers_count = execute_query("SELECT COUNT(*) as count FROM customers")[0]['count']
    customer_ids = []
    if customers_count == 0:
        customers_data = [
            ('John Smith', 'john@email.com', '+1234567890', 'Madrid', 'Active'),
            ('Maria Garcia', 'maria@email.com', '+1987654321', 'Barcelona', 'Active'),
            ('Robert Brown', 'robert@email.com', '+1122334455', 'Valencia', 'Active'),
            ('Linda Davis', 'linda@email.com', '+1555123456', 'Seville', 'Active'),
            ('William Wilson', 'william@email.com', '+1444987654', 'Zaragoza', 'Inactive')
        ]
        for c in customers_data:
            c_id = execute_update(
                "INSERT INTO customers (name, email, phone, city, status) VALUES (%s, %s, %s, %s, %s)",
                c, return_id=True
            )
            customer_ids.append(c_id)
        print(f"Seeded {len(customer_ids)} customers.")
    else:
        customer_ids = [c['id'] for c in execute_query("SELECT id FROM customers")]

    # 3. Seed Products if empty
    products_count = execute_query("SELECT COUNT(*) as count FROM products")[0]['count']
    product_ids = []
    product_prices = {}
    if products_count == 0:
        products_data = [
            ('Wireless Headphones', 'Electronics', 125.00, 50),
            ('Smart Watch', 'Electronics', 210.00, 30),
            ('T-Shirt (Men)', 'Clothing', 35.00, 100),
            ('Jeans (Men)', 'Clothing', 55.00, 80),
            ('Coffee Maker', 'Home Appliances', 85.00, 20),
            ('Water Bottle', 'Accessories', 15.00, 150)
        ]
        for p in products_data:
            p_id = execute_update(
                "INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)",
                p, return_id=True
            )
            product_ids.append(p_id)
            product_prices[p_id] = p[2]
        print(f"Seeded {len(product_ids)} products.")
    else:
        db_products = execute_query("SELECT id, price FROM products")
        product_ids = [p['id'] for p in db_products]
        product_prices = {p['id']: float(p['price']) for p in db_products}

    # 4. Seed Sales if empty
    sales_count = execute_query("SELECT COUNT(*) as count FROM sales")[0]['count']
    if sales_count == 0 and customer_ids and product_ids:
        # We will generate sales for the current month and the previous month to demonstrate growth trends
        today = date.today()
        # Previous Month (June/July 2026 reference)
        prev_month_date = today - timedelta(days=30)
        
        sales_data = [
            # customer_id, product_id, quantity, sale_date, status
            (customer_ids[0], product_ids[0], 2, prev_month_date, 'Completed'), # 2 * 125 = 250
            (customer_ids[1], product_ids[1], 1, prev_month_date, 'Completed'), # 1 * 210 = 210
            (customer_ids[2], product_ids[2], 3, prev_month_date, 'Completed'), # 3 * 35 = 105
            (customer_ids[3], product_ids[3], 1, prev_month_date, 'Completed'), # 1 * 55 = 55
            
            # Current Month sales (higher revenue to show +ve growth)
            (customer_ids[0], product_ids[0], 4, today - timedelta(days=5), 'Completed'), # 4 * 125 = 500
            (customer_ids[1], product_ids[1], 2, today - timedelta(days=4), 'Completed'), # 2 * 210 = 420
            (customer_ids[2], product_ids[2], 5, today - timedelta(days=3), 'Completed'), # 5 * 35 = 175
            (customer_ids[3], product_ids[3], 2, today - timedelta(days=2), 'Completed'), # 2 * 55 = 110
            (customer_ids[4], product_ids[4], 2, today - timedelta(days=1), 'Completed'), # 2 * 85 = 170
            (customer_ids[0], product_ids[5], 10, today, 'Completed'),                     # 10 * 15 = 150
            (customer_ids[2], product_ids[0], 1, today, 'Pending')                         # 1 * 125 = 125
        ]
        
        for s in sales_data:
            c_id, p_id, qty, s_date, status = s
            price = product_prices[p_id]
            total = price * qty
            execute_update(
                """INSERT INTO sales (customer_id, product_id, quantity, unit_price, total_amount, sale_date, status) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (c_id, p_id, qty, price, total, s_date, status)
            )
        print("Seeded sales records.")

    # 5. Seed Expenses if empty
    expenses_count = execute_query("SELECT COUNT(*) as count FROM expenses")[0]['count']
    if expenses_count == 0:
        today = date.today()
        prev_month_date = today - timedelta(days=30)
        
        expenses_data = [
            (prev_month_date, 'Rent', 'Office Rent', 1500.00),
            (prev_month_date, 'Utilities', 'Electricity and Water', 250.00),
            (prev_month_date, 'Salaries', 'Employee Salaries', 3000.00),
            (today - timedelta(days=15), 'Rent', 'Office Rent', 1500.00),
            (today - timedelta(days=10), 'Utilities', 'Electricity and Water', 280.00),
            (today - timedelta(days=5), 'Salaries', 'Employee Salaries', 3000.00),
            (today - timedelta(days=2), 'Marketing', 'Google Ads Campaign', 500.00)
        ]
        for e in expenses_data:
            execute_update(
                "INSERT INTO expenses (date, category, description, amount) VALUES (%s, %s, %s, %s)",
                e
            )
        print("Seeded expenses records.")
        
    print("Database seeding completed successfully.")

def main():
    print("Initializing Database...")
    try:
        # Initialize pool
        init_db_pool(Config)
        
        # Execute schema SQL file
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        execute_sql_file(schema_path)
        print("Database schema loaded successfully.")
        
        # Seed records
        seed_database()
        print("Database initialization successful!")
    except Exception as e:
        print(f"Database initialization failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
