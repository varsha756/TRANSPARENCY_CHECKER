import streamlit as st
from config.database import get_connection
from services.campaign_service import get_approved_campaigns
from services.donation_service import record_donation
from components.chat_widget import render_chat_bubble

def get_approved_campaigns():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.title, c.description, c.goal_amount, c.created_at,
               COALESCE(SUM(d.amount), 0) AS raised, COUNT(d.id) AS donor_count
        FROM campaigns c
        LEFT JOIN campaign_donations cd ON cd.campaign_id = c.id
        LEFT JOIN donations d ON d.id = cd.donation_id
        WHERE c.status = 'approved'
        GROUP BY c.id
        ORDER BY c.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def campaigns_page():
    if not st.session_state.get("logged_in") or st.session_state.get("role") != "donor":
        st.error("Access restricted to Donor accounts.")
        st.stop()

    st.title("🎯 Active Campaigns")
    st.subheader("Support causes by donating or volunteering")

    campaigns = get_approved_campaigns()
    if not campaigns:
        st.info("No approved campaigns available yet.")
        return

    for c in campaigns:
        goal = c["goal_amount"]
        raised = c["raised"]
        pct = 0 if goal <= 0 else min(100, round((raised / goal) * 100))

        with st.container():
            st.markdown(f"### {c['title']}")
            st.write(c["description"])
            st.progress(pct / 100)
            st.write(f"Raised: ₹{raised:,.0f} / Goal: ₹{goal:,.0f}")
            st.write(f"Donors: {c['donor_count']}")

            choice = st.radio("How would you like to contribute?",
                              ["Donate Money", "Join as Volunteer"],
                              key=f"choice_{c['id']}")

            if choice == "Donate Money":
                amount = st.number_input("Enter donation amount (₹)", min_value=100.0, step=100.0, key=f"amt_{c['id']}")
                st.button("Donate Now", key=f"donate_{c['id']}")
            else:
                name = st.text_input("Your Name", key=f"name_{c['id']}")
                contact = st.text_input("Contact Number", key=f"contact_{c['id']}")
                st.text_area("What can you bring?", key=f"bring_{c['id']}")
                st.button("Register as Volunteer", key=f"vol_{c['id']}")

            st.divider()

render_chat_bubble()