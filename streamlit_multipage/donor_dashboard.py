import streamlit as st
from config.database import get_connection
from services.report_service import get_latest_score_for_org

from services.donation_service import record_donation

def record_donation_form():
    st.subheader("Record a Donation")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM organizations")
    orgs = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if not orgs:
        st.info("No NGOs registered yet.")
        return

    org_choice = st.selectbox("NGO", orgs, format_func=lambda o: o["name"])
    amount = st.number_input("Amount (₹)", min_value=1.0, step=100.0)
    category = st.selectbox("Category", ["Education", "Health", "Relief", "Other"])

    if st.button("Confirm Donation"):
        donor_id = st.session_state["user_id"]
        txn = record_donation(donor_id, org_choice["id"], amount, category)
        if txn:
            st.success(f"Donation recorded! Transaction ID: {txn}")
        else:
            st.error("Something went wrong.")


def _score_badge(score: int) -> str:
    """Return a small colored badge based on transparency score."""
    if score >= 75:
        color, label = "#1f8a3b", "High Transparency"
    elif score >= 50:
        color, label = "#b8860b", "Moderate Transparency"
    else:
        color, label = "#a12727", "Low Transparency"

    return f"""
        <span style="
            background-color:{color};
            color:white;
            padding:4px 10px;
            border-radius:12px;
            font-size:0.85rem;
            font-weight:600;
        ">{score}/100 · {label}</span>
    """


def donor_dashboard():
    # --- Access control ---
    if not st.session_state.get("logged_in") or st.session_state.get("role") != "donor":
        st.error("Access restricted to Donor accounts.")
        st.stop()

    st.title("Donor Dashboard")
    st.subheader("Search NGOs & Check Transparency Scores")

    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("Search NGO by name")
    with col2:
        sort_by_score = st.checkbox("Sort by score", value=False)

    if not search_term:
        st.write("Enter an NGO name above to check its transparency score.")
        return

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM organizations WHERE name LIKE ?",
            (f"%{search_term}%",)
        )
        results = [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

    if not results:
        st.info("No matching organizations found.")
        return

    # Attach latest score to each org via the shared service function
    enriched = []
    for org in results:
        score = get_latest_score_for_org(org["id"])
        enriched.append((org, score))

    if sort_by_score:
        # Orgs with no score yet sort to the bottom
        enriched.sort(
            key=lambda pair: pair[1]["transparency_score"] if pair[1] else -1,
            reverse=True,
        )

    for org, score in enriched:
        with st.container(border=True):
            header_col, badge_col = st.columns([3, 1])
            with header_col:
                st.markdown(f"### {org['name']}")
                st.write(f"Registration No: {org.get('registration_number') or 'Not provided'}")
                st.write(f"Verified: {'✅ Yes' if org.get('verified') else '❌ Not verified'}")
            with badge_col:
                if score:
                    st.markdown(_score_badge(score["transparency_score"]), unsafe_allow_html=True)

            if score:
                if score["red_flags"]:
                    st.warning("Red Flags:")
                    for flag in score["red_flags"].split(", "):
                        st.write(f"- {flag}")
                else:
                    st.success("No red flags detected.")
            else:
                st.info("No financial reports analyzed for this organization yet.")

            st.divider()

    record_donation_form()
    st.divider()