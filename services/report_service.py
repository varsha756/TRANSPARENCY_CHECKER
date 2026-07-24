from config.database import get_connection


def save_report_and_score(org_id, user_id, file_path, extracted_text, score_data):
    """
    Saves the uploaded report into the 'reports' table, then saves the
    AI-generated transparency score into the 'scores' table, linked via report_id.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Insert the report
        cursor.execute(
            """
            INSERT INTO reports (org_id, uploaded_by, file_path, extracted_text)
            VALUES (?, ?, ?, ?)
            """,
            (org_id, user_id, file_path, extracted_text),
        )
        report_id = cursor.lastrowid

        # 2. Insert the score, linked to that report
        cursor.execute(
            """
            INSERT INTO scores (report_id, admin_cost_percentage, transparency_score, red_flags, ai_summary)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                report_id,
                score_data.get("admin_cost_percentage"),
                score_data.get("transparency_score"),
                score_data.get("red_flags"),
                score_data.get("summary"),
            ),
        )

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving report/score: {e}")
        return False


def get_latest_score_for_org(org_id):
    """
    Fetches the most recent transparency score for a given organization,
    by joining reports -> scores and taking the latest one.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT s.*
        FROM scores s
        JOIN reports r ON s.report_id = r.id
        WHERE r.org_id = ?
        ORDER BY s.id DESC
        LIMIT 1
        """,
        (org_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
def get_all_org_scores():
    """
    Fetches every organization along with its most recent transparency score,
    ordered from highest to lowest score. Used for donor-facing leaderboards
    (e.g. "Top NGOs by Transparency").
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT o.id AS org_id, o.name AS name, s.transparency_score,
               s.admin_cost_percentage, s.red_flags, s.ai_summary
        FROM organizations o
        LEFT JOIN reports r ON r.org_id = o.id
        LEFT JOIN scores s ON s.report_id = r.id
        WHERE r.id IS NULL OR r.id = (
            SELECT r2.id
            FROM reports r2
            JOIN scores s2 ON s2.report_id = r2.id
            WHERE r2.org_id = o.id
            ORDER BY s2.id DESC
            LIMIT 1
        )
        ORDER BY s.transparency_score DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
