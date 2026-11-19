import sqlite3

conn = sqlite3.connect('habari_customers.db')

try:
    conn.execute("ALTER TABLE customers ADD COLUMN flagged_at TEXT")
    print("Added column: flagged_at")
except sqlite3.OperationalError:
    print("Column already exists: flagged_at")

conn.commit()
conn.close()