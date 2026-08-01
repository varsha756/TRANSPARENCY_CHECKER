import bcrypt
import sqlite3
import secrets
import time
from config.database import get_connection

SESSION_DURATION_DAYS = 30


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

def create_user(username: str, email: str, password: str, role: str, registration_no: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (username, email, hash_password(password), role)
        )
        user_id = cursor.lastrowid

        if role == "ngo":
            cursor.execute(
                """INSERT INTO organizations (user_id, name, registration_number)
                   VALUES (?, ?, ?)""",
                (user_id, username, registration_no)
            )

        conn.commit()
        return True, "Account created successfully."

    except sqlite3.IntegrityError:
        return False, "Email or username already exists."
    except Exception as e:
        return False, f"Signup failed: {e}"
    finally:
        conn.close()

def authenticate_user(email: str, password: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    if user and verify_password(password, user["password_hash"]):
        return True, dict(user)
    return False, None


# ---------------------------------------------------------------------
# Persistent-login session tokens (backs the "stay logged in" cookie)
# ---------------------------------------------------------------------

def create_session_token(user_id: int) -> str:
    """
    Generates a new random session token, stores it in the sessions table
    linked to this user with a 30-day expiry, and returns the token so it
    can be saved in a browser cookie.
    """
    token = secrets.token_hex(32)
    expires_at = int(time.time()) + SESSION_DURATION_DAYS * 86400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expires_at),
    )
    conn.commit()
    conn.close()
    return token


def get_user_by_session_token(token: str):
    """
    Looks up a user by a session token, but only if that token exists and
    hasn't expired. Returns a user dict (same shape as authenticate_user)
    or None if the token is missing/invalid/expired.
    """
    if not token:
        return None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT u.*
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token = ? AND s.expires_at > ?
        """,
        (token, int(time.time())),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_session_token(token: str):
    """Removes a session token from the DB (used on logout)."""
    if not token:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()
