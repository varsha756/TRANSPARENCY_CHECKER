from config.database import get_connection


def get_campaigns_for_org(org_id):
    """
    All campaigns for one NGO, each with the amount raised so far
    (computed via campaign_donations -> donations, no column added to
    the donations table).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            c.id,
            c.title,
            c.description,
            c.goal_amount,
            c.status,
            c.created_at,
            COALESCE(SUM(d.amount), 0) AS raised,
            COUNT(d.id) AS donor_count
        FROM campaigns c
        LEFT JOIN campaign_donations cd ON cd.campaign_id = c.id
        LEFT JOIN donations d ON d.id = cd.donation_id
        WHERE c.org_id = ?
        GROUP BY c.id
        ORDER BY c.created_at DESC
    """, (org_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_campaign(org_id, title, description, goal_amount):
    """New campaigns are auto-approved and immediately visible to donors."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO campaigns (org_id, title, description, goal_amount, status)
        VALUES (?, ?, ?, ?, 'approved')
    """, (org_id, title, description, goal_amount))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_campaign_totals_for_org(org_id):
    """Summary numbers for the NGO dashboard stat cards."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*) AS campaign_count,
            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) AS active_count
        FROM campaigns
        WHERE org_id = ?
    """, (org_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {"campaign_count": 0, "active_count": 0}

def get_approved_campaigns():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            c.id, c.org_id, c.title, c.description, c.goal_amount, c.created_at,
            COALESCE(SUM(d.amount), 0) AS raised,
            COUNT(d.id) AS donor_count
        FROM campaigns c
        LEFT JOIN campaign_donations cd ON cd.campaign_id = c.id
        LEFT JOIN donations d ON d.id = cd.donation_id
        WHERE c.status = 'approved'
        GROUP BY c.id
        ORDER BY c.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def register_volunteer(campaign_id, donor_id, name, contact, contribution):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO volunteers (campaign_id, donor_id, name, contact, contribution)
        VALUES (?, ?, ?, ?, ?)
    """, (campaign_id, donor_id, name, contact, contribution))
    conn.commit()
    conn.close()

def link_donation_to_campaign(campaign_id, donation_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO campaign_donations (campaign_id, donation_id)
        VALUES (?, ?)
    """, (campaign_id, donation_id))
    conn.commit()
    conn.close()

def get_volunteers_for_campaign(campaign_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM volunteers WHERE campaign_id = ? ORDER BY created_at DESC",
        (campaign_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]      
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]