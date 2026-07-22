import streamlit as st
from config.database import get_connection
from services.report_service import get_latest_score_for_org, get_score_history_for_org


def render_org_analysis(org_id: int, org_name: str):
    st.subheader(f"Organization: {org_name}")

    latest = get_latest_score_for_org(org_id)
    if not latest:
        st.info("No reports analyzed yet for this organization.")
        return

    st.metric("Transparency Score", f"{latest['transparency_score']}/100")
    if latest.get("admin_cost_percentage") is not None:
        st.write(f"Administrative Cost: {latest['admin_cost_percentage']}%")

    if latest["red_flags"]:
        st.warning("Red Flags:")
        for flag in latest["red_flags"].split(", "):
            st.write(f"- {flag}")
    else:
        st.success("No red flags detected.")

    history = get_score_history_for_org(org_id)
    if len(history) > 1:
        import pandas as pd
        import plotly.express as px
        df = pd.DataFrame(history)
        fig = px.line(df, x="created_at", y="transparency_score", markers=True,
                      title="Transparency Score Over Time")
        st.plotly_chart(fig, use_container_width=True)


def analysis_page():
    if not st.session_state.get("logged_in"):
        st.error("Please log in to view this page.")
        st.stop()

    role = st.session_state.get("role")
    st.title("🔍 Transparency Analysis")

    if role == "ngo":
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
        render_org_analysis(org["id"], org["name"])

    elif role == "donor":
        st.info("Donor view not finalized yet — pending donations table schema.")

    else:
        st.error("Unrecognized role.")
        st.stop()