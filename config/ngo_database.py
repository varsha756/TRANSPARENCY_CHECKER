import sqlite3
from config.database import get_connection


def _column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return column in [row[1] for row in cursor.fetchall()]


def init_ngo_db():
    """
    NGO-side tables. Uses the same app.db and the same get_connection()
    as database.py, but never touches users / organizations / donations /
    reports / scores / viewed_orgs / money_usage_reports — those stay
    exactly as defined in database.py.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Campaigns created by an NGO. Must be approved (status='approved') by
    # the platform admin before it can appear on the donor page.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            goal_amount REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (org_id) REFERENCES organizations(id)
        )
    """)

    # Link table: connects an existing donation to a campaign, without
    # adding any column to the donations table itself. A donation with no
    # row here simply wasn't tied to a specific campaign.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaign_donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donation_id INTEGER NOT NULL UNIQUE,
            campaign_id INTEGER NOT NULL,
            linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (donation_id) REFERENCES donations(id),
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_org_id ON campaigns(org_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_campaign_donations_campaign_id ON campaign_donations(campaign_id)")

    conn.commit()
    conn.close()
    print("[NGO DB INIT] campaigns + campaign_donations ensured")


if __name__ == "__main__":
    init_ngo_db()