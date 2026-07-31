import streamlit as st
import os
from config.database import get_connection
from services.pdf_service import extract_text_from_pdf
from services.scoring_service import calculate_score
from services.report_service import save_report_and_score, get_latest_score_for_org
from services.news_service import get_ngo_news
from apicalls.ai_analyzer import analyze_report_with_ai
from services.campaign_service import get_campaigns_for_org, create_campaign, get_campaign_totals_for_org
import google.generativeai as genai





# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------
CANOPY = "#14332B"      # deep forest green — hero / dark surfaces
MEADOW = "#52B788"      # primary accent — trust, growth
CORAL = "#F4A261"       # warm accent — flags / attention
SKY = "#4CC9F0"         # info accent
PLUM = "#9D6FE0"        # secondary accent
PAPER = "#1a1d24"       # card background (dark)
CANVAS = "#0e1117"      # page background (dark)
INK = "#fafafa"         # primary text (light)
MUTED = "#9aa5a1"       # secondary text (light gray)


def _inject_theme():
    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            .stApp {{
                background: {CANVAS};
            }}
            html, body, [class*="css"] {{
                font-family: 'Inter', sans-serif;
                color: {INK};
            }}
            h1, h2, h3, .nd-display {{
                font-family: 'Poppins', sans-serif !important;
            }}

            /* Hide chrome WITHOUT reserving its layout space */
            #MainMenu, footer, header {{ display: none !important; }}

            /* Reduce the large default top gap above the first element */
            .block-container {{
                padding-top: 1.5rem !important;
                padding-bottom: 2rem !important;
            }}

            /* ---------- Hero banner ---------- */
            .nd-hero {{
                position: relative;
                overflow: hidden;
                background: linear-gradient(135deg, {CANOPY} 0%, #1F4A3B 100%);
                border-radius: 22px;
                padding: 36px 40px;
                margin-bottom: 28px;
                color: #EAF4EF;
            }}
            .nd-hero::before {{
                content: "";
                position: absolute;
                right: -60px; top: -60px;
                width: 220px; height: 220px;
                border-radius: 50%;
                background: radial-gradient(circle, rgba(82,183,136,0.35) 0%, transparent 70%);
            }}
            .nd-hero-eyebrow {{
                font-size: 13px;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: {MEADOW};
                font-weight: 600;
                margin-bottom: 6px;
            }}
            .nd-hero-title {{
                font-family: 'Poppins', sans-serif;
                font-size: 30px;
                font-weight: 700;
                margin: 0 0 6px 0;
                position: relative;
            }}
            .nd-hero-sub {{
                font-size: 14px;
                color: #C9DED3;
                position: relative;
            }}

            /* ---------- Stat cards ---------- */
            .nd-card {{
                background: {PAPER};
                border-radius: 18px;
                padding: 20px 22px;
                box-shadow: 0 2px 10px rgba(20, 51, 43, 0.06);
                border: 1px solid rgba(20, 51, 43, 0.05);
                height: 100%;
            }}
            .nd-stat-icon {{
                width: 38px; height: 38px;
                border-radius: 11px;
                display: flex; align-items: center; justify-content: center;
                font-size: 18px;
                margin-bottom: 12px;
            }}
            .nd-stat-label {{
                font-size: 12px;
                color: {MUTED};
                text-transform: uppercase;
                letter-spacing: 0.05em;
                font-weight: 600;
                margin-bottom: 4px;
            }}
            .nd-stat-value {{
                font-family: 'Poppins', sans-serif;
                font-size: 19px;
                font-weight: 600;
                color: {INK};
                word-break: break-word;
            }}

            /* ---------- Section "cards" (real containers, properly nested) ---------- */
            div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div.st-key-upload_card),
            .st-key-upload_card,
            .st-key-score_card,
            .st-key-campaigns_card {{
                background: {PAPER};
                border-radius: 20px;
                padding: 26px 30px 10px 30px;
                box-shadow: 0 2px 10px rgba(20, 51, 43, 0.06);
                border: 1px solid rgba(20, 51, 43, 0.05);
                margin-bottom: 24px;
            }}
            .nd-section-title {{
                font-family: 'Poppins', sans-serif;
                font-size: 18px;
                font-weight: 600;
                color: {INK};
                margin-bottom: 4px;
            }}
            .nd-section-desc {{
                font-size: 13px;
                color: {MUTED};
                margin-bottom: 18px;
            }}

            /* ---------- Gauge ---------- */
            .nd-gauge-wrap {{
                display: flex;
                align-items: center;
                gap: 26px;
                flex-wrap: wrap;
            }}
            .nd-gauge {{
                width: 140px; height: 140px;
                border-radius: 50%;
                display: flex; align-items: center; justify-content: center;
                background: conic-gradient(
                    {MEADOW} calc(var(--pct) * 1%),
                    #2a2f38 calc(var(--pct) * 1%)
                );
                position: relative;
                flex-shrink: 0;
            }}
            .nd-gauge::after {{
                content: "";
                position: absolute;
                width: 106px; height: 106px;
                border-radius: 50%;
                background: {PAPER};
            }}
            .nd-gauge-value {{
                position: relative;
                font-family: 'Poppins', sans-serif;
                font-size: 26px;
                font-weight: 700;
                color: {INK};
                z-index: 2;
            }}
            .nd-gauge-sub {{
                position: relative;
                font-size: 11px;
                color: {MUTED};
                z-index: 2;
                margin-top: -2px;
            }}

            .nd-empty {{
                background: {CANVAS};
                border: 1px dashed rgba(255,255,255,0.15);
                border-radius: 14px;
                padding: 18px 20px;
                color: {MUTED};
                font-size: 14px;
            }}

            .nd-flag-pill {{
                display: inline-block;
                background: rgba(244,162,97,0.15);
                color: #F4A261;
                border-radius: 999px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: 500;
                margin: 0 8px 8px 0;
            }}

            /* ---------- Campaigns ---------- */
            .nd-campaign-card {{
                background: {CANVAS};
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.06);
                padding: 18px 20px;
                margin-bottom: 14px;
            }}
            .nd-campaign-top {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 12px;
                margin-bottom: 8px;
            }}
            .nd-campaign-title {{
                font-family: 'Poppins', sans-serif;
                font-size: 15px;
                font-weight: 600;
                color: {INK};
            }}
            .nd-campaign-desc {{
                font-size: 13px;
                color: {MUTED};
                margin-bottom: 12px;
            }}
            .nd-badge {{
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.04em;
                padding: 4px 10px;
                border-radius: 999px;
                white-space: nowrap;
            }}
            .nd-badge-pending {{ background: rgba(244,162,97,0.18); color: #F4A261; }}
            .nd-badge-approved {{ background: rgba(82,183,136,0.18); color: #52B788; }}
            .nd-badge-rejected {{ background: rgba(213,90,48,0.15); color: #E07856; }}
            .nd-progress-track {{
                width: 100%;
                height: 8px;
                border-radius: 999px;
                background: #2a2f38;
                overflow: hidden;
                margin-bottom: 8px;
            }}
            .nd-progress-fill {{
                height: 100%;
                background: {MEADOW};
                border-radius: 999px;
            }}
            .nd-campaign-meta {{
                display: flex;
                justify-content: space-between;
                font-size: 12px;
                color: {MUTED};
            }}

            /* File uploader dropzone restyle */
            [data-testid="stFileUploaderDropzone"] {{
                background: {CANVAS} !important;
                border: 1.5px dashed rgba(255,255,255,0.18) !important;
                border-radius: 14px !important;
            }}

            /* Sidebar */
            section[data-testid="stSidebar"] {{
                background: {PAPER};
                border-right: 1px solid rgba(255,255,255,0.06);
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _stat_card(icon, bg, label, value):
    st.markdown(
        f"""
        <div class="nd-card">
            <div class="nd-stat-icon" style="background:{bg}20; color:{bg};">{icon}</div>
            <div class="nd-stat-label">{label}</div>
            <div class="nd-stat-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_news_sidebar():
    st.sidebar.markdown("#### 📰 Latest NGO News")
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

    _inject_theme()
    render_news_sidebar()

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
    latest = get_latest_score_for_org(org_id)
    campaigns = get_campaigns_for_org(org_id)
    campaign_totals = get_campaign_totals_for_org(org_id)

    # ---------------- Hero ----------------
    st.markdown(
        f"""
        <div class="nd-hero">
            <div class="nd-hero-eyebrow">NGO Dashboard</div>
            <div class="nd-hero-title">Welcome back, {org['name']}</div>
            <div class="nd-hero-sub">Track your financial transparency and keep donors informed.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------- Stat cards ----------------
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _stat_card("🏢", MEADOW, "Organization", org["name"])
    with c2:
        _stat_card("🪪", SKY, "Registration No.", org.get("registration_number") or "Not provided")
    with c3:
        score_display = f"{latest['transparency_score']}/100" if latest else "—"
        _stat_card("🛡️", PLUM, "Transparency Score", score_display)
    with c4:
        active = campaign_totals.get("active_count") or 0
        total = campaign_totals.get("campaign_count") or 0
        _stat_card("📣", CORAL, "Active Campaigns", f"{active} of {total}")

    st.write("")

    # ---------------- Upload section (real container — nests correctly) ----------------
    with st.container(key="upload_card"):
        st.markdown('<div class="nd-section-title">Upload Financial Report</div>', unsafe_allow_html=True)
        st.markdown('<div class="nd-section-desc">Upload a PDF financial report to generate an updated transparency score.</div>', unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Choose a PDF", type=["pdf"], label_visibility="collapsed")

        if uploaded_file and st.button("Analyze Report", type="primary"):
            os.makedirs("data/uploaded_reports", exist_ok=True)
            file_path = f"data/uploaded_reports/{org_id}_{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            extracted_text = extract_text_from_pdf(uploaded_file)

            with st.spinner("Running AI transparency analysis..."):
                score_data = analyze_report_with_ai(extracted_text)

            if save_report_and_score(org_id, user_id, file_path, extracted_text, score_data):
                st.success("Report analyzed and saved!")
                if score_data.get("summary"):
                    st.info(score_data["summary"])
                st.rerun()
            else:
                st.error("Something went wrong saving the report.")

    # ---------------- Score section (real container) ----------------
    with st.container(key="score_card"):
        st.markdown('<div class="nd-section-title">Latest Transparency Score</div>', unsafe_allow_html=True)
        st.markdown('<div class="nd-section-desc">A snapshot of how transparent your most recent report is.</div>', unsafe_allow_html=True)

        if latest:
            pct = max(0, min(100, latest["transparency_score"]))
            st.markdown(
                f"""
                <div class="nd-gauge-wrap">
                    <div class="nd-gauge" style="--pct:{pct};">
                        <div style="position:relative; z-index:2; display:flex; flex-direction:column; align-items:center;">
                            <span class="nd-gauge-value">{pct}</span>
                            <span class="nd-gauge-sub">out of 100</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if latest["red_flags"]:
                st.markdown("**Red flags detected:**")
                flags_html = "".join(
                    f'<span class="nd-flag-pill">⚠ {flag}</span>'
                    for flag in latest["red_flags"].split(", ")
                )
                st.markdown(flags_html, unsafe_allow_html=True)
            else:
                st.success("No red flags detected. This report looks clean.")
        else:
            st.markdown(
                '<div class="nd-empty">No reports analyzed yet. Upload one above to see your transparency score.</div>',
                unsafe_allow_html=True,
            )

    # ---------------- Campaigns section (real container) ----------------
    with st.container(key="campaigns_card"):
        st.markdown('<div class="nd-section-title">Campaigns</div>', unsafe_allow_html=True)
        st.markdown('<div class="nd-section-desc">Create a fundraising campaign. It goes live for donors immediately.</div>', unsafe_allow_html=True)
        with st.form("new_campaign_form", clear_on_submit=True):
            title = st.text_input("Campaign title", placeholder="School kits drive")
            description = st.text_area("Description", placeholder="What will this campaign fund?")
            goal_amount = st.number_input("Goal amount (₹)", min_value=0.0, step=100.0)
            submitted = st.form_submit_button("Create campaign", type="primary")

            if submitted:
                if not title.strip():
                    st.error("Give the campaign a title first.")
                else:
                    create_campaign(org_id, title.strip(), description.strip(), goal_amount)
                    st.success("Campaign created and is now live for donors!")
                    st.rerun()

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if campaigns:
            badge_class = {
                "pending": "nd-badge-pending",
                "approved": "nd-badge-approved",
                "rejected": "nd-badge-rejected",
            }
            for c in campaigns:
                goal = c["goal_amount"] or 0
                raised = c["raised"] or 0
                pct = 0 if goal <= 0 else min(100, round((raised / goal) * 100))
                status = c["status"]
                desc = c["description"] or "No description provided."

                st.markdown(
                    f"""
                    <div class="nd-campaign-card">
                        <div class="nd-campaign-top">
                            <div class="nd-campaign-title">{c['title']}</div>
                            <span class="nd-badge {badge_class.get(status, 'nd-badge-pending')}">{status}</span>
                        </div>
                        <div class="nd-campaign-desc">{desc}</div>
                        <div class="nd-progress-track">
                            <div class="nd-progress-fill" style="width:{pct}%;"></div>
                        </div>
                        <div class="nd-campaign-meta">
                            <span>₹{raised:,.0f} raised of ₹{goal:,.0f}</span>
                            <span>{c['donor_count']} donor{'s' if c['donor_count'] != 1 else ''} · {pct}%</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="nd-empty">No campaigns yet. Create one above to start raising funds.</div>',
                unsafe_allow_html=True,
            )