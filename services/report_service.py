from config.database import get_connection

def save_report_and_score(org_id, user_id, file_path, extracted_text, score_data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO reports (org_id, uploaded_by, file_path, extracted_text)
               VALUES (?, ?, ?, ?)""",
            (org_id, user_id, file_path, extracted_text)
        )
        report_id = cursor.lastrowid

        cursor.execute(
            """INSERT INTO scores (report_id, admin_cost_percentage, transparency_score, red_flags, ai_summary)
               VALUES (?, ?, ?, ?, ?)""",
            (report_id, score_data.get("admin_cost_percentage"),
             score_data["transparency_score"], ", ".join(score_data["red_flags"]), "")
        )
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()

def get_latest_score_for_org(org_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.* FROM scores s
        JOIN reports r ON s.report_id = r.id
        WHERE r.org_id = ?
        ORDER BY s.created_at DESC LIMIT 1
    """, (org_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None