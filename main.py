import streamlit as st
from streamlit_lottie import st_lottie
import requests

# --- Local imports ---
from config.database import init_db
from auth.signup import signup_page
from auth.login import login_page
from streamlit_multipage.ngo_dashboard import ngo_dashboard
from streamlit_multipage.donor_home import donor_home   # donor main dashboard
from streamlit_multipage.donor_dashboard import donor_dashboard  # NGO search
from streamlit_multipage.donor_report import donor_reports
from streamlit_multipage.market import market
from services.report_service import get_all_org_scores
from streamlit_multipage.donation import donation


# --- Page config ---
st.set_page_config(page_title="Donation Transparency Checker", page_icon="🌍", layout="wide")

# --- Initialize DB once ---
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

# --- Session defaults ---
if "page" not in st.session_state:
    st.session_state.page = "home"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

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

# ======================================================
# NOT LOGGED IN
# ======================================================
if not st.session_state.logged_in:
    # Hide sidebar
    st.markdown(
        """<style>[data-testid="stSidebar"] {display: none;}</style>""",
        unsafe_allow_html=True
    )

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
        signup_page()
        if st.button("Already have an account? Login"):
            st.session_state.page = "login"
            st.rerun()

    elif st.session_state.page == "login":
        login_page()
        if st.button("Need an account? Sign up"):
            st.session_state.page = "signup"
            st.rerun()

# ======================================================
# LOGGED IN
# ======================================================
else:
    user = st.session_state["user"]
    role = st.session_state["role"]

    st.sidebar.title("Navigation")
    st.sidebar.write(f"Logged in as: **{user['username']}** ({role})")

    if role == "ngo":
        nav = st.sidebar.radio("Go to", ["Dashboard", "Upload Report"])
    else:
        nav = st.sidebar.radio("Go to", ["Dashboard", "Marketplace", "Search NGOs", "Reports"])

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    st.divider()

    # --- NGO Pages ---
    if role == "ngo":
        nav = st.sidebar.radio("Go to", ["Dashboard", "Upload Report"])
        if nav == "Dashboard":
            ngo_dashboard()
        elif nav == "Upload Report":
            st.write("📄 Upload report page coming soon...")

    else:
        donor_pages = ["Dashboard", "Marketplace", "Reports"]
        all_pages = donor_pages + ["Search NGOs", "Donation"]

        if "page" not in st.session_state or st.session_state.page not in all_pages:
            st.session_state.page = "Dashboard"

        if st.session_state.page == "Donation":
            # Full-page donation flow: hide the sidebar entirely
            st.markdown(
                """<style>[data-testid="stSidebar"] {display: none;}</style>""",
                unsafe_allow_html=True
            )
        else:
            current = st.session_state.page if st.session_state.page in donor_pages else "Dashboard"
            choice = st.sidebar.radio("Go to", donor_pages, index=donor_pages.index(current))
            if choice != st.session_state.page:
                st.session_state.page = choice
                st.rerun()

        if st.session_state.page == "Dashboard":
            donor_home()
        elif st.session_state.page == "Marketplace":
            market()
        elif st.session_state.page == "Search NGOs":
            donor_dashboard()
        elif st.session_state.page == "Reports":
            donor_reports()
        elif st.session_state.page == "Donation":
            donation()
