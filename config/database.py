import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "app.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS viewed_orgs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_id INTEGER,
            org_id INTEGER,
            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (donor_id) REFERENCES users(id),
            FOREIGN KEY (org_id) REFERENCES organizations(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'donor',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            name TEXT NOT NULL,
            registration_number TEXT,
            country TEXT,
            verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER,
            uploaded_by INTEGER,
            file_path TEXT,
            extracted_text TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (org_id) REFERENCES organizations(id),
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER,
            admin_cost_percentage REAL,
            transparency_score INTEGER,
            red_flags TEXT,
            ai_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (report_id) REFERENCES reports(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_id INTEGER,
            org_id INTEGER,
            amount REAL NOT NULL,
            category TEXT,
            transaction_id TEXT UNIQUE,
            donated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (donor_id) REFERENCES users(id),
            FOREIGN KEY (org_id) REFERENCES organizations(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS money_usage_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_id INTEGER,
            org_id INTEGER,
            report_id INTEGER,
            donation_total REAL,
            donation_count INTEGER,
            usage_summary TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (donor_id) REFERENCES users(id),
            FOREIGN KEY (org_id) REFERENCES organizations(id),
            FOREIGN KEY (report_id) REFERENCES reports(id)
        )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS volunteers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER NOT NULL,
        donor_id INTEGER,
        name TEXT NOT NULL,
        contact TEXT NOT NULL,
        contribution TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
    )
""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS search_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        search_term TEXT NOT NULL,
        searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

    # NEW: persistent-login session tokens. A row here backs a browser
    # cookie so a user stays logged in after closing/reopening the app,
    # instead of losing their account and having to sign up again.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        expires_at INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

    conn.commit()
    conn.close()
    print(f"[DB INIT] all tables ensured at: {DB_PATH}")