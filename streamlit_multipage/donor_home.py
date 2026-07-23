import json
import streamlit as st
import streamlit.components.v1 as components
from services.donation_service import (
    get_donor_summary, get_recent_donations, get_impact_breakdown,
    get_donation_trend, get_highest_donations
)
from services.report_service import get_all_org_scores

# ---------------------------------------------------------------------------
# Page-level CSS: strip Streamlit's default padding so our fixed-height
# component fills the viewport without adding its own scrollbar.
# ---------------------------------------------------------------------------
PAGE_CSS = """
<style>
.block-container { padding-top: 1.2rem; padding-bottom: 0.5rem; max-width: 100% !important; }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
</style>
"""


def _safe_num(x, default=0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def donor_home():
    st.markdown(PAGE_CSS, unsafe_allow_html=True)

    donor_id = st.session_state["user_id"]
    user = st.session_state["user"]

    # ---- Pull data from services (unchanged calls / shapes) --------------
    summary = get_donor_summary(donor_id) or {}
    recent = get_recent_donations(donor_id) or []
    impact = get_impact_breakdown(donor_id) or {}
    trend = get_donation_trend(donor_id) or []
    top_ngos = (get_all_org_scores() or [])[:5]
    highest = get_highest_donations() or []

    total = _safe_num(summary.get("total"), 0)
    count = int(summary.get("count", 0) or 0)
    avg_donation = (total / count) if count else 0
    ngos_supported = len(impact) if impact else len({d.get("org_name") for d in recent if d.get("org_name")})
    highest_single = 0
    if highest:
        highest_single = max(_safe_num(h.get("amount"), 0) for h in highest)
    elif recent:
        highest_single = max(_safe_num(d.get("amount"), 0) for d in recent)

    # A friendly "suggested" giving goal — purely a UI motivator, not a
    # backend fact, so we label it clearly as "Suggested" in the UI.
    goal = max(total * 1.5, 500)
    goal_pct = min(100, round((total / goal) * 100, 1)) if goal else 0

    # ---- Shape data for the JS charts / tables ----------------------------
    impact_labels = list(impact.keys())
    impact_values = [round(_safe_num(v), 2) for v in impact.values()]

    trend_labels = [str(t.get("month", "")) for t in trend]
    trend_values = [_safe_num(t.get("total"), 0) for t in trend]

    ngo_rows = [
        {
            "rank": i + 1,
            "name": org.get("name", "Unknown"),
            "score": _safe_num(org.get("transparency_score"), 0),
        }
        for i, org in enumerate(top_ngos)
    ]

    recent_rows = [
        {
            "org": d.get("org_name", "—"),
            "amount": _safe_num(d.get("amount"), 0),
            "date": str(d.get("donated_at", "")),
        }
        for d in recent
    ]

    highest_rows = [
        {
            "donor": h.get("donor", "—"),
            "amount": _safe_num(h.get("amount"), 0),
            "org": h.get("org_name", "—"),
            "date": str(h.get("donated_at", "")),
        }
        for h in highest
    ]

    payload = {
        "username": user.get("username", "Donor"),
        "total": total,
        "count": count,
        "avg": avg_donation,
        "ngos": ngos_supported,
        "highestSingle": highest_single,
        "goal": goal,
        "goalPct": goal_pct,
        "impactLabels": impact_labels,
        "impactValues": impact_values,
        "trendLabels": trend_labels,
        "trendValues": trend_values,
        "ngoRows": ngo_rows,
        "recentRows": recent_rows,
        "highestRows": highest_rows,
    }
    data_json = json.dumps(payload)

    # ---- The dashboard itself: one fixed-height HTML/JS component --------
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

  /* FIX: header row is now flexible (minmax) instead of a hard 56px,
     so if the header wraps to two lines it grows instead of overflowing
     into the KPI row below it. */
  .wrap {{
    display: grid;
    grid-template-rows: minmax(56px, auto) 118px 260px 190px 200px;
    gap: 14px;
    height: 1010px;
    padding: 4px 4px 0 4px;
  }}
  .card {{
    background: linear-gradient(160deg, #141a2c 0%, #10152400 100%);
    background-color: #131a2b;
    border: 1px solid #232b40;
    border-radius: 14px;
    padding: 14px 18px;
    min-height: 0;
    overflow: hidden; /* FIX: safety net so no child ever visually bleeds into the next grid row */
    display: flex;
    flex-direction: column;
  }}
  .card h4 {{
    margin: 0 0 8px 0; font-size: 13.5px; font-weight: 600;
    color: #aab2c5; text-transform: uppercase; letter-spacing: .04em;
    display: flex; align-items: center; gap: 6px; justify-content: space-between;
  }}
  /* Header */
  .header-row {{
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap;   /* FIX: allow actions to drop to a new line instead of overflowing */
    row-gap: 8px;
  }}
  .title-block h1 {{ margin: 0; font-size: 22px; font-weight: 700; color: #fff; }}
  .title-block .sub {{ color: #8b93a7; font-size: 12.5px; margin-top: 2px; }}
  .header-actions {{
    display: flex; gap: 10px; align-items: center;
    flex-wrap: wrap;    /* FIX: buttons/search wrap together, no clipping */
  }}
  .search-box {{
    background: #10162a; border: 1px solid #262f47; border-radius: 8px;
    padding: 7px 12px; color: #e8eaf2; font-size: 13px;
    width: 220px;
    min-width: 140px;   /* FIX: shrink before wrapping, so it fits more often */
    flex-shrink: 1;
    outline: none;
  }}
  .search-box::placeholder {{ color: #5c6580; }}
  .btn {{
    background: #4f8cff; color: #fff; border: none; border-radius: 8px;
    padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer;
    white-space: nowrap;
  }}
  .btn:hover {{ background: #3b76e6; }}
  .btn.ghost {{
    background: transparent; border: 1px solid #33405e; color: #cfd5e6;
  }}
  .btn.ghost:hover {{ border-color: #4f8cff; color: #fff; }}

  /* KPI row */
  .kpi-row {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; }}
  .kpi {{
    background: #131a2b; border: 1px solid #232b40; border-radius: 14px;
    padding: 14px 16px; display: flex; flex-direction: column; justify-content: center;
  }}
  .kpi .label {{ color: #8b93a7; font-size: 12px; margin-bottom: 6px; }}
  .kpi .value {{ font-size: 24px; font-weight: 700; color: #fff; }}
  .kpi .value.accent {{ color: #6fe2a0; }}

  /* Row 3: charts + leaderboard */
  .row3 {{ display: grid; grid-template-columns: 1.1fr 1.3fr 1fr; gap: 14px; min-height: 0; }}
  .chart-holder {{ position: relative; flex: 1; min-height: 0; }}

  .ngo-item {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 7px 0; border-bottom: 1px solid #1c2338;
  }}
  .ngo-item:last-child {{ border-bottom: none; }}
  .ngo-rank {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 20px; height: 20px; border-radius: 50%; font-size: 11px; font-weight: 700;
    color: #fff; margin-right: 8px;
  }}
  .ngo-name {{ font-size: 13.5px; color: #dfe3ee; display: flex; align-items: center; }}
  .score-pill {{
    color: #fff; padding: 2px 10px; border-radius: 8px; font-size: 12px; font-weight: 700;
  }}
  .ngo-list {{ overflow-y: auto; flex: 1; }}

  /* Row 4: recent donations + goal */
  .row4 {{ display: grid; grid-template-columns: 1.6fr 1fr; gap: 14px; min-height: 0; }}
  .recent-list {{ overflow-y: auto; flex: 1; padding-right: 4px; }}
  .recent-item {{
    display: flex; justify-content: space-between; align-items: baseline;
    padding: 8px 0; border-bottom: 1px solid #1c2338; font-size: 13px;
  }}
  .recent-item .org {{ font-weight: 600; color: #fff; }}
  .recent-item .date {{ color: #6d7690; font-size: 11px; }}
  .recent-item .amt {{ color: #6fe2a0; font-weight: 700; }}
  .hidden {{ display: none !important; }}

  .goal-box {{ display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; gap: 6px; }}
  .goal-sub {{ color: #6d7690; font-size: 11px; text-align: center; }}

  /* Row 5: highest donations table */
  .table-wrap {{ overflow-y: auto; flex: 1; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{
    text-align: left; color: #8b93a7; font-weight: 600; font-size: 11.5px;
    text-transform: uppercase; letter-spacing: .03em; padding: 6px 10px;
    border-bottom: 1px solid #232b40; cursor: pointer; user-select: none;
    position: sticky; top: 0; background: #131a2b;
  }}
  th:hover {{ color: #4f8cff; }}
  td {{ padding: 7px 10px; border-bottom: 1px solid #1a2136; color: #dfe3ee; }}
  tr:hover td {{ background: #171f34; }}
  .amount-cell {{ color: #6fe2a0; font-weight: 700; }}
  .empty-note {{ color: #6d7690; font-size: 13px; margin: auto; }}

  ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
  ::-webkit-scrollbar-thumb {{ background: #2a3350; border-radius: 4px; }}
</style>
</head>
<body>
<div class="wrap">

  <!-- Header -->
  <div class="card header-row" style="padding: 10px 18px;">
    <div class="title-block">
      <h1>Donor Dashboard</h1>
      <div class="sub" id="welcomeMsg"></div>
    </div>
    <div class="header-actions">
      <input class="search-box" id="searchBox" placeholder="Search recent donations by NGO..." />
      <button class="btn ghost" id="exportBtn">⬇ Export CSV</button>
    </div>
  </div>

  <!-- KPI row -->
  <div class="kpi-row">
    <div class="kpi"><div class="label">❤️ Total Donations</div><div class="value" id="kpiTotal">₹0</div></div>
    <div class="kpi"><div class="label">Number of Donations</div><div class="value" id="kpiCount">0</div></div>
    <div class="kpi"><div class="label">Average Donation</div><div class="value" id="kpiAvg">₹0</div></div>
    <div class="kpi"><div class="label">NGOs Supported</div><div class="value accent" id="kpiNgos">0</div></div>
    <div class="kpi"><div class="label">🏆 Highest Single Gift</div><div class="value accent" id="kpiHighest">₹0</div></div>
  </div>

  <!-- Charts + leaderboard -->
  <div class="row3">
    <div class="card">
      <h4>Impact Overview</h4>
      <div class="chart-holder"><canvas id="impactChart"></canvas></div>
    </div>
    <div class="card">
      <h4>Donation Trend</h4>
      <div class="chart-holder"><canvas id="trendChart"></canvas></div>
    </div>
    <div class="card">
      <h4>Top NGOs by Transparency</h4>
      <div class="ngo-list" id="ngoList"></div>
    </div>
  </div>

  <!-- Recent donations + goal -->
  <div class="row4">
    <div class="card">
      <h4>Recent Donations <span id="recentCount" style="color:#4f8cff;font-size:11px;"></span></h4>
      <div class="recent-list" id="recentList"></div>
    </div>
    <div class="card">
      <h4>🎯 Giving Goal <span style="font-weight:400; text-transform:none; color:#5c6580;">(suggested)</span></h4>
      <div class="goal-box">
        <div class="chart-holder" style="width:120px;height:120px;flex:none;">
          <canvas id="goalRing"></canvas>
        </div>
        <div id="goalLabel" style="font-size:20px;font-weight:700;color:#fff;"></div>
        <div class="goal-sub" id="goalSub"></div>
      </div>
    </div>
  </div>

  <!-- Highest donations table -->
  <div class="card">
    <h4>🏆 Highest Donations <span style="font-weight:400;text-transform:none;color:#5c6580;font-size:11px;">click a column to sort</span></h4>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th data-key="donor">Donor</th>
            <th data-key="amount">Amount</th>
            <th data-key="org">Organization</th>
            <th data-key="date">Donated At</th>
          </tr>
        </thead>
        <tbody id="highestBody"></tbody>
      </table>
    </div>
  </div>

</div>

<script>
const DATA = {data_json};

function fmtINR(n) {{
  n = Number(n) || 0;
  return "₹" + n.toLocaleString("en-IN", {{ maximumFractionDigits: 0 }});
}}

document.getElementById("welcomeMsg").textContent = "Welcome back, " + DATA.username + "!";
document.getElementById("kpiTotal").textContent = fmtINR(DATA.total);
document.getElementById("kpiCount").textContent = DATA.count;
document.getElementById("kpiAvg").textContent = fmtINR(DATA.avg);
document.getElementById("kpiNgos").textContent = DATA.ngos;
document.getElementById("kpiHighest").textContent = fmtINR(DATA.highestSingle);

// ---- Impact donut ----
const impactCanvas = document.getElementById("impactChart");
if (DATA.impactLabels.length) {{
  new Chart(impactCanvas, {{
    type: "doughnut",
    data: {{
      labels: DATA.impactLabels,
      datasets: [{{
        data: DATA.impactValues,
        backgroundColor: ["#4f8cff","#6fe2a0","#f5a623","#e05b4d","#9b6bff","#33c2d6"],
        borderWidth: 0,
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ position: "bottom", labels: {{ color: "#c7cede", boxWidth: 10, font: {{ size: 11 }} }} }} }}
    }}
  }});
}} else {{
  impactCanvas.parentElement.innerHTML = '<div class="empty-note">No donations yet.</div>';
}}

// ---- Trend line ----
const trendCanvas = document.getElementById("trendChart");
if (DATA.trendLabels.length) {{
  new Chart(trendCanvas, {{
    type: "line",
    data: {{
      labels: DATA.trendLabels,
      datasets: [{{
        data: DATA.trendValues,
        borderColor: "#4f8cff",
        backgroundColor: "rgba(79,140,255,0.15)",
        tension: 0.35, fill: true, pointRadius: 3, pointBackgroundColor: "#4f8cff",
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ ticks: {{ color: "#8b93a7", font: {{ size: 10 }} }}, grid: {{ color: "#1c2338" }} }},
        y: {{ ticks: {{ color: "#8b93a7", font: {{ size: 10 }} }}, grid: {{ color: "#1c2338" }} }}
      }}
    }}
  }});
}} else {{
  trendCanvas.parentElement.innerHTML = '<div class="empty-note">No trend data yet.</div>';
}}

// ---- Goal ring ----
const goalCanvas = document.getElementById("goalRing");
new Chart(goalCanvas, {{
  type: "doughnut",
  data: {{
    datasets: [{{
      data: [DATA.goalPct, Math.max(0, 100 - DATA.goalPct)],
      backgroundColor: ["#6fe2a0", "#1c2338"],
      borderWidth: 0,
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false, cutout: "72%",
    plugins: {{ legend: {{ display: false }}, tooltip: {{ enabled: false }} }}
  }}
}});
document.getElementById("goalLabel").textContent = DATA.goalPct + "%";
document.getElementById("goalSub").textContent = fmtINR(DATA.total) + " of " + fmtINR(DATA.goal) + " goal";

// ---- Top NGOs leaderboard ----
const rankColors = {{1: "#f5a623", 2: "#e05b4d", 3: "#3fae5c", 4: "#4f8cff", 5: "#9b6bff"}};
const ngoList = document.getElementById("ngoList");
if (DATA.ngoRows.length) {{
  DATA.ngoRows.forEach(o => {{
    const color = rankColors[o.rank] || "#4f8cff";
    const el = document.createElement("div");
    el.className = "ngo-item";
    el.innerHTML = `
      <span class="ngo-name"><span class="ngo-rank" style="background:${{color}}">${{o.rank}}</span>${{o.name}}</span>
      <span class="score-pill" style="background:${{color}}">${{o.score}}</span>`;
    ngoList.appendChild(el);
  }});
}} else {{
  ngoList.innerHTML = '<div class="empty-note">No NGO data yet.</div>';
}}

// ---- Recent donations (with live search) ----
const recentList = document.getElementById("recentList");
document.getElementById("recentCount").textContent = "(" + DATA.recentRows.length + ")";
function renderRecent(filter) {{
  recentList.innerHTML = "";
  const f = (filter || "").toLowerCase();
  const rows = DATA.recentRows.filter(r => r.org.toLowerCase().includes(f));
  if (!rows.length) {{
    recentList.innerHTML = '<div class="empty-note">No matching donations.</div>';
    return;
  }}
  rows.forEach(d => {{
    const el = document.createElement("div");
    el.className = "recent-item";
    el.innerHTML = `
      <span><span class="org">${{d.org}}</span><br><span class="date">${{d.date}}</span></span>
      <span class="amt">${{fmtINR(d.amount)}}</span>`;
    recentList.appendChild(el);
  }});
}}
renderRecent("");
document.getElementById("searchBox").addEventListener("input", (e) => renderRecent(e.target.value));

// ---- Highest donations table (sortable) ----
let sortState = {{ key: "amount", dir: -1 }};
const highestBody = document.getElementById("highestBody");
function renderHighest() {{
  highestBody.innerHTML = "";
  if (!DATA.highestRows.length) {{
    highestBody.innerHTML = '<tr><td colspan="4" class="empty-note">No donations yet.</td></tr>';
    return;
  }}
  const rows = [...DATA.highestRows].sort((a, b) => {{
    const va = a[sortState.key], vb = b[sortState.key];
    if (typeof va === "number") return (va - vb) * sortState.dir;
    return String(va).localeCompare(String(vb)) * sortState.dir;
  }});
  rows.forEach(r => {{
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${{r.donor}}</td>
      <td class="amount-cell">${{fmtINR(r.amount)}}</td>
      <td>${{r.org}}</td>
      <td>${{r.date}}</td>`;
    highestBody.appendChild(tr);
  }});
}}
renderHighest();
document.querySelectorAll("th[data-key]").forEach(th => {{
  th.addEventListener("click", () => {{
    const key = th.getAttribute("data-key");
    sortState.dir = (sortState.key === key) ? -sortState.dir : -1;
    sortState.key = key;
    renderHighest();
  }});
}});

// ---- CSV export ----
document.getElementById("exportBtn").addEventListener("click", () => {{
  const rows = [["Donor", "Amount", "Organization", "Donated At"]];
  DATA.highestRows.forEach(r => rows.push([r.donor, r.amount, r.org, r.date]));
  const csv = rows.map(r => r.map(v => `"${{String(v).replace(/"/g, '""')}}"`).join(",")).join("\\n");
  const blob = new Blob([csv], {{ type: "text/csv" }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "donations_export.csv"; a.click();
  URL.revokeObjectURL(url);
}});
</script>
</body>
</html>
"""

    components.html(dashboard_html, height=1030, scrolling=False)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ New Donation", use_container_width=True):
            st.session_state["page"] = "Marketplace"
            st.rerun()
    with col2:
        if st.button("🔍 Search NGOs", use_container_width=True):
            st.session_state["page"] = "Search NGOs"
            st.rerun()