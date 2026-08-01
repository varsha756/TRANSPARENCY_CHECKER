import streamlit as st
from auth.auth_owner import owner_logout


def owner_panel():
    """
    The owner's private admin area. Only reachable if
    st.session_state["owner_authed"] is True (checked in main.py).

    Currently a placeholder with 3 tabs — will be filled in with real
    functionality next: Register NGO, Manage NGOs (+ Analyze), Stats.
    """
    st.title("🛠️ Owner Panel")

    if st.button("🔒 Logout of Owner Panel"):
        owner_logout()

    tab1, tab2, tab3 = st.tabs(["➕ Register New NGO", "🏢 Manage NGOs", "📊 Stats Dashboard"])

    with tab1:
        st.info("Register New NGO form will go here.")

    with tab2:
        st.info("List of registered NGOs + Analyze button will go here.")

    with tab3:
        st.info("Platform stats (users, logins, donations, certificates, etc.) will go here.")
