from config.database import get_connection


def get_platform_stats() -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as c FROM organizations")
    total_ngos = cursor.fetchone()["c"]

    cursor.execute("SELECT COUNT(*) as c FROM organizations WHERE verified = 1")
    verified_ngos = cursor.fetchone()["c"]

    cursor.execute("SELECT COUNT(*) as c FROM users WHERE role = 'donor'")
    total_donors = cursor.fetchone()["c"]

    cursor.execute("SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as cnt FROM donations")
    row = cursor.fetchone()

    conn.close()
    return {
        "total_ngos": total_ngos,
        "verified_ngos": verified_ngos,
        "unverified_ngos": total_ngos - verified_ngos,
        "total_donors": total_donors,
        "total_donation_amount": row["total"],
        "total_donation_count": row["cnt"],
    }


def get_category_breakdown() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(category, 'Uncategorized') as category, COUNT(*) as count
        FROM organizations
        GROUP BY category
        ORDER BY count DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_donations_trend() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT strftime('%Y-%m', donated_at) as month, SUM(amount) as total
        FROM donations
        GROUP BY month
        ORDER BY month
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_recent_volunteers(limit: int = 8) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.name, v.contact, v.contribution, v.created_at,
               c.title as campaign_title
        FROM volunteers v
        LEFT JOIN campaigns c ON v.campaign_id = c.id
        ORDER BY v.created_at DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_active_campaigns(limit: int = 8) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.title, c.goal_amount, c.status, c.created_at,
               o.name as org_name
        FROM campaigns c
        LEFT JOIN organizations o ON c.org_id = o.id
        WHERE c.status = 'approved'
        ORDER BY c.created_at DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_campaign_status_breakdown() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM campaigns
        GROUP BY status
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_totals_extra() -> dict:
    """Extra counts (volunteers, campaigns) for KPI cards."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as c FROM volunteers")
    total_volunteers = cursor.fetchone()["c"]

    cursor.execute("SELECT COUNT(*) as c FROM campaigns WHERE status = 'approved'")
    active_campaigns = cursor.fetchone()["c"]

    conn.close()
    return {"total_volunteers": total_volunteers, "active_campaigns": active_campaigns}