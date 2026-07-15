import streamlit as st
from services.auth_service import authenticate_user

def login_page():
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        success, user = authenticate_user(email, password)
        if success:
            st.session_state["logged_in"] = True
            st.session_state["user"] = user
            st.success(f"Welcome back, {user['username']}!")
            st.rerun()
        else:
            st.error("Invalid email or password.")