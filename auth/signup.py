import streamlit as st
from services.auth_service import create_user

def signup_page():
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
                st.success(message)
                st.info("You can now log in.")
            else:
                st.error(message)
