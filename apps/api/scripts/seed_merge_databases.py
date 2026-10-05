"""
Seed Script for Multi-Source Merge Test Databases:
1. PostgreSQL: `retail_store_pg` (Physical POS retail store data)
2. MySQL: `retail_online_mysql` (Online web store data)

Both databases feature matching tables (`customers`, `products`, `orders`) designed for
multi-source merging, with:
- 1-2 unique columns per table in PostgreSQL (e.g. `loyalty_tier`, `shelf_location`, `terminal_pos_id`)
- 1-2 unique columns per table in MySQL (e.g. `referral_code`, `barcode_upc`, `ip_address`)
- Deliberate NULLs across both shared and dialect-specific columns to thoroughly test
  nullability coercion, keyset pagination, and DuckDB merge deduplication.
"""

from datetime import datetime, timezone, timedelta
import random
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pymysql

# Connection configurations
PG_CONFIG = {
    "host": "localhost",
    "port": 5434,
    "user": "postgres",
    "password": "postgres_password",
    "dbname": "postgres",
}

MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "root",
    "password": "mysql_password",
}

PG_TARGET_DB = "retail_store_pg"
MYSQL_TARGET_DB = "retail_online_mysql"


def create_and_seed_postgres():
    print(f"\n[PostgreSQL] Connecting to postgres server on port {PG_CONFIG['port']}...")
    conn = psycopg2.connect(**PG_CONFIG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Create Database if not exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (PG_TARGET_DB,))
    if not cur.fetchone():
        print(f"[PostgreSQL] Creating database '{PG_TARGET_DB}'...")
        cur.execute(f'CREATE DATABASE "{PG_TARGET_DB}"')
    else:
        print(f"[PostgreSQL] Database '{PG_TARGET_DB}' already exists.")
    cur.close()
    conn.close()

    # Connect to retail_store_pg
    pg_db_config = dict(PG_CONFIG)
    pg_db_config["dbname"] = PG_TARGET_DB
    conn = psycopg2.connect(**pg_db_config)
    conn.autocommit = True
    cur = conn.cursor()

    print(f"[PostgreSQL] Creating schema in '{PG_TARGET_DB}'...")

    # Drop existing tables to ensure clean reproducible state
    cur.execute("DROP TABLE IF EXISTS orders CASCADE;")
    cur.execute("DROP TABLE IF EXISTS products CASCADE;")
    cur.execute("DROP TABLE IF EXISTS customers CASCADE;")

    # 1. Customers Table (with PG-specific loyalty_tier & vat_tax_id)
    cur.execute("""
        CREATE TABLE customers (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            phone VARCHAR(50),
            loyalty_tier VARCHAR(50),
            vat_tax_id VARCHAR(50),
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Products Table (with PG-specific weight_kg & shelf_location)
    cur.execute("""
        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            sku VARCHAR(100) NOT NULL UNIQUE,
            product_name VARCHAR(255) NOT NULL,
            category VARCHAR(100) NOT NULL,
            unit_price NUMERIC(10, 2) NOT NULL,
            stock_quantity INTEGER,
            weight_kg NUMERIC(8, 2),
            shelf_location VARCHAR(50),
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 3. Orders Table (with PG-specific terminal_pos_id & cashier_badge_no)
    cur.execute("""
        CREATE TABLE orders (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
            order_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            order_status VARCHAR(50) NOT NULL,
            total_amount NUMERIC(12, 2) NOT NULL,
            notes TEXT,
            terminal_pos_id VARCHAR(50),
            cashier_badge_no VARCHAR(50)
        );
    """)

    print(f"[PostgreSQL] Seeding '{PG_TARGET_DB}' tables...")

    # Seed Customers (30 rows, deliberate NULLs in phone, loyalty_tier, vat_tax_id)
    first_names = ["James", "Emma", "Liam", "Olivia", "Noah", "Ava", "William", "Sophia", "Benjamin", "Isabella",
                   "Lucas", "Mia", "Henry", "Evelyn", "Alexander", "Harper", "Sebastian", "Camila", "Jack", "Gianna"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
    tiers = ["Bronze", "Silver", "Gold", "Platinum"]

    base_time = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    for i in range(1, 31):
        fn = first_names[(i - 1) % len(first_names)]
        ln = last_names[(i * 3) % len(last_names)]
        email = f"{fn.lower()}.{ln.lower()}{i}@retailstore.com"
        
        # Deliberate NULLs:
        phone = None if i in [3, 7, 12, 19, 25] else f"+1-555-01{i:02d}"
        loyalty = None if i in [2, 8, 14, 22] else tiers[(i % len(tiers))]
        vat = None if i in [1, 5, 9, 16, 28] else f"VAT-US-{10000 + i * 37}"
        created = base_time + timedelta(days=i, hours=(i * 3) % 24)

        cur.execute("""
            INSERT INTO customers (first_name, last_name, email, phone, loyalty_tier, vat_tax_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (fn, ln, email, phone, loyalty, vat, created))

    # Seed Products (25 rows, deliberate NULLs in stock_quantity, weight_kg, shelf_location)
    categories = ["Electronics", "Apparel", "Home & Kitchen", "Fitness", "Office Supplies"]
    for i in range(1, 26):
        sku = f"PG-SKU-{100 + i}"
        cat = categories[(i - 1) % len(categories)]
        name = f"In-Store {cat} Item #{i}"
        price = round(15.99 + (i * 7.50), 2)
        
        # Deliberate NULLs:
        stock = None if i in [4, 11, 18, 23] else (50 + i * 5)
        weight = None if i in [2, 7, 13, 20] else round(0.5 + (i * 0.25), 2)
        shelf = None if i in [5, 9, 15, 24] else f"Aisle-{(i % 6) + 1}-Bay-{(i % 4) + 1}"
        created = base_time + timedelta(days=i)

        cur.execute("""
            INSERT INTO products (sku, product_name, category, unit_price, stock_quantity, weight_kg, shelf_location, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (sku, name, cat, price, stock, weight, shelf, created))

    # Seed Orders (35 rows, deliberate NULLs in customer_id, notes, terminal_pos_id, cashier_badge_no)
    statuses = ["completed", "completed", "completed", "pending", "refunded"]
    for i in range(1, 36):
        cust_id = None if i in [6, 21] else ((i % 30) + 1)
        status = statuses[(i - 1) % len(statuses)]
        amount = round(25.50 + (i * 12.75), 2)
        order_date = base_time + timedelta(days=(i * 2), hours=(i * 5) % 24)
        
        # Deliberate NULLs:
        notes = None if i % 2 == 0 else f"Walk-in POS purchase receipt ref #{8000 + i}"
        terminal = None if i in [3, 10, 17, 29] else f"POS-TERM-{(i % 4) + 1:02d}"
        badge = None if i in [1, 8, 14, 26] else f"EMP-{(i % 5) + 101}"

        cur.execute("""
            INSERT INTO orders (customer_id, order_date, order_status, total_amount, notes, terminal_pos_id, cashier_badge_no)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (cust_id, order_date, status, amount, notes, terminal, badge))

    cur.close()
    conn.close()
    print("[PostgreSQL] Seeded retail_store_pg: 30 customers, 25 products, 35 orders successfully.")


def create_and_seed_mysql():
    print(f"\n[MySQL] Connecting to mysql server on port {MYSQL_CONFIG['port']}...")
    conn = pymysql.connect(**MYSQL_CONFIG)
    cur = conn.cursor()

    # Create Database if not exists
    print(f"[MySQL] Creating database '{MYSQL_TARGET_DB}' if not exists...")
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_TARGET_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    conn.commit()
    cur.close()
    conn.close()

    # Connect to retail_online_mysql
    my_db_config = dict(MYSQL_CONFIG)
    my_db_config["database"] = MYSQL_TARGET_DB
    conn = pymysql.connect(**my_db_config)
    cur = conn.cursor()

    print(f"[MySQL] Creating schema in '{MYSQL_TARGET_DB}'...")

    # Drop existing tables
    cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cur.execute("DROP TABLE IF EXISTS `orders`;")
    cur.execute("DROP TABLE IF EXISTS `products`;")
    cur.execute("DROP TABLE IF EXISTS `customers`;")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1;")

    # 1. Customers Table (with MySQL-specific referral_code & preferred_currency)
    cur.execute("""
        CREATE TABLE `customers` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `first_name` VARCHAR(100) NOT NULL,
            `last_name` VARCHAR(100) NOT NULL,
            `email` VARCHAR(255) NOT NULL UNIQUE,
            `phone` VARCHAR(50) NULL,
            `referral_code` VARCHAR(50) NULL,
            `preferred_currency` VARCHAR(10) NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # 2. Products Table (with MySQL-specific barcode_upc & warranty_months)
    cur.execute("""
        CREATE TABLE `products` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `sku` VARCHAR(100) NOT NULL UNIQUE,
            `product_name` VARCHAR(255) NOT NULL,
            `category` VARCHAR(100) NOT NULL,
            `unit_price` DECIMAL(10, 2) NOT NULL,
            `stock_quantity` INT NULL,
            `barcode_upc` VARCHAR(50) NULL,
            `warranty_months` INT NULL,
            `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # 3. Orders Table (with MySQL-specific ip_address & browser_user_agent)
    cur.execute("""
        CREATE TABLE `orders` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `customer_id` INT NULL,
            `order_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            `order_status` VARCHAR(50) NOT NULL,
            `total_amount` DECIMAL(12, 2) NOT NULL,
            `notes` TEXT NULL,
            `ip_address` VARCHAR(45) NULL,
            `browser_user_agent` VARCHAR(255) NULL,
            CONSTRAINT `fk_mysql_orders_cust` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    conn.commit()

    print(f"[MySQL] Seeding '{MYSQL_TARGET_DB}' tables...")

    first_names = ["Oliver", "Charlotte", "Elijah", "Amelia", "Mateo", "Harper", "Theodore", "Evelyn", "Ezra", "Abigail",
                   "Daniel", "Emily", "Henry", "Ella", "Jackson", "Avery", "Samuel", "Scarlett", "David", "Grace"]
    last_names = ["Clark", "Lewis", "Robinson", "Walker", "Perez", "Hall", "Young", "Allen", "Sanchez", "Wright",
                  "King", "Scott", "Green", "Baker", "Adams", "Nelson", "Hill", "Ramirez", "Campbell", "Mitchell"]
    currencies = ["USD", "EUR", "GBP", "CAD", "AUD"]
    ref_codes = ["SUMMER26", "INFLUENCER10", "WELCOMEVIP", "DISCOUNT5"]

    base_time = datetime(2026, 2, 1, 9, 30, 0)
    for i in range(1, 31):
        fn = first_names[(i - 1) % len(first_names)]
        ln = last_names[(i * 2) % len(last_names)]
        email = f"{fn.lower()}.{ln.lower()}{i}@onlinestore.org"
        
        # Deliberate NULLs:
        phone = None if i in [4, 9, 15, 21, 28] else f"+1-555-08{i:02d}"
        ref = None if i in [2, 6, 11, 19, 27] else ref_codes[(i % len(ref_codes))]
        curr = None if i in [3, 8, 14, 22] else currencies[(i % len(currencies))]
        created = base_time + timedelta(days=i, hours=(i * 4) % 24)

        cur.execute("""
            INSERT INTO `customers` (`first_name`, `last_name`, `email`, `phone`, `referral_code`, `preferred_currency`, `created_at`)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (fn, ln, email, phone, ref, curr, created))

    # Seed Products (25 rows, deliberate NULLs in stock_quantity, barcode_upc, warranty_months)
    categories = ["Electronics", "Apparel", "Home & Kitchen", "Fitness", "Office Supplies"]
    warranties = [12, 24, 36, 48]
    for i in range(1, 26):
        sku = f"MY-SKU-{200 + i}"
        cat = categories[(i - 1) % len(categories)]
        name = f"Online Digital {cat} #{i}"
        price = round(19.99 + (i * 8.25), 2)
        
        # Deliberate NULLs:
        stock = None if i in [3, 8, 16, 22] else (100 + i * 10)
        upc = None if i in [1, 6, 12, 19] else f"01234567{8000 + i:04d}"
        warranty = None if i in [4, 10, 17, 23] else warranties[(i % len(warranties))]
        created = base_time + timedelta(days=i)

        cur.execute("""
            INSERT INTO `products` (`sku`, `product_name`, `category`, `unit_price`, `stock_quantity`, `barcode_upc`, `warranty_months`, `created_at`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (sku, name, cat, price, stock, upc, warranty, created))

    # Seed Orders (35 rows, deliberate NULLs in customer_id, notes, ip_address, browser_user_agent)
    statuses = ["completed", "completed", "processing", "shipped", "refunded"]
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 Safari/17.2",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
    ]
    for i in range(1, 36):
        cust_id = None if i in [5, 19] else ((i % 30) + 1)
        status = statuses[(i - 1) % len(statuses)]
        amount = round(32.00 + (i * 14.50), 2)
        order_date = base_time + timedelta(days=(i * 2), hours=(i * 7) % 24)
        
        # Deliberate NULLs:
        notes = None if i % 2 != 0 else f"Online web checkout order ref #{9000 + i}"
        ip = None if i in [2, 9, 18, 27] else f"198.51.100.{10 + i}"
        ua = None if i in [4, 11, 20, 31] else agents[(i % len(agents))]

        cur.execute("""
            INSERT INTO `orders` (`customer_id`, `order_date`, `order_status`, `total_amount`, `notes`, `ip_address`, `browser_user_agent`)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (cust_id, order_date, status, amount, notes, ip, ua))

    conn.commit()
    cur.close()
    conn.close()
    print("[MySQL] Seeded retail_online_mysql: 30 customers, 25 products, 35 orders successfully.")


if __name__ == "__main__":
    print("=" * 70)
    print("MIGRAFLOW MULTI-SOURCE MERGE DATABASE PROVISIONER")
    print("=" * 70)
    create_and_seed_postgres()
    create_and_seed_mysql()
    print("\n" + "=" * 70)
    print("ALL MERGE DATABASES CREATED AND SEEDED SUCCESSFULLY!")
    print("=" * 70)
