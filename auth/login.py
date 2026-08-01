import streamlit as st
import datetime
from services.auth_service import (
    authenticate_user,
    create_session_token,
    get_user_by_email,
    update_user_password,
)

def login_page(cookie_manager):
    if "auth_view" not in st.session_state:
        st.session_state["auth_view"] = "login"  # "login" or "forgot_password"

    if st.session_state["auth_view"] == "forgot_password":
        _forgot_password_view()
        return

    st.markdown("### 🔑 Welcome Back")
    st.write("Log in to your dashboard")

    email = st.text_input("Email", placeholder="you@example.com")
    password = st.text_input("Password", type="password", placeholder="Enter your password")

    col1, col2 = st.columns([1, 1])
    with col1:
        remember_me = st.checkbox("Remember me")
    with col2:
        if st.button("Forgot password?", use_container_width=True):
            st.session_state["auth_view"] = "forgot_password"
            st.rerun()

    if st.button("Log In", use_container_width=True):
        success, user = authenticate_user(email, password)
        if success:
            st.session_state["logged_in"] = True
            st.session_state["user"] = user
            st.session_state["user_id"] = user["id"]
            st.session_state["role"] = user["role"]

            if remember_me:
                token = create_session_token(user["id"])
                cookie_manager.set(
                    "auth_token",
                    token,
                    expires_at=datetime.datetime.now() + datetime.timedelta(days=30),
                    key="set_auth_token_cookie",
                )

            st.success(f"Welcome back, {user['username']}!")
            st.rerun()
        else:
            st.error("Invalid email or password.")

    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("New here?")
    with col2:
        if st.button("Create an account", use_container_width=True):
            st.session_state["page"] = "signup"
            st.rerun()

def _forgot_password_view():
    st.markdown("### 🔑 Reset Password")
    st.write("Enter your email to reset your password.")

    email = st.text_input("Email", key="reset_email", placeholder="you@example.com")

    if "reset_user_verified" not in st.session_state:
        st.session_state["reset_user_verified"] = False

    if not st.session_state["reset_user_verified"]:
        if st.button("Continue"):
            user = get_user_by_email(email)
            if user:
                st.session_state["reset_user_verified"] = True
                st.session_state["reset_user_id"] = user["id"]
                st.rerun()
            else:
                st.error("No account found with that email.")
    else:
        new_password = st.text_input("New password", type="password", key="new_pw")
        confirm_password = st.text_input("Confirm new password", type="password", key="confirm_pw")

        if st.button("Reset Password"):
            if not new_password:
                st.error("Password cannot be empty.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                update_user_password(st.session_state["reset_user_id"], new_password)
                st.success("Password updated! Please log in.")
                st.session_state["reset_user_verified"] = False
                st.session_state["auth_view"] = "login"
                st.rerun()

    if st.button("← Back to login"):
        st.session_state["auth_view"] = "login"
        st.session_state["reset_user_verified"] = False
        st.rerun()