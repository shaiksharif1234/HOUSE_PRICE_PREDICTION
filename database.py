import sqlite3

DB_NAME = "users.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area INTEGER,
            bedrooms INTEGER,
            bathrooms INTEGER,
            model TEXT,
            price INTEGER,
            time TEXT,
            user_email TEXT
        )
    """)
    

    # ➕ ADD: indexes belong to predictions table
    conn.execute("CREATE INDEX IF NOT EXISTS idx_price ON predictions(price)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_area ON predictions(area)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_model ON predictions(model)")

    conn.commit()
    conn.close()

def create_user_table():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    

    conn.commit()
    conn.close()


def get_price_stats():
    conn = get_db()
    stats = conn.execute("""
        SELECT
            COUNT(*) AS total,
            MIN(price) AS min_price,
            MAX(price) AS max_price,
            AVG(price) AS avg_price
        FROM predictions
    """).fetchone()
    conn.close()
    return stats