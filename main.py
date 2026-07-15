import streamlit as st
from streamlit_lottie import st_lottie
import requests
from config.database import init_db
from auth.signup import signup_page
from auth.login import login_page

# Page config
st.set_page_config(page_title="Donation Transparency Checker", page_icon="🌍", layout="wide")

# Initialize DB once per session
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

# Cached Lottie loader
@st.cache_data
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        return r.json()
    except requests.exceptions.RequestException:
        return None

lottie_animation = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_jcikwtux.json")

# Initialize page state
if "page" not in st.session_state:
    st.session_state.page = "home"

# Home page
if st.session_state.page == "home":
    st.title("🌍 Donation Transparency Checker")
    st.subheader("Welcome to the Transparency Platform")

    if lottie_animation:
        st_lottie(lottie_animation, height=250, key="donation")
    st.write("This tool helps you verify how donations are being used.")

    if st.button("➡️ Get Started"):
        st.session_state.page = "signup"
        st.rerun()

# Signup page
elif st.session_state.page == "signup":
    signup_page()
    if st.button("Already have an account? Login"):
        st.session_state.page = "login"
        st.rerun()

# Login page
elif st.session_state.page == "login":
    login_page()
    if st.button("Need an account? Sign up"):
        st.session_state.page = "signup"
        st.rerun()