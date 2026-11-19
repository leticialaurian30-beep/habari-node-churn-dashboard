import sqlite3

conn = sqlite3.connect('habari_customers.db')
cursor = conn.cursor()

columns = [
    ('churn_result', 'INTEGER'),
    ('churn_probability', 'REAL'),
    ('contact_status', "TEXT DEFAULT 'Not contacted'"),
    ('notes', 'TEXT'),
    ('status_updated_at', 'TEXT'),
    ('updated_by', 'TEXT'),
]

cursor.execute("PRAGMA table_info(customers)")
existing = [row[1] for row in cursor.fetchall()]

for name, col_type in columns:
    if name in existing:
        print(f"Column already exists, skipped: {name}")
    else:
        cursor.execute(f"ALTER TABLE customers ADD COLUMN {name} {col_type}")
        print(f"Column added: {name}")

conn.commit()
conn.close()
print("Done.")