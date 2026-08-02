import os
import json
import streamlit as st
import streamlit.components.v1 as components
from auth.auth_owner import owner_logout
from services.ngo_service import register_ngo, get_all_ngos, save_report_and_analyze, get_latest_score
from services.pdf_service import extract_text_from_pdf
from services.stats_service import (
    get_platform_stats, get_category_breakdown, get_donations_trend,
    get_recent_volunteers, get_active_campaigns, get_campaign_status_breakdown,
    get_totals_extra,
)


def owner_panel():
    """
    The owner's private admin area. Only reachable if
    st.session_state["owner_authed"] is True (checked in main.py).
    """
    # Trim Streamlit's default top whitespace/header padding so this
    # reads as a compact, one-page dashboard instead of a tall empty page.
    st.markdown(
        """
        <style>
            .block-container { padding-top: 2rem; padding-bottom: 2rem; }
            [data-testid="stHeader"] { height: 2.5rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col_title, col_logout = st.columns([5, 1])
    with col_title:
        st.markdown("### 🛠️ Owner Panel")
    with col_logout:
        if st.button("🔒 Logout"):
            owner_logout()

    tab1, tab2, tab3 = st.tabs(["➕ Register New NGO", "🏢 Manage NGOs", "📊 Stats Dashboard"])

    with tab1:
        _register_ngo_tab()

    with tab2:
        _manage_ngos_tab()

    with tab3:
        _stats_dashboard_tab()


def _register_ngo_tab():
    st.subheader("Register a New NGO")
    st.caption("This creates an internal record only — no login account is created for the NGO.")

    ngo_categories = [
        "Education", "Healthcare", "Environment", "Poverty Relief",
        "Animal Welfare", "Disaster Relief", "Women Empowerment",
        "Child Welfare", "Human Rights", "Other",
    ]

    with st.form("register_ngo_form", clear_on_submit=True):
        name = st.text_input("NGO Name *")
        registration_number = st.text_input("Registration Number *")
        category = st.selectbox("Category *", ngo_categories)
        contact_phone = st.text_input("Contact Phone *")

        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("Email (optional)")
        with col2:
            country = st.text_input("Country (optional)")

        description = st.text_area("Description (optional)")

        submitted = st.form_submit_button("Register NGO")

    if submitted:
        success, message = register_ngo(
            name=name,
            registration_number=registration_number,
            category=category,
            contact_phone=contact_phone,
            email=email,
            country=country,
            description=description,
        )
        if success:
            st.success(message)
        else:
            st.error(message)

    st.markdown("---")
    st.markdown("#### Recently Registered NGOs")
    ngos = get_all_ngos()
    if not ngos:
        st.write("No NGOs registered yet.")
    else:
        st.dataframe(
            [
                {
                    "ID": row["id"],
                    "Name": row["name"],
                    "Reg. Number": row["registration_number"],
                    "Category": row["category"],
                    "Phone": row["contact_phone"],
                    "Email": row["email"],
                    "Country": row["country"],
                    "Verified": bool(row["verified"]),
                }
                for row in ngos
            ],
            use_container_width=True,
        )


def _manage_ngos_tab():
    st.subheader("Manage NGOs")

    ngos = get_all_ngos()
    if not ngos:
        st.info("No NGOs registered yet. Add one in the 'Register New NGO' tab first.")
        return

    ngo_options = {f"{row['name']} (ID: {row['id']})": row["id"] for row in ngos}
    selected_label = st.selectbox("Select an NGO", list(ngo_options.keys()))
    org_id = ngo_options[selected_label]
    org = next(row for row in ngos if row["id"] == org_id)

    st.write(f"**Category:** {org['category'] or '—'} &nbsp;&nbsp; **Verified:** {'✅ Yes' if org['verified'] else '❌ No'}")

    st.markdown("---")
    st.markdown("#### Upload Financial Report")

    uploaded_file = st.file_uploader(
        "Upload a financial/annual report (PDF)",
        type=["pdf"],
        key=f"upload_{org_id}",
    )

    if uploaded_file is not None:
        if st.button("🔎 Analyze Report with AI", key=f"analyze_{org_id}"):
            with st.spinner("Extracting text and running AI analysis..."):
                raw_bytes = uploaded_file.getvalue()

                reports_dir = os.path.join("uploads", "reports")
                os.makedirs(reports_dir, exist_ok=True)
                safe_name = f"org{org_id}_{uploaded_file.name}"
                file_path = os.path.join(reports_dir, safe_name)
                with open(file_path, "wb") as f:
                    f.write(raw_bytes)

                extracted_text = extract_text_from_pdf(uploaded_file)
                result = save_report_and_analyze(org_id, file_path, extracted_text)

            st.success(f"Analysis complete — '{org['name']}' has been marked as verified.")
            st.metric("Transparency Score", f"{result['transparency_score']}/100")

            if result["red_flags"]:
                st.warning("Red Flags:")
                for flag in result["red_flags"].split(", "):
                    st.write(f"- {flag}")
            else:
                st.success("No red flags detected.")

            if result["summary"]:
                st.markdown("**AI Summary:**")
                st.write(result["summary"])

            st.rerun()

    st.markdown("---")
    st.markdown("#### Latest Analysis on File")
    latest = get_latest_score(org_id)
    if not latest:
        st.write("No reports analyzed yet for this NGO.")
    else:
        st.metric("Transparency Score", f"{latest['transparency_score']}/100")
        if latest["red_flags"]:
            for flag in latest["red_flags"].split(", "):
                st.write(f"- {flag}")
        if latest["ai_summary"]:
            st.caption(latest["ai_summary"])


def _stats_dashboard_tab():
    stats = get_platform_stats()
    categories = get_category_breakdown()
    trend = get_donations_trend()
    volunteers = get_recent_volunteers()
    campaigns = get_active_campaigns()
    campaign_status = get_campaign_status_breakdown()
    extra = get_totals_extra()

    def _fmt_date(s):
        return (s or "")[:16]

    payload = {
        "totalNgos": stats["total_ngos"],
        "verified": stats["verified_ngos"],
        "unverified": stats["unverified_ngos"],
        "totalDonors": stats["total_donors"],
        "totalDonated": stats["total_donation_amount"],
        "totalVolunteers": extra["total_volunteers"],
        "activeCampaigns": extra["active_campaigns"],
        "categoryLabels": [c["category"] for c in categories],
        "categoryValues": [c["count"] for c in categories],
        "trendLabels": [t["month"] for t in trend],
        "trendValues": [t["total"] for t in trend],
        "volunteerRows": [
            {
                "name": v["name"],
                "contact": v["contact"],
                "contribution": v["contribution"] or "—",
                "campaign": v["campaign_title"] or "—",
                "date": _fmt_date(v["created_at"]),
            }
            for v in volunteers
        ],
        "campaignRows": [
            {
                "title": c["title"],
                "org": c["org_name"] or "—",
                "goal": c["goal_amount"],
                "date": _fmt_date(c["created_at"]),
            }
            for c in campaigns
        ],
        "statusLabels": [s["status"] for s in campaign_status],
        "statusValues": [s["count"] for s in campaign_status],
    }
    data_json = json.dumps(payload)

    dashboard_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0; padding: 0; height: 100%;
    background: #0b0f1a;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    color: #e8eaf2;
    overflow: hidden;
  }}
  .wrap {{
    display: grid;
    grid-template-rows: 90px 190px 160px 200px 190px;
    gap: 10px;
    height: 850px;
    padding: 4px 4px 0 4px;
  }}
  .card {{
    background: linear-gradient(160deg, #141a2c 0%, #10152400 100%);
    background-color: #131a2b;
    border: 1px solid #232b40;
    border-radius: 14px;
    padding: 10px 14px;
    min-height: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }}
  .card h4 {{
    margin: 0 0 6px 0; font-size: 12.5px; font-weight: 600;
    color: #aab2c5; text-transform: uppercase; letter-spacing: .04em;
    display: flex; justify-content: space-between; align-items: center;
  }}
  .kpi-row {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; }}
  .kpi {{
    background: #131a2b; border: 1px solid #232b40; border-radius: 12px;
    padding: 8px 10px; display: flex; flex-direction: column; justify-content: center;
  }}
  .kpi .label {{ color: #8b93a7; font-size: 10px; margin-bottom: 3px; }}
  .kpi .value {{ font-size: 17px; font-weight: 700; color: #fff; }}
  .kpi .value.accent {{ color: #6fe2a0; }}
  .row2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; min-height: 0; }}
  .chart-holder {{ position: relative; flex: 1; min-height: 0; }}
  .empty-note {{ color: #6d7690; font-size: 12px; margin: auto; }}
  .list-wrap {{ overflow-y: auto; flex: 1; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; table-layout: fixed; }}
  th {{
    text-align: left; color: #8b93a7; font-weight: 600; font-size: 10.5px;
    text-transform: uppercase; letter-spacing: .03em; padding: 5px 8px;
    border-bottom: 1px solid #232b40; position: sticky; top: 0; background: #131a2b;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }}
  td {{
    padding: 5px 8px; border-bottom: 1px solid #1a2136; color: #dfe3ee;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }}
  tr:hover td {{ background: #171f34; }}
  .pill {{
    display: inline-block; padding: 1px 8px; border-radius: 8px; font-size: 10.5px;
    font-weight: 700; color: #fff; background: #4f8cff;
  }}
  ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
  ::-webkit-scrollbar-thumb {{ background: #2a3350; border-radius: 4px; }}
</style>
</head>
<body>
<div class="wrap">

  <div class="kpi-row">
    <div class="kpi"><div class="label">Total NGOs</div><div class="value" id="kpiTotalNgos">0</div></div>
    <div class="kpi"><div class="label">Verified</div><div class="value accent" id="kpiVerified">0</div></div>
    <div class="kpi"><div class="label">Unverified</div><div class="value" id="kpiUnverified">0</div></div>
    <div class="kpi"><div class="label">Total Donors</div><div class="value" id="kpiDonors">0</div></div>
    <div class="kpi"><div class="label">💰 Total Donated</div><div class="value accent" id="kpiDonated">₹0</div></div>
    <div class="kpi"><div class="label">🙋 Volunteers</div><div class="value" id="kpiVolunteers">0</div></div>
    <div class="kpi"><div class="label">📢 Active Campaigns</div><div class="value accent" id="kpiCampaigns">0</div></div>
  </div>

  <div class="row2">
    <div class="card">
      <h4>NGO Verification Status</h4>
      <div class="chart-holder"><canvas id="verifyChart"></canvas></div>
    </div>
    <div class="card">
      <h4>NGOs by Category</h4>
      <div class="chart-holder"><canvas id="categoryChart"></canvas></div>
    </div>
  </div>

  <div class="card">
    <h4>Donations Trend (by Month)</h4>
    <div class="chart-holder"><canvas id="trendChart"></canvas></div>
  </div>

  <div class="row2">
    <div class="card">
      <h4>🙋 Recently Registered Volunteers</h4>
      <div class="list-wrap">
        <table>
          <thead><tr><th style="width:22%">Name</th><th style="width:22%">Contact</th><th style="width:40%">Campaign</th><th style="width:16%">Date</th></tr></thead>
          <tbody id="volunteerBody"></tbody>
        </table>
      </div>
    </div>
    <div class="card">
      <h4>📢 Active Campaigns</h4>
      <div class="list-wrap">
        <table>
          <thead><tr><th style="width:44%">Title</th><th style="width:26%">NGO</th><th style="width:14%">Goal</th><th style="width:16%">Date</th></tr></thead>
          <tbody id="campaignBody"></tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="card">
    <h4>Campaign Status Breakdown</h4>
    <div class="chart-holder"><canvas id="statusChart"></canvas></div>
  </div>

</div>

<script>
const DATA = {data_json};

function fmtINR(n) {{
  n = Number(n) || 0;
  return "₹" + n.toLocaleString("en-IN", {{ maximumFractionDigits: 0 }});
}}

document.getElementById("kpiTotalNgos").textContent = DATA.totalNgos;
document.getElementById("kpiVerified").textContent = DATA.verified;
document.getElementById("kpiUnverified").textContent = DATA.unverified;
document.getElementById("kpiDonors").textContent = DATA.totalDonors;
document.getElementById("kpiDonated").textContent = fmtINR(DATA.totalDonated);
document.getElementById("kpiVolunteers").textContent = DATA.totalVolunteers;
document.getElementById("kpiCampaigns").textContent = DATA.activeCampaigns;

// ---- Verification donut ----
const verifyCanvas = document.getElementById("verifyChart");
if (DATA.totalNgos > 0) {{
  new Chart(verifyCanvas, {{
    type: "doughnut",
    data: {{
      labels: ["Verified", "Unverified"],
      datasets: [{{ data: [DATA.verified, DATA.unverified], backgroundColor: ["#6fe2a0", "#4f8cff"], borderColor: "#0b0f1a", borderWidth: 2 }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ position: "bottom", labels: {{ color: "#c7cede", boxWidth: 9, font: {{ size: 10 }} }} }} }}
    }}
  }});
}} else {{
  verifyCanvas.parentElement.innerHTML = '<div class="empty-note">No NGOs registered yet.</div>';
}}

// ---- Category donut ----
const categoryCanvas = document.getElementById("categoryChart");
if (DATA.categoryLabels.length) {{
  new Chart(categoryCanvas, {{
    type: "doughnut",
    data: {{
      labels: DATA.categoryLabels,
      datasets: [{{ data: DATA.categoryValues, backgroundColor: ["#4f8cff","#6fe2a0","#f5a623","#e05b4d","#9b6bff","#33c2d6","#f472b6"], borderColor: "#0b0f1a", borderWidth: 2 }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ position: "bottom", labels: {{ color: "#c7cede", boxWidth: 9, font: {{ size: 10 }} }} }} }}
    }}
  }});
}} else {{
  categoryCanvas.parentElement.innerHTML = '<div class="empty-note">No NGOs registered yet.</div>';
}}

// ---- Donations trend line ----
const trendCanvas = document.getElementById("trendChart");
if (DATA.trendLabels.length) {{
  new Chart(trendCanvas, {{
    type: "line",
    data: {{
      labels: DATA.trendLabels,
      datasets: [{{ data: DATA.trendValues, borderColor: "#6fe2a0", backgroundColor: "rgba(111,226,160,0.15)", tension: 0.35, fill: true, pointRadius: 3, pointBackgroundColor: "#6fe2a0" }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ ticks: {{ color: "#8b93a7", font: {{ size: 9 }} }}, grid: {{ color: "#1c2338" }} }},
        y: {{ ticks: {{ color: "#8b93a7", font: {{ size: 9 }} }}, grid: {{ color: "#1c2338" }} }}
      }}
    }}
  }});
}} else {{
  trendCanvas.parentElement.innerHTML = '<div class="empty-note">No donations recorded yet.</div>';
}}

// ---- Volunteers table ----
const volunteerBody = document.getElementById("volunteerBody");
if (DATA.volunteerRows.length) {{
  DATA.volunteerRows.forEach(v => {{
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${{v.name}}</td><td>${{v.contact}}</td><td title="${{v.campaign}}">${{v.campaign}}</td><td>${{v.date}}</td>`;
    volunteerBody.appendChild(tr);
  }});
}} else {{
  volunteerBody.innerHTML = '<tr><td colspan="4" class="empty-note">No volunteers registered yet.</td></tr>';
}}

// ---- Active campaigns table ----
const campaignBody = document.getElementById("campaignBody");
if (DATA.campaignRows.length) {{
  DATA.campaignRows.forEach(c => {{
    const tr = document.createElement("tr");
    tr.innerHTML = `<td title="${{c.title}}">${{c.title}}</td><td>${{c.org}}</td><td>${{fmtINR(c.goal)}}</td><td>${{c.date}}</td>`;
    campaignBody.appendChild(tr);
  }});
}} else {{
  campaignBody.innerHTML = '<tr><td colspan="4" class="empty-note">No active campaigns yet.</td></tr>';
}}

// ---- Campaign status donut ----
const statusCanvas = document.getElementById("statusChart");
if (DATA.statusLabels.length) {{
  new Chart(statusCanvas, {{
    type: "doughnut",
    data: {{
      labels: DATA.statusLabels,
      datasets: [{{ data: DATA.statusValues, backgroundColor: ["#f5a623","#6fe2a0","#e05b4d","#4f8cff"], borderColor: "#0b0f1a", borderWidth: 2 }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ position: "bottom", labels: {{ color: "#c7cede", boxWidth: 9, font: {{ size: 10 }} }} }} }}
    }}
  }});
}} else {{
  statusCanvas.parentElement.innerHTML = '<div class="empty-note">No campaigns created yet.</div>';
}}
</script>
</body>
</html>
"""

    components.html(dashboard_html, height=870, scrolling=False)
    import os
import json
import streamlit as st
import streamlit.components.v1 as components
from auth.auth_owner import owner_logout
from services.ngo_service import register_ngo, get_all_ngos, save_report_and_analyze, get_latest_score
from services.pdf_service import extract_text_from_pdf
from services.stats_service import (
    get_platform_stats, get_category_breakdown, get_donations_trend,
    get_recent_volunteers, get_active_campaigns, get_campaign_status_breakdown,
    get_totals_extra,
)


def _safe_get(row, key, default="—"):
    """
    Safely read a column from a sqlite3.Row (or dict-like) object.
    sqlite3.Row raises IndexError (not KeyError) when a key/column
    doesn't exist, so we check membership first instead of relying
    on a try/except around KeyError.
    """
    try:
        keys = row.keys()
    except AttributeError:
        keys = row.keys() if hasattr(row, "keys") else []
    if key in keys:
        value = row[key]
        return value if value is not None else default
    return default


def owner_panel():
    """
    The owner's private admin area. Only reachable if
    st.session_state["owner_authed"] is True (checked in main.py).
    """
    # Trim Streamlit's default top whitespace/header padding so this
    # reads as a compact, one-page dashboard instead of a tall empty page.
    st.markdown(
        """
        <style>
            .block-container { padding-top: 2rem; padding-bottom: 2rem; }
            [data-testid="stHeader"] { height: 2.5rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col_title, col_logout = st.columns([5, 1])
    with col_title:
        st.markdown("### 🛠️ Owner Panel")
    with col_logout:
        if st.button("🔒 Logout"):
            owner_logout()

    tab1, tab2, tab3 = st.tabs(["➕ Register New NGO", "🏢 Manage NGOs", "📊 Stats Dashboard"])

    with tab1:
        _register_ngo_tab()

    with tab2:
        _manage_ngos_tab()

    with tab3:
        _stats_dashboard_tab()


def _register_ngo_tab():
    st.subheader("Register a New NGO")
    st.caption("This creates an internal record only — no login account is created for the NGO.")

    ngo_categories = [
        "Education", "Healthcare", "Environment", "Poverty Relief",
        "Animal Welfare", "Disaster Relief", "Women Empowerment",
        "Child Welfare", "Human Rights", "Other",
    ]

    with st.form("register_ngo_form", clear_on_submit=True):
        name = st.text_input("NGO Name *")
        registration_number = st.text_input("Registration Number *")
        category = st.selectbox("Category *", ngo_categories)
        contact_phone = st.text_input("Contact Phone *")

        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("Email (optional)")
        with col2:
            country = st.text_input("Country (optional)")

        description = st.text_area("Description (optional)")

        submitted = st.form_submit_button("Register NGO")

    if submitted:
        success, message = register_ngo(
            name=name,
            registration_number=registration_number,
            category=category,
            contact_phone=contact_phone,
            email=email,
            country=country,
            description=description,
        )
        if success:
            st.success(message)
        else:
            st.error(message)

    st.markdown("---")
    st.markdown("#### Recently Registered NGOs")
    ngos = get_all_ngos()
    if not ngos:
        st.write("No NGOs registered yet.")
    else:
        st.dataframe(
            [
                {
                    "ID": _safe_get(row, "id", "—"),
                    "Name": _safe_get(row, "name", "—"),
                    "Reg. Number": _safe_get(row, "registration_number", "—"),
                    "Category": _safe_get(row, "category", "Uncategorized"),
                    "Phone": _safe_get(row, "contact_phone", "—"),
                    "Email": _safe_get(row, "email", "—"),
                    "Country": _safe_get(row, "country", "—"),
                    "Verified": bool(_safe_get(row, "verified", 0)),
                }
                for row in ngos
            ],
            use_container_width=True,
        )


def _manage_ngos_tab():
    st.subheader("Manage NGOs")

    ngos = get_all_ngos()
    if not ngos:
        st.info("No NGOs registered yet. Add one in the 'Register New NGO' tab first.")
        return

    ngo_options = {f"{_safe_get(row, 'name', 'Unnamed')} (ID: {_safe_get(row, 'id', '?')})": row["id"] for row in ngos}
    selected_label = st.selectbox("Select an NGO", list(ngo_options.keys()))
    org_id = ngo_options[selected_label]
    org = next(row for row in ngos if row["id"] == org_id)

    category_display = _safe_get(org, "category", "—")
    verified_display = "✅ Yes" if _safe_get(org, "verified", 0) else "❌ No"
    st.write(f"**Category:** {category_display} &nbsp;&nbsp; **Verified:** {verified_display}")

    st.markdown("---")
    st.markdown("#### Upload Financial Report")

    uploaded_file = st.file_uploader(
        "Upload a financial/annual report (PDF)",
        type=["pdf"],
        key=f"upload_{org_id}",
    )

    if uploaded_file is not None:
        if st.button("🔎 Analyze Report with AI", key=f"analyze_{org_id}"):
            with st.spinner("Extracting text and running AI analysis..."):
                raw_bytes = uploaded_file.getvalue()

                reports_dir = os.path.join("uploads", "reports")
                os.makedirs(reports_dir, exist_ok=True)
                safe_name = f"org{org_id}_{uploaded_file.name}"
                file_path = os.path.join(reports_dir, safe_name)
                with open(file_path, "wb") as f:
                    f.write(raw_bytes)

                extracted_text = extract_text_from_pdf(uploaded_file)
                result = save_report_and_analyze(org_id, file_path, extracted_text)

            st.success(f"Analysis complete — '{_safe_get(org, 'name', 'This NGO')}' has been marked as verified.")
            st.metric("Transparency Score", f"{result['transparency_score']}/100")

            if result["red_flags"]:
                st.warning("Red Flags:")
                for flag in result["red_flags"].split(", "):
                    st.write(f"- {flag}")
            else:
                st.success("No red flags detected.")

            if result["summary"]:
                st.markdown("**AI Summary:**")
                st.write(result["summary"])

            st.rerun()

    st.markdown("---")
    st.markdown("#### Latest Analysis on File")
    latest = get_latest_score(org_id)
    if not latest:
        st.write("No reports analyzed yet for this NGO.")
    else:
        st.metric("Transparency Score", f"{latest['transparency_score']}/100")
        if latest["red_flags"]:
            for flag in latest["red_flags"].split(", "):
                st.write(f"- {flag}")
        if latest["ai_summary"]:
            st.caption(latest["ai_summary"])


def _stats_dashboard_tab():
    stats = get_platform_stats()
    categories = get_category_breakdown()
    trend = get_donations_trend()
    volunteers = get_recent_volunteers()
    campaigns = get_active_campaigns()
    campaign_status = get_campaign_status_breakdown()
    extra = get_totals_extra()

    def _fmt_date(s):
        return (s or "")[:16]

    payload = {
        "totalNgos": stats["total_ngos"],
        "verified": stats["verified_ngos"],
        "unverified": stats["unverified_ngos"],
        "totalDonors": stats["total_donors"],
        "totalDonated": stats["total_donation_amount"],
        "totalVolunteers": extra["total_volunteers"],
        "activeCampaigns": extra["active_campaigns"],
        "categoryLabels": [c["category"] for c in categories],
        "categoryValues": [c["count"] for c in categories],
        "trendLabels": [t["month"] for t in trend],
        "trendValues": [t["total"] for t in trend],
        "volunteerRows": [
            {
                "name": v["name"],
                "contact": v["contact"],
                "contribution": v["contribution"] or "—",
                "campaign": v["campaign_title"] or "—",
                "date": _fmt_date(v["created_at"]),
            }
            for v in volunteers
        ],
        "campaignRows": [
            {
                "title": c["title"],
                "org": c["org_name"] or "—",
                "goal": c["goal_amount"],
                "date": _fmt_date(c["created_at"]),
            }
            for c in campaigns
        ],
        "statusLabels": [s["status"] for s in campaign_status],
        "statusValues": [s["count"] for s in campaign_status],
    }
    data_json = json.dumps(payload)

    dashboard_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0; padding: 0; height: 100%;
    background: #0b0f1a;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    color: #e8eaf2;
    overflow: hidden;
  }}
  .wrap {{
    display: grid;
    grid-template-rows: 90px 190px 160px 200px 190px;
    gap: 10px;
    height: 850px;
    padding: 4px 4px 0 4px;
  }}
  .card {{
    background: linear-gradient(160deg, #141a2c 0%, #10152400 100%);
    background-color: #131a2b;
    border: 1px solid #232b40;
    border-radius: 14px;
    padding: 10px 14px;
    min-height: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }}
  .card h4 {{
    margin: 0 0 6px 0; font-size: 12.5px; font-weight: 600;
    color: #aab2c5; text-transform: uppercase; letter-spacing: .04em;
    display: flex; justify-content: space-between; align-items: center;
  }}
  .kpi-row {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; }}
  .kpi {{
    background: #131a2b; border: 1px solid #232b40; border-radius: 12px;
    padding: 8px 10px; display: flex; flex-direction: column; justify-content: center;
  }}
  .kpi .label {{ color: #8b93a7; font-size: 10px; margin-bottom: 3px; }}
  .kpi .value {{ font-size: 17px; font-weight: 700; color: #fff; }}
  .kpi .value.accent {{ color: #6fe2a0; }}
  .row2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; min-height: 0; }}
  .chart-holder {{ position: relative; flex: 1; min-height: 0; }}
  .empty-note {{ color: #6d7690; font-size: 12px; margin: auto; }}
  .list-wrap {{ overflow-y: auto; flex: 1; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; table-layout: fixed; }}
  th {{
    text-align: left; color: #8b93a7; font-weight: 600; font-size: 10.5px;
    text-transform: uppercase; letter-spacing: .03em; padding: 5px 8px;
    border-bottom: 1px solid #232b40; position: sticky; top: 0; background: #131a2b;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }}
  td {{
    padding: 5px 8px; border-bottom: 1px solid #1a2136; color: #dfe3ee;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }}
  tr:hover td {{ background: #171f34; }}
  .pill {{
    display: inline-block; padding: 1px 8px; border-radius: 8px; font-size: 10.5px;
    font-weight: 700; color: #fff; background: #4f8cff;
  }}
  ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
  ::-webkit-scrollbar-thumb {{ background: #2a3350; border-radius: 4px; }}
</style>
</head>
<body>
<div class="wrap">

  <div class="kpi-row">
    <div class="kpi"><div class="label">Total NGOs</div><div class="value" id="kpiTotalNgos">0</div></div>
    <div class="kpi"><div class="label">Verified</div><div class="value accent" id="kpiVerified">0</div></div>
    <div class="kpi"><div class="label">Unverified</div><div class="value" id="kpiUnverified">0</div></div>
    <div class="kpi"><div class="label">Total Donors</div><div class="value" id="kpiDonors">0</div></div>
    <div class="kpi"><div class="label">💰 Total Donated</div><div class="value accent" id="kpiDonated">₹0</div></div>
    <div class="kpi"><div class="label">🙋 Volunteers</div><div class="value" id="kpiVolunteers">0</div></div>
    <div class="kpi"><div class="label">📢 Active Campaigns</div><div class="value accent" id="kpiCampaigns">0</div></div>
  </div>

  <div class="row2">
    <div class="card">
      <h4>NGO Verification Status</h4>
      <div class="chart-holder"><canvas id="verifyChart"></canvas></div>
    </div>
    <div class="card">
      <h4>NGOs by Category</h4>
      <div class="chart-holder"><canvas id="categoryChart"></canvas></div>
    </div>
  </div>

  <div class="card">
    <h4>Donations Trend (by Month)</h4>
    <div class="chart-holder"><canvas id="trendChart"></canvas></div>
  </div>

  <div class="row2">
    <div class="card">
      <h4>🙋 Recently Registered Volunteers</h4>
      <div class="list-wrap">
        <table>
          <thead><tr><th style="width:22%">Name</th><th style="width:22%">Contact</th><th style="width:40%">Campaign</th><th style="width:16%">Date</th></tr></thead>
          <tbody id="volunteerBody"></tbody>
        </table>
      </div>
    </div>
    <div class="card">
      <h4>📢 Active Campaigns</h4>
      <div class="list-wrap">
        <table>
          <thead><tr><th style="width:44%">Title</th><th style="width:26%">NGO</th><th style="width:14%">Goal</th><th style="width:16%">Date</th></tr></thead>
          <tbody id="campaignBody"></tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="card">
    <h4>Campaign Status Breakdown</h4>
    <div class="chart-holder"><canvas id="statusChart"></canvas></div>
  </div>

</div>

<script>
const DATA = {data_json};

function fmtINR(n) {{
  n = Number(n) || 0;
  return "₹" + n.toLocaleString("en-IN", {{ maximumFractionDigits: 0 }});
}}

document.getElementById("kpiTotalNgos").textContent = DATA.totalNgos;
document.getElementById("kpiVerified").textContent = DATA.verified;
document.getElementById("kpiUnverified").textContent = DATA.unverified;
document.getElementById("kpiDonors").textContent = DATA.totalDonors;
document.getElementById("kpiDonated").textContent = fmtINR(DATA.totalDonated);
document.getElementById("kpiVolunteers").textContent = DATA.totalVolunteers;
document.getElementById("kpiCampaigns").textContent = DATA.activeCampaigns;

// ---- Verification donut ----
const verifyCanvas = document.getElementById("verifyChart");
if (DATA.totalNgos > 0) {{
  new Chart(verifyCanvas, {{
    type: "doughnut",
    data: {{
      labels: ["Verified", "Unverified"],
      datasets: [{{ data: [DATA.verified, DATA.unverified], backgroundColor: ["#6fe2a0", "#4f8cff"], borderColor: "#0b0f1a", borderWidth: 2 }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ position: "bottom", labels: {{ color: "#c7cede", boxWidth: 9, font: {{ size: 10 }} }} }} }}
    }}
  }});
}} else {{
  verifyCanvas.parentElement.innerHTML = '<div class="empty-note">No NGOs registered yet.</div>';
}}

// ---- Category donut ----
const categoryCanvas = document.getElementById("categoryChart");
if (DATA.categoryLabels.length) {{
  new Chart(categoryCanvas, {{
    type: "doughnut",
    data: {{
      labels: DATA.categoryLabels,
      datasets: [{{ data: DATA.categoryValues, backgroundColor: ["#4f8cff","#6fe2a0","#f5a623","#e05b4d","#9b6bff","#33c2d6","#f472b6"], borderColor: "#0b0f1a", borderWidth: 2 }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ position: "bottom", labels: {{ color: "#c7cede", boxWidth: 9, font: {{ size: 10 }} }} }} }}
    }}
  }});
}} else {{
  categoryCanvas.parentElement.innerHTML = '<div class="empty-note">No NGOs registered yet.</div>';
}}

// ---- Donations trend line ----
const trendCanvas = document.getElementById("trendChart");
if (DATA.trendLabels.length) {{
  new Chart(trendCanvas, {{
    type: "line",
    data: {{
      labels: DATA.trendLabels,
      datasets: [{{ data: DATA.trendValues, borderColor: "#6fe2a0", backgroundColor: "rgba(111,226,160,0.15)", tension: 0.35, fill: true, pointRadius: 3, pointBackgroundColor: "#6fe2a0" }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ ticks: {{ color: "#8b93a7", font: {{ size: 9 }} }}, grid: {{ color: "#1c2338" }} }},
        y: {{ ticks: {{ color: "#8b93a7", font: {{ size: 9 }} }}, grid: {{ color: "#1c2338" }} }}
      }}
    }}
  }});
}} else {{
  trendCanvas.parentElement.innerHTML = '<div class="empty-note">No donations recorded yet.</div>';
}}

// ---- Volunteers table ----
const volunteerBody = document.getElementById("volunteerBody");
if (DATA.volunteerRows.length) {{
  DATA.volunteerRows.forEach(v => {{
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${{v.name}}</td><td>${{v.contact}}</td><td title="${{v.campaign}}">${{v.campaign}}</td><td>${{v.date}}</td>`;
    volunteerBody.appendChild(tr);
  }});
}} else {{
  volunteerBody.innerHTML = '<tr><td colspan="4" class="empty-note">No volunteers registered yet.</td></tr>';
}}

// ---- Active campaigns table ----
const campaignBody = document.getElementById("campaignBody");
if (DATA.campaignRows.length) {{
  DATA.campaignRows.forEach(c => {{
    const tr = document.createElement("tr");
    tr.innerHTML = `<td title="${{c.title}}">${{c.title}}</td><td>${{c.org}}</td><td>${{fmtINR(c.goal)}}</td><td>${{c.date}}</td>`;
    campaignBody.appendChild(tr);
  }});
}} else {{
  campaignBody.innerHTML = '<tr><td colspan="4" class="empty-note">No active campaigns yet.</td></tr>';
}}

// ---- Campaign status donut ----
const statusCanvas = document.getElementById("statusChart");
if (DATA.statusLabels.length) {{
  new Chart(statusCanvas, {{
    type: "doughnut",
    data: {{
      labels: DATA.statusLabels,
      datasets: [{{ data: DATA.statusValues, backgroundColor: ["#f5a623","#6fe2a0","#e05b4d","#4f8cff"], borderColor: "#0b0f1a", borderWidth: 2 }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ position: "bottom", labels: {{ color: "#c7cede", boxWidth: 9, font: {{ size: 10 }} }} }} }}
    }}
  }});
}} else {{
  statusCanvas.parentElement.innerHTML = '<div class="empty-note">No campaigns created yet.</div>';
}}
</script>
</body>
</html>
"""

    components.html(dashboard_html, height=870, scrolling=False)