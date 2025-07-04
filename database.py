import sqlite3

def init_db():
    conn = sqlite3.connect("mandoubak.db")
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            role TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            details TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            mandoub_id INTEGER,
            offer_text TEXT
        )
    ''')

    conn.commit()
    conn.close()

def add_user(user_id, role):
    conn = sqlite3.connect("mandoubak.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (id, role) VALUES (?, ?)", (user_id, role))
    conn.commit()
    conn.close()

def get_user_role(user_id):
    conn = sqlite3.connect("mandoubak.db")
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def save_order(user_id, details):
    conn = sqlite3.connect("mandoubak.db")
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, details) VALUES (?, ?)", (user_id, details))
    conn.commit()
    order_id = c.lastrowid
    conn.close()
    return order_id

def get_mandoubs():
    conn = sqlite3.connect("mandoubak.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE role = 'mandoub'")
    ids = [row[0] for row in c.fetchall()]
    conn.close()
    return ids

def save_offer(order_id, mandoub_id, text):
    conn = sqlite3.connect("mandoubak.db")
    c = conn.cursor()
    c.execute("INSERT INTO offers (order_id, mandoub_id, offer_text) VALUES (?, ?, ?)", (order_id, mandoub_id, text))
    conn.commit()
    conn.close()
يشفشلا
