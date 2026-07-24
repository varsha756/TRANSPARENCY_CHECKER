import streamlit as st
from config.database import get_connection
from apicalls.ai_analyzer import analyze_money_usage


def donor_reports():
    if not st.session_state.get("logged_in") or st.session_state.get("role") != "donor":
        st.error("Access restricted to Donor accounts.")
        st.stop()

    st.title("📊 My Impact Reports")

    donor_id = st.session_state["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    # ---- Group this donor's donations by organization ----------------
    cursor.execute(
        """
        SELECT o.id AS org_id, o.name AS org_name, o.registration_number,
               SUM(d.amount) AS total_amount, COUNT(d.id) AS donation_count,
               MAX(d.donated_at) AS last_donated_at
        FROM donations d
        JOIN organizations o ON d.org_id = o.id
        WHERE d.donor_id = ?
        GROUP BY o.id
        ORDER BY last_donated_at DESC
        """,
        (donor_id,),
    )
    org_rows = [dict(r) for r in cursor.fetchall()]

    st.metric("NGOs Supported", len(org_rows))
    st.metric("Total Donated", f"₹{sum(r['total_amount'] for r in org_rows):,.0f}" if org_rows else "₹0")

    if not org_rows:
        st.info("You haven't donated to any NGOs yet. Go to 'Marketplace' or 'Search NGOs' to get started.")
        conn.close()
        return

    for org in org_rows:
        org_id = org["org_id"]

        # ---- Latest report + score for this org -----------------------
        cursor.execute(
            """
            SELECT r.id AS report_id, r.extracted_text, r.uploaded_at,
                   s.transparency_score, s.red_flags
            FROM reports r
            LEFT JOIN scores s ON s.report_id = r.id
            WHERE r.org_id = ?
            ORDER BY r.id DESC
            LIMIT 1
            """,
            (org_id,),
        )
        report_row = cursor.fetchone()
        report_row = dict(report_row) if report_row else None

        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"### {org['org_name']}")
                st.write(f"Reg. No: {org.get('registration_number') or 'Not provided'}")
                st.write(
                    f"You've donated **₹{org['total_amount']:,.0f}** "
                    f"across {org['donation_count']} donation(s)."
                )
            with c2:
                if report_row and report_row.get("transparency_score") is not None:
                    st.metric("Score", f"{report_row['transparency_score']}/100")
                else:
                    st.info("No report yet")

            if report_row and report_row.get("red_flags"):
                with st.expander("⚠️ Red Flags"):
                    for flag in report_row["red_flags"].split(", "):
                        st.write(f"- {flag}")

            # ---- AI: how this donor's money was used -------------------
            st.markdown("#### 🤖 How your money was used")

            if not report_row:
                st.write(
                    f"{org['org_name']} hasn't uploaded a financial report yet, "
                    f"so we can't generate a usage summary yet."
                )
            else:
                report_id = report_row["report_id"]

                cursor.execute(
                    """
                    SELECT id, report_id, donation_total, donation_count, usage_summary, generated_at
                    FROM money_usage_reports
                    WHERE donor_id = ? AND org_id = ?
                    """,
                    (donor_id, org_id),
                )
                cached = cursor.fetchone()
                cached = dict(cached) if cached else None

                needs_regen = True
                if cached:
                    same_report = cached["report_id"] == report_id
                    same_amount = abs(cached["donation_total"] - org["total_amount"]) < 0.01
                    same_count = cached["donation_count"] == org["donation_count"]
                    if same_report and same_amount and same_count:
                        needs_regen = False

                if needs_regen:
                    with st.spinner("Generating AI summary..."):
                        result = analyze_money_usage(
                            org["org_name"],
                            report_row.get("extracted_text", ""),
                            org["total_amount"],
                            org["donation_count"],
                        )
                    usage_summary = result["usage_summary"]

                    if cached:
                        cursor.execute(
                            """
                            UPDATE money_usage_reports
                            SET report_id=?, donation_total=?, donation_count=?,
                                usage_summary=?, generated_at=CURRENT_TIMESTAMP
                            WHERE id=?
                            """,
                            (report_id, org["total_amount"], org["donation_count"],
                             usage_summary, cached["id"]),
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO money_usage_reports
                                (donor_id, org_id, report_id, donation_total, donation_count, usage_summary)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (donor_id, org_id, report_id, org["total_amount"],
                             org["donation_count"], usage_summary),
                        )
                    conn.commit()
                    generated_note = "just now"
                else:
                    usage_summary = cached["usage_summary"]
                    generated_note = f"on {cached['generated_at']}"

                st.write(usage_summary)
                st.caption(
                    f"🛈 This summary was AI-generated {generated_note}, based on "
                    f"{org['org_name']}'s financial report uploaded on "
                    f"{report_row.get('uploaded_at', 'an earlier date')}. "
                    f"It is an interpretive summary of the NGO's self-submitted report, "
                    f"not an independently verified audit."
                )

            st.download_button("Download Transparency Report", "report.pdf", key=f"report_{org_id}")
            st.download_button("Download Certificate", "certificate.pdf", key=f"cert_{org_id}")

    conn.close()