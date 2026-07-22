import streamlit as st
from config.database import get_connection

def donor_reports():
    if not st.session_state.get("logged_in") or st.session_state.get("role") != "donor":
        st.error("Access restricted to Donor accounts.")
        st.stop()

    st.title("📊 Donor Dashboard")
    st.metric("Total NGOs Viewed", 5)   # Replace with actual query counts
    st.metric("Certificates Earned", 3) # Replace with actual donations

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
            continue
        seen.add(row["name"])

        with st.container(border=True):
            c1, c2 = st.columns([3,1])
            with c1:
                st.markdown(f"### {row['name']}")
                st.write(f"Reg. No: {row.get('registration_number') or 'Not provided'}")
            with c2:
                if row["transparency_score"] is not None:
                    st.metric("Score", f"{row['transparency_score']}/100")
                else:
                    st.info("No report yet")

            if row["red_flags"]:
                with st.expander("⚠️ Red Flags"):
                    for flag in row["red_flags"].split(", "):
                        st.write(f"- {flag}")

            st.download_button("Download Transparency Report", "report.pdf")
            st.download_button("Download Certificate", "certificate.pdf")
            st.divider()
