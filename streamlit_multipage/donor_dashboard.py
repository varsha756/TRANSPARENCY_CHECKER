import streamlit as st
from config.database import get_connection

def donor_dashboard():
    # --- Access control ---
    if not st.session_state.get("logged_in") or st.session_state.get("role") != "donor":
        st.error("Access restricted to Donor accounts.")
        st.stop()

    st.title("Donor Dashboard")
    st.subheader("Search NGOs & Check Transparency Scores")

    search_term = st.text_input("Search NGO by name")

    conn = get_connection()
    cursor = conn.cursor()

    if search_term:
        cursor.execute(
            "SELECT * FROM organizations WHERE name LIKE ?",
            (f"%{search_term}%",)
        )
        results = cursor.fetchall()

        if not results:
            st.info("No matching organizations found.")
        else:
            for org in results:
                org = dict(org)
                with st.container():
                    st.markdown(f"### {org['name']}")
                    st.write(f"Registration No: {org.get('registration_number') or 'Not provided'}")
                    st.write(f"Verified: {'✅' if org.get('verified') else '❌'}")

                    # Fetch latest score for this org
                    cursor.execute("""
                        SELECT s.* FROM scores s
                        JOIN reports r ON s.report_id = r.id
                        WHERE r.org_id = ?
                        ORDER BY s.created_at DESC LIMIT 1
                    """, (org["id"],))
                    score_row = cursor.fetchone()

                    if score_row:
                        score = dict(score_row)
                        st.metric("Transparency Score", f"{score['transparency_score']}/100")
                        if score["red_flags"]:
                            st.warning("Red Flags:")
                            for flag in score["red_flags"].split(", "):
                                st.write(f"- {flag}")
                        else:
                            st.success("No red flags detected.")
                    else:
                        st.info("No financial reports analyzed for this organization yet.")

                    st.divider()
    else:
        st.write("Enter an NGO name above to check its transparency score.")

    conn.close()