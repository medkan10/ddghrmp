import sqlite3
from sqlalchemy import text
import pandas as pd
from pathlib import Path
import hashlib
import bcrypt
from datetime import datetime
from db.database import get_engine
# Set database path
DB_PATH = Path("db/app_data.db")
DB_PATH.parent.mkdir(exist_ok=True)

# Connect and create tables if not exist
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Purchases table
    cursor.execute("""
        CREATE TABLE IF NOT purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            buyer_name TEXT,
            contact_info TEXT,
            receipt_path TEXT,
            FOREIGN KEY (product_id) REFERENCES products(id)
    """)

    # Expenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            amount REAL,
            description TEXT,
            receipt TEXT
        )
    """)

    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        date TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE stock_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        date TEXT NOT NULL DEFAULT (datetime('now')),
        userid INTEGER,
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (userid) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()

# def hash_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()
def hash_password(password: str) -> str:
    """Hashes a plain password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(plain_password: str, hashed_password: str) -> bool:
    """Checks if the plain password matches the hashed password."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def update_user_password(username, old_password, new_password):
    engine = get_engine()

    with engine.connect() as conn:
        result = conn.execute(text("SELECT password FROM users WHERE username = :username"), {"username": username})
        row = result.fetchone()

        if not row:
            raise ValueError("User not found.")

        stored_hashed_password = row[0]

        if not check_password(old_password, stored_hashed_password):
            raise ValueError("Incorrect current password.")

    # Now hash new password and update
    new_hashed = hash_password(new_password)
    
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE users SET password = :password WHERE username = :username
        """), {"password": new_hashed, "username": username})


# Insert purchase
def insert_purchase(date, product_id, quantity, unit_price, buyer_name, contact_info, payment_mode, location, receipt_path, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Check available stock
        cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
        result = cursor.fetchone()
        if result is None:
            raise ValueError("Product not found")
        available_stock = result[0]

        if quantity > available_stock:
            raise ValueError("Not enough stock available")

        if location == "":
            raise ValueError("Please enter a delivery location!")
        # Insert purchase
        cursor.execute('''
            INSERT INTO purchases (date, product_id, quantity, unit_price, buyer_name, contact_info, payment_mode, location, receipt_path, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, product_id, quantity, unit_price, buyer_name, contact_info, payment_mode, location, receipt_path, user_id))

        # Deduct stock
        # cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))

        conn.commit()
        return True
    except Exception as e:
        print("Purchase failed:", e)
        return False
    finally:
        conn.close()


# Insert expense
def insert_expense(date, category, amount, description, receipt_path, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expenses (date, category, amount, description, receipt_path, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (date, category, amount, description, receipt_path, user_id))
    conn.commit()
    conn.close()

# Fetch all purchases
def fetch_purchases():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.date, pr.name, p.quantity, p.unit_price,
               p.buyer_name, p.contact_info, p.payment_mode, p.location, p.receipt_path, p.user_id
        FROM purchases p
        JOIN products pr ON p.product_id = pr.id
        ORDER BY p.date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


# Fetch all expenses
def fetch_expenses():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM expenses')
    records = cursor.fetchall()
    conn.close()
    return records

# Fetch list of Products
def fetch_products():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock FROM products")
    products = cursor.fetchall()
    conn.close()
    return products



def add_product(name, price, user_id, stock=0):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO products (name, price, user_id, stock) VALUES (?, ?, ?, ?)", (name, price, user_id, stock))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def update_product(product_id, name, price, stock):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET name = ?, price = ?, stock = ? WHERE id = ?", (name, price, stock, product_id))
    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

def add_stock_entry(product_id, quantity, userid, date=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        if date:
            cursor.execute(
                "INSERT INTO stock_entries (product_id, quantity, date, userid) VALUES (?, ?, ?, ?)",
                (product_id, quantity, date, userid)
            )
        else:
            cursor.execute(
                "INSERT INTO stock_entries (product_id, quantity, userid) VALUES (?, ?, ?)",
                (product_id, quantity, userid)
            )

        cursor.execute(
            "UPDATE products SET stock = stock + ? WHERE id = ?",
            (quantity, product_id)
        )
        conn.commit()
    except Exception as e:
        print(f"Error adding stock entry: {e}")
    finally:
        conn.close()

def fetch_stock_entries():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT s.id, p.name, s.quantity, s.date
            FROM stock_entries s
            JOIN products p ON s.product_id = p.id
            ORDER BY s.date DESC
        """)
        entries = cursor.fetchall()
        return entries
    except Exception as e:
        print(f"Error fetching stock entries: {e}")
        return []
    finally:
        conn.close()

def fetch_stock_trend():
    engine = get_engine()
    query = text("""
        SELECT s.date, s.product_id, p.name AS product_name, s.quantity
        FROM stock_entries s
        JOIN products p ON s.product_id = p.id
        ORDER BY s.date
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df