import streamlit as st
from streamlit_lottie import st_lottie
import requests
import extra_streamlit_components as stx

# --- Local imports ---
from config.database import init_db
from auth.signup import signup_page
from auth.login import login_page
from services.auth_service import get_user_by_session_token, delete_session_token
from streamlit_multipage.ngo_dashboard import ngo_dashboard
from streamlit_multipage.donor_home import donor_home   # donor main dashboard
from streamlit_multipage.donor_dashboard import donor_dashboard  # NGO search
from streamlit_multipage.donor_report import donor_reports
from streamlit_multipage.market import market
from services.report_service import get_all_org_scores
from streamlit_multipage.donation import donation
from config.ngo_database import init_ngo_db
from streamlit_multipage.donor_chatbot import donor_chatbot
from streamlit_multipage.campaigns import campaigns_page

# --- Page config ---
st.set_page_config(page_title="Donation Transparency Checker", page_icon="🌍", layout="wide")

# --- Initialize DB once ---
if "db_initialized" not in st.session_state:
    init_db()
    init_ngo_db()
    st.session_state["db_initialized"] = True

# --- Session defaults ---
if "page" not in st.session_state:
    st.session_state.page = "home"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "owner_authed" not in st.session_state:
    st.session_state.owner_authed = False

# --- Cookie manager: powers "stay logged in" across browser restarts ---
cookie_manager = stx.CookieManager(key="cookie_manager")

# --- Hidden admin route: visit the app URL with ?admin=1 to reach this.
# Not linked anywhere in the normal UI — password-protected via secrets.
if st.query_params.get("admin") == "1":
    from auth.auth_owner import admin_page
    admin_page()
    st.stop()

# --- Owner panel: reached via the "Owner Access" button on the donor
# dashboard sidebar (not a URL trick). Once owner_authed is True, this
# takes over the whole page regardless of donor login state.
if st.session_state.owner_authed:
    from admin.owner_login import owner_panel
    owner_panel()
    st.stop()

# --- Auto-login from a saved session cookie, if we're not logged in yet ---
if not st.session_state.logged_in:
    saved_token = cookie_manager.get("auth_token")
    if saved_token:
        auto_user = get_user_by_session_token(saved_token)
        if auto_user:
            st.session_state["logged_in"] = True
            st.session_state["user"] = auto_user
            st.session_state["user_id"] = auto_user["id"]
            st.session_state["role"] = auto_user["role"]
            st.rerun()

# --- Cached Lottie loader ---
@st.cache_data
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        return r.json()
    except requests.exceptions.RequestException:
        return None


def do_logout():
    """Clears the server-side session, deletes the DB session token, and
    removes the browser cookie so the user is fully logged out everywhere."""
    token = cookie_manager.get("auth_token")
    if token:
        delete_session_token(token)
        cookie_manager.delete("auth_token", key="delete_auth_token_cookie")
    st.session_state.clear()
    st.rerun()


# ======================================================
# NOT LOGGED IN
# ======================================================
if not st.session_state.logged_in:
    st.sidebar.title("Navigation")

    nav_labels = ["Home", "Login", "Signup"]
    label_to_page = {"Home": "home", "Login": "login", "Signup": "signup"}
    page_to_label = {v: k for k, v in label_to_page.items()}

    current_label = page_to_label.get(st.session_state.page, "Home")
    nav_choice = st.sidebar.radio("Go to", nav_labels, index=nav_labels.index(current_label))

    if label_to_page[nav_choice] != st.session_state.page:
        st.session_state.page = label_to_page[nav_choice]
        st.rerun()

    if st.session_state.page == "home":
        st.title("🌍 Donation Transparency Checker")
        st.subheader("Welcome to the Transparency Platform")

        lottie_animation = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_jcikwtux.json")
        if lottie_animation:
            st_lottie(lottie_animation, height=250, key="donation")

        st.write("This tool helps you verify how donations are being used.")

        if st.button("➡️ Get Started"):
            st.session_state.page = "signup"
            st.rerun()

    elif st.session_state.page == "signup":
        signup_page(cookie_manager)

    elif st.session_state.page == "login":
        login_page(cookie_manager)

# ======================================================
# LOGGED IN
# ======================================================
else:
    user = st.session_state["user"]
    role = st.session_state["role"]

    st.sidebar.title("Navigation")
    st.sidebar.write(f"Logged in as: **{user['username']}** ({role})")

    if role != "ngo":
        st.sidebar.divider()
        with st.sidebar.expander("🔒 Owner Access"):
            from auth.auth_owner import owner_login_form
            owner_login_form()

    if role == "ngo":
        ngo_pages = ["Dashboard", "Upload Report"]

        if "page" not in st.session_state or st.session_state.page not in ngo_pages:
            st.session_state.page = "Dashboard"

        choice = st.sidebar.radio("Go to", ngo_pages, index=ngo_pages.index(st.session_state.page))
        if choice != st.session_state.page:
            st.session_state.page = choice
            st.rerun()

        if st.sidebar.button("Logout"):
            do_logout()

        if st.session_state.page == "Dashboard":
            ngo_dashboard()
        elif st.session_state.page == "Upload Report":
            st.write("📄 Upload report page coming soon...")

    else:
        donor_pages = ["Dashboard", "Marketplace", "Search NGOs", "Reports", "Campaigns"]
        if "page" not in st.session_state or st.session_state.page not in donor_pages + ["Donation"]:
            st.session_state.page = "Dashboard"

        if st.session_state.page == "Donation":
            # Full-page donation flow: hide the sidebar entirely
            st.markdown(
                """<style>[data-testid="stSidebar"] {display: none;}</style>""",
                unsafe_allow_html=True
            )
        else:
            choice = st.sidebar.radio("Go to", donor_pages, index=donor_pages.index(st.session_state.page))
            if choice != st.session_state.page:
                st.session_state.page = choice
                st.rerun()

            if st.sidebar.button("Logout"):
                do_logout()

        if st.session_state.page == "Dashboard":
            donor_home()
        elif st.session_state.page == "Marketplace":
            market()
        elif st.session_state.page == "Search NGOs":
            donor_dashboard()
        elif st.session_state.page == "Reports":
            donor_reports()
        elif st.session_state.page == "Campaigns":
            campaigns_page()
        elif st.session_state.page == "Donation":
            donation()
        elif st.session_state.page == "Chatbot":
            donor_chatbot()