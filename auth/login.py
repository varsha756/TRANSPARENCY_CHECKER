import streamlit as st
import datetime
from services.auth_service import authenticate_user, create_session_token

def login_page(cookie_manager):
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        success, user = authenticate_user(email, password)
        if success:
            st.session_state["logged_in"] = True
            st.session_state["user"] = user
            st.session_state["user_id"] = user["id"]
            st.session_state["role"] = user["role"]

            # Persist login across browser restarts: create a DB-backed
            # session token and store it in a browser cookie for 30 days.
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
