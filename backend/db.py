import sqlite3

def get_db():
    return sqlite3.connect("users.db")

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            refresh_token TEXT NOT NULL
        )
    """)
    db.commit()

def save_user(email, refresh_token):
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO users (email, refresh_token) VALUES (?, ?)",
        (email, refresh_token)
    )
    db.commit()

def get_refresh_token(email):
    db = get_db()
    cur = db.execute(
        "SELECT refresh_token FROM users WHERE email = ?",
        (email,)
    )
    row = cur.fetchone()
    return row[0] if row else None
