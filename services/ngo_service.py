from config.database import get_connection


def register_ngo(name, registration_number, category, contact_phone, email=None, country=None, description=None):
    """
    Creates an internal-only organizations record (user_id stays NULL —
    this NGO has no login account, per current design). Returns
    (success: bool, message: str).
    """
    name = (name or "").strip()
    registration_number = (registration_number or "").strip()
    category = (category or "").strip()
    contact_phone = (contact_phone or "").strip()
    email = (email or "").strip() or None
    country = (country or "").strip() or None
    description = (description or "").strip() or None

    if not name or not registration_number or not category or not contact_phone:
        return False, "Name, registration number, category, and contact phone are all required."

    conn = get_connection()
    cursor = conn.cursor()

    # Prevent duplicate registration numbers
    cursor.execute(
        "SELECT id FROM organizations WHERE registration_number = ?",
        (registration_number,),
    )
    if cursor.fetchone():
        conn.close()
        return False, f"An NGO with registration number '{registration_number}' already exists."

    # Prevent duplicate emails (only checked if an email was provided)
    if email:
        cursor.execute("SELECT id FROM organizations WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return False, f"An NGO with email '{email}' already exists."

    cursor.execute(
        """
        INSERT INTO organizations
            (user_id, name, registration_number, country, verified,
             email, category, contact_phone, description)
        VALUES (NULL, ?, ?, ?, 0, ?, ?, ?, ?)
        """,
        (name, registration_number, country, email, category, contact_phone, description),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return True, f"NGO '{name}' registered successfully (ID: {new_id})."


def get_all_ngos():
    """Returns all organizations as a list of sqlite3.Row objects, most recent first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM organizations ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def save_report_and_analyze(org_id: int, file_path: str, extracted_text: str) -> dict:
    """
    Saves a report row for this org, runs the Gemini transparency analyzer
    on the extracted text, stores the resulting score, and — on a
    successful analysis — marks the organization as verified.

    Returns a dict: {transparency_score, red_flags, summary}
    """
    from apicalls.ai_analyzer import analyze_report_with_ai

    conn = get_connection()
    cursor = conn.cursor()

    # uploaded_by stays NULL — the owner isn't a row in the users table,
    # they're a fixed identity defined only in secrets.
    cursor.execute(
        """
        INSERT INTO reports (org_id, uploaded_by, file_path, extracted_text)
        VALUES (?, NULL, ?, ?)
        """,
        (org_id, file_path, extracted_text),
    )
    report_id = cursor.lastrowid

    result = analyze_report_with_ai(extracted_text)

    cursor.execute(
        """
        INSERT INTO scores (report_id, admin_cost_percentage, transparency_score, red_flags, ai_summary)
        VALUES (?, NULL, ?, ?, ?)
        """,
        (report_id, result["transparency_score"], result["red_flags"], result["summary"]),
    )

    # Mark the org verified once a report has been analyzed.
    cursor.execute("UPDATE organizations SET verified = 1 WHERE id = ?", (org_id,))

    conn.commit()
    conn.close()

    return result


def get_latest_score(org_id: int):
    """Returns the most recent scores row for an org (as a dict), or None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT s.* FROM scores s
        JOIN reports r ON s.report_id = r.id
        WHERE r.org_id = ?
        ORDER BY s.created_at DESC
        LIMIT 1
        """,
        (org_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None