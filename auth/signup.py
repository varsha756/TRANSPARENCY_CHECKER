import streamlit as st
from services.auth_service import create_user

def signup_page():
    st.subheader("Create an Account")

    role_label = st.radio(
        "Sign up as",
        ["Donor", "NGO"],
        horizontal=True
    )
    role = "donor" if role_label == "Donor" else "ngo"

    username = st.text_input("Username" if role == "donor" else "NGO Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    # Optional: extra field for NGOs
    registration_no = None
    if role == "ngo":
        registration_no = st.text_input("NGO Registration Number (optional)")

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