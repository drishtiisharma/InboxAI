import sqlite3

def get_db():
    return sqlite3.connect("users.db")

# db.py - Add these functions
def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # Users table (existing)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            refresh_token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Conversation history table (NEW)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email) REFERENCES users (email)
        )
    """)
    
    conn.commit()
    conn.close()

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


def save_conversation(email: str, role: str, content: str):
    """Save a conversation message"""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO conversations (email, role, content) 
        VALUES (?, ?, ?)
    """, (email, role, content))
    
    conn.commit()
    conn.close()

def get_conversation_history(user_email: str, limit: int = 10):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role, content
        FROM conversations
        WHERE email = ?
        ORDER BY id ASC
        LIMIT ?
    """, (user_email, limit))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "role": role,
            "content": content
        }
        for role, content in rows
    ]
