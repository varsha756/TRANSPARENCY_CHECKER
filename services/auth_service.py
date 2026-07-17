import bcrypt
import sqlite3
from config.database import get_connection

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