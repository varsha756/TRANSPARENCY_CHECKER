import streamlit as st
import datetime
from services.auth_service import create_user, authenticate_user, create_session_token


def signup_page(cookie_manager):
    st.subheader("Create an Account")

    role = "donor"

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Sign Up"):
        if not username or not email or not password:
            st.error("All fields are required.")
        elif password != confirm:
            st.error("Passwords do not match.")
        else:
            success, message = create_user(username, email, password, role)

            if success:
                logged_in, user = authenticate_user(email, password)

                if logged_in:
                    st.session_state["logged_in"] = True
                    st.session_state["user"] = user
                    st.session_state["user_id"] = user["id"]
                    st.session_state["role"] = user["role"]
                    st.session_state["page"] = "Dashboard"

                    token = create_session_token(user["id"])
                    cookie_manager.set(
                        "auth_token",
                        token,
                        expires_at=datetime.datetime.now() + datetime.timedelta(days=30),
                        key="set_auth_token_cookie_signup",
                    )

                    st.success(f"Welcome, {user['username']}! Redirecting to your dashboard...")
                    st.rerun()
                else:
                    st.success(message)
                    st.info("Account created — please log in.")
            else:
                st.error(message)