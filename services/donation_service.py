from config.database import get_connection
import uuid


def record_donation(donor_id, org_id, amount, category=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        txn_id = str(uuid.uuid4())
        cursor.execute(
            """INSERT INTO donations (donor_id, org_id, amount, category, transaction_id)
               VALUES (?, ?, ?, ?, ?)""",
            (donor_id, org_id, amount, category, txn_id)
        )
        conn.commit()
        return txn_id
    except Exception as e:
        print(e)
        conn.rollback()
        return None
    finally:
        conn.close()


def get_donor_summary(donor_id):
    """Total donated + donation count for the top card."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COALESCE(SUM(amount),0) AS total, COUNT(*) AS count FROM donations WHERE donor_id = ?",
        (donor_id,)
    )
    row = dict(cursor.fetchone())
    conn.close()
    return row


def get_recent_donations(donor_id, limit=3):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.amount, d.donated_at, o.name AS org_name
        FROM donations d
        JOIN organizations o ON d.org_id = o.id
        WHERE d.donor_id = ?
        ORDER BY d.donated_at DESC LIMIT ?
    """, (donor_id, limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_impact_breakdown(donor_id):
    """Sum of this donor's donations grouped by category, for the pie chart."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(category, 'Other') AS category, SUM(amount) AS total
        FROM donations WHERE donor_id = ? GROUP BY category
    """, (donor_id,))
    rows = {r["category"]: r["total"] for r in cursor.fetchall()}
    conn.close()
    return rows


def get_donation_trend(donor_id):
    """Monthly totals for the trend line."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT strftime('%Y-%m', donated_at) AS month, SUM(amount) AS total
        FROM donations WHERE donor_id = ?
        GROUP BY month ORDER BY month ASC
    """, (donor_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_highest_donations(limit=5):
    """Top donations across all donors (public leaderboard-style table)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.username AS donor, d.amount, o.name AS org_name, d.donated_at
        FROM donations d
        JOIN users u ON d.donor_id = u.id
        JOIN organizations o ON d.org_id = o.id
        ORDER BY d.amount DESC LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows