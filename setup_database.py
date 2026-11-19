import sqlite3
import pandas as pd
from werkzeug.security import generate_password_hash

# Load your real customer data
df = pd.read_csv('habarinode_combined.csv')

df = df[['customer_id', 'region', 'package', 'tenure_months',
         'network_downtime_tickets', 'power_issue_tickets',
         'payment_tickets', 'faulty_equipment_tickets',
         'total_tickets_6mo', 'fup_triggered']]

df['fup_triggered'] = df['fup_triggered'].map({'Yes': 1, 'No': 0})

conn = sqlite3.connect('habari_customers.db')
df.to_sql('customers', conn, if_exists='replace', index=False)

# Create a permanent staff accounts table
conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
''')

# Add the default admin account only if it doesn't already exist
existing = conn.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()
if not existing:
    conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                 (('admin', generate_password_hash('CHANGE_ME'))))

# Create a permanent prediction history table
conn.execute('''
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT,
        tenure REAL,
        downtime REAL,
        total_tickets REAL,
        fup TEXT,
        result TEXT,
        probability REAL
    )
''')

conn.commit()
conn.close()

print(f"Loaded {len(df)} customers, created users and history tables.")