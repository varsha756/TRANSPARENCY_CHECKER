import streamlit as st
from config.database import get_connection

def donor_reports():
    if not st.session_state.get("logged_in") or st.session_state.get("role") != "donor":
        st.error("Access restricted to Donor accounts.")
        st.stop()

    st.title("Your Reports")
    st.subheader("Recently Viewed NGOs")

    donor_id = st.session_state["user_id"]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.name, o.registration_number, v.viewed_at,
               s.transparency_score, s.red_flags
        FROM viewed_orgs v
        JOIN organizations o ON v.org_id = o.id
        LEFT JOIN reports r ON r.org_id = o.id
        LEFT JOIN scores s ON s.report_id = r.id
        WHERE v.donor_id = ?
        ORDER BY v.viewed_at DESC
    """, (donor_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        st.info("You haven't checked any NGOs yet. Go to 'Search NGOs' to get started.")
        return

    seen = set()
    for row in rows:
        row = dict(row)
        if row["name"] in seen:
            continue  # avoid duplicate entries from repeated views
        seen.add(row["name"])

        with st.container():
            st.markdown(f"### {row['name']}")
            st.write(f"Registration No: {row.get('registration_number') or 'Not provided'}")
            if row["transparency_score"] is not None:
                st.metric("Transparency Score", f"{row['transparency_score']}/100")
                if row["red_flags"]:
                    st.warning("Red Flags:")
                    for flag in row["red_flags"].split(", "):
                        st.write(f"- {flag}")
            else:
                st.info("No transparency report available yet for this NGO.")
            st.divider()