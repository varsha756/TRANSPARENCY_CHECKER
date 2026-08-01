import streamlit as st


def owner_login_form():
    """
    Renders the owner login form. On successful match against
    st.secrets["OWNER_EMAIL"] / st.secrets["OWNER_PASSWORD"], sets
    st.session_state["owner_authed"] = True.

    This is intentionally NOT tied to the users table — the owner is a
    single fixed identity defined only in secrets, not a signed-up account.
    """
    st.markdown("### 🔒 Owner Access")
    st.caption("Only the site owner can log in here.")

    email = st.text_input("Email", key="owner_email_input")
    password = st.text_input("Password", type="password", key="owner_password_input")

    if st.button("Login as Owner", key="owner_login_btn"):
        owner_email = st.secrets.get("OWNER_EMAIL")
        owner_password = st.secrets.get("OWNER_PASSWORD")

        if owner_email is None or owner_password is None:
            st.error(
                "OWNER_EMAIL / OWNER_PASSWORD are not set in secrets. "
                "Add them in .streamlit/secrets.toml (local) or your "
                "Streamlit Cloud app's Settings → Secrets (deployed)."
            )
            return

        if email.strip().lower() == owner_email.strip().lower() and password == owner_password:
            st.session_state["owner_authed"] = True
            st.rerun()
        else:
            st.error("Incorrect email or password.")


def owner_logout():
    """Clears owner session — does NOT touch the donor's own login state."""
    st.session_state["owner_authed"] = False
    st.rerun()
