import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('habari_customers.db')

# Add a full_name column to the users table if it's not already there
try:
    conn.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
except sqlite3.OperationalError:
    pass

# Add an updated_by column to customers, to record which officer made each update
try:
    conn.execute("ALTER TABLE customers ADD COLUMN updated_by TEXT")
except sqlite3.OperationalError:
    pass

# Add real staff accounts (edit these names/usernames to match real Habari Node staff)
staff = [
    ('admin', 'CHANGE_ME', 'System Administrator'),
    ('jsanga', 'CHANGE_ME', 'John Sanga'),
    ('gmwakalinga', 'CHANGE_ME', 'Grace Mwakalinga'),
]

for username, password, full_name in staff:
    existing = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO users (username, password_hash, full_name) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), full_name)
        )
        print(f"Added staff account: {username}")
    else:
        print(f"Already exists: {username}")

conn.commit()
conn.close()