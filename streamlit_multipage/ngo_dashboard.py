import streamlit as st
import os
from config.database import get_connection
from services.pdf_service import extract_text_from_pdf
from services.scoring_service import calculate_score
from services.report_service import save_report_and_score, get_latest_score_for_org
from services.news_service import get_ngo_news


def render_news_sidebar():
    st.sidebar.error("SIDEBAR FUNCTION IS RUNNING")   # temporary debug line
    st.sidebar.subheader("📰 Latest NGO News")
    ...
    news_items = get_ngo_news()
    if not news_items:
        st.sidebar.info("No news available right now.")
        return

    for item in news_items:
        st.sidebar.markdown(
            f"**[{item['title']}]({item['url']})**  \n"
            f"*{item['source']} · {item['published_at']}*"
        )
        st.sidebar.divider()


def ngo_dashboard():
    # --- Access control ---
    if not st.session_state.get("logged_in") or st.session_state.get("role") != "ngo":
        st.error("Access restricted to NGO accounts.")
        if st.button("Logout / Reset"):
            st.session_state.clear()
            st.rerun()
        st.stop()

    render_news_sidebar()   # <-- actually call it now

    st.title("NGO Dashboard")

    user_id = st.session_state["user_id"]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM organizations WHERE user_id = ?", (user_id,))
    org = cursor.fetchone()
    conn.close()

    if not org:
        st.error("No organization profile found for this account.")
        st.stop()

    org = dict(org)
    org_id = org["id"]

    st.subheader(f"Organization: {org['name']}")
    st.write(f"Registration No: {org.get('registration_number') or 'Not provided'}")

    st.divider()

    st.subheader("Upload Financial Report (PDF)")
    uploaded_file = st.file_uploader("Choose a PDF", type=["pdf"])

    if uploaded_file and st.button("Analyze Report"):
        os.makedirs("data/uploaded_reports", exist_ok=True)
        file_path = f"data/uploaded_reports/{org_id}_{uploaded_file.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        extracted_text = extract_text_from_pdf(uploaded_file)
        score_data = calculate_score(extracted_text)

        if save_report_and_score(org_id, user_id, file_path, extracted_text, score_data):
            st.success("Report analyzed and saved!")
        else:
            st.error("Something went wrong saving the report.")

    st.divider()

    st.subheader("Latest Transparency Score")
    latest = get_latest_score_for_org(org_id)

    if latest:
        st.metric("Transparency Score", f"{latest['transparency_score']}/100")
        if latest["red_flags"]:
            st.warning("Red Flags:")
            for flag in latest["red_flags"].split(", "):
                st.write(f"- {flag}")
        else:
            st.success("No red flags detected.")
    else:
        st.info("No reports analyzed yet. Upload one above.")