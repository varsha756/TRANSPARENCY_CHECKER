import streamlit as st
from services.campaign_service import get_approved_campaigns, register_volunteer, link_donation_to_campaign
from services.donation_service import record_donation
from components.chat_widget import render_chat_bubble
import textwrap
from components.news_widget import render_news_sidebar
import google.generativeai as genai



# ---------------------------------------------------------------------------
# Design tokens (same palette as the NGO dashboard, for a consistent app feel)
# ---------------------------------------------------------------------------
CANOPY = "#14332B"
MEADOW = "#52B788"
CORAL = "#F4A261"
SKY = "#4CC9F0"
PLUM = "#9D6FE0"
PAPER = "#1a1d24"
CANVAS = "#0e1117"
INK = "#fafafa"
MUTED = "#9aa5a1"


def _inject_theme():
    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            .stApp {{ background: {CANVAS}; }}
            html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; color: {INK}; }}
            h1, h2, h3 {{ font-family: 'Poppins', sans-serif !important; }}
            #MainMenu, footer, header {{ display: none !important; }}
            .block-container {{ padding-top: 1.5rem !important; padding-bottom: 2rem !important; }}

            .cp-hero {{
                position: relative; overflow: hidden;
                background: linear-gradient(135deg, {CANOPY} 0%, #1F4A3B 100%);
                border-radius: 22px; padding: 32px 40px; margin-bottom: 26px; color: #EAF4EF;
            }}
            .cp-hero::before {{
                content: ""; position: absolute; right: -60px; top: -60px;
                width: 220px; height: 220px; border-radius: 50%;
                background: radial-gradient(circle, rgba(82,183,136,0.35) 0%, transparent 70%);
            }}
            .cp-hero-eyebrow {{
                font-size: 13px; letter-spacing: 0.08em; text-transform: uppercase;
                color: {MEADOW}; font-weight: 600; margin-bottom: 6px;
            }}
            .cp-hero-title {{
                font-family: 'Poppins', sans-serif; font-size: 28px; font-weight: 700;
                margin: 0 0 6px 0; position: relative;
            }}
            .cp-hero-sub {{ font-size: 14px; color: #C9DED3; position: relative; }}

            div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[class*="st-key-campaign_card_"]),
[class*="st-key-campaign_card_"] {{
                background: {PAPER}; border-radius: 20px; padding: 24px 28px;
                box-shadow: 0 2px 10px rgba(20, 51, 43, 0.06);
                border: 1px solid rgba(255,255,255,0.05); margin-bottom: 22px;
            }}
            .cp-title {{
                font-family: 'Poppins', sans-serif; font-size: 20px; font-weight: 700; color: {INK};
                margin-bottom: 4px;
            }}
            .cp-desc {{ font-size: 14px; color: {MUTED}; margin-bottom: 16px; line-height: 1.5; }}

            .cp-progress-track {{
                width: 100%; height: 10px; border-radius: 999px; background: #2a2f38;
                overflow: hidden; margin-bottom: 10px;
            }}
            .cp-progress-fill {{
                height: 100%; border-radius: 999px;
                background: linear-gradient(90deg, {MEADOW}, {SKY});
            }}
            .cp-stat-row {{
                display: flex; justify-content: space-between; align-items: center;
                margin-bottom: 18px; flex-wrap: wrap; gap: 10px;
            }}
            .cp-stat {{ display: flex; flex-direction: column; }}
            .cp-stat-label {{
                font-size: 11px; color: {MUTED}; text-transform: uppercase;
                letter-spacing: 0.04em; font-weight: 600;
            }}
            .cp-stat-value {{ font-size: 16px; font-weight: 700; color: {INK}; }}
            .cp-stat-value.accent {{ color: {MEADOW}; }}
            .cp-pct-badge {{
                font-size: 12px; font-weight: 700; padding: 4px 12px; border-radius: 999px;
                background: rgba(82,183,136,0.18); color: {MEADOW};
            }}

            .stButton > button[kind="primary"] {{
                background: {MEADOW} !important; border: none !important; border-radius: 10px !important;
                font-weight: 600 !important;
            }}
            .stButton > button[kind="primary"]:hover {{ background: #3f9d6f !important; }}

            .cp-empty {{
                background: {CANVAS}; border: 1px dashed rgba(255,255,255,0.15); border-radius: 14px;
                padding: 24px; color: {MUTED}; font-size: 14px; text-align: center;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def campaigns_page():
    if not st.session_state.get("logged_in") or st.session_state.get("role") != "donor":
        st.error("Access restricted to Donor accounts.")
        st.stop()

    def _inject_theme():
        st.markdown(
        textwrap.dedent(f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        ...
        </style>
        """),
        unsafe_allow_html=True,
    )

    campaigns = get_approved_campaigns()
    if not campaigns:
        st.markdown(
            '<div class="cp-empty">No approved campaigns right now — check back soon.</div>',
            unsafe_allow_html=True,
        )
        render_chat_bubble()
        return

    for c in campaigns:
        goal = c["goal_amount"] or 0
        raised = c["raised"] or 0
        pct = 0 if goal <= 0 else min(100, round((raised / goal) * 100))

        with st.container(key=f"campaign_card_{c['id']}"):
            st.markdown(f'<div class="cp-title">{c["title"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="cp-desc">{c["description"]}</div>', unsafe_allow_html=True)

            st.markdown(
                f"""
                <div class="cp-progress-track">
                    <div class="cp-progress-fill" style="width:{pct}%;"></div>
                </div>
                <div class="cp-stat-row">
                    <div class="cp-stat">
                        <span class="cp-stat-label">Raised</span>
                        <span class="cp-stat-value accent">₹{raised:,.0f}</span>
                    </div>
                    <div class="cp-stat">
                        <span class="cp-stat-label">Goal</span>
                        <span class="cp-stat-value">₹{goal:,.0f}</span>
                    </div>
                    <div class="cp-stat">
                        <span class="cp-stat-label">Donors</span>
                        <span class="cp-stat-value">{c['donor_count']}</span>
                    </div>
                    <span class="cp-pct-badge">{pct}% funded</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_news_sidebar()


            tab_donate, tab_volunteer = st.tabs(["💰  Donate Money", "🙋  Volunteer"])

            with tab_donate:
                amount = st.number_input(
                    "Amount (₹)", min_value=100.0, step=100.0, key=f"amt_{c['id']}"
                )
                if st.button("Donate Now", key=f"donate_{c['id']}", type="primary"):
                    donation_id = record_donation(
                        st.session_state["user_id"], c["org_id"], amount, "Campaign",
                    )
                    if donation_id:
                        link_donation_to_campaign(c["id"], donation_id)
                        st.success(f"Thanks! ₹{amount:,.0f} donated to {c['title']}.")
                        st.rerun()
                    else:
                        st.error("Something went wrong recording the donation.")

            with tab_volunteer:
                name = st.text_input("Your name", key=f"name_{c['id']}")
                contact = st.text_input("Contact number", key=f"contact_{c['id']}")
                bring = st.text_area("What can you bring?", key=f"bring_{c['id']}")
                if st.button("Register as Volunteer", key=f"vol_{c['id']}", type="primary"):
                    if not name.strip() or not contact.strip():
                        st.error("Please enter your name and contact number.")
                    else:
                        register_volunteer(
                            campaign_id=c["id"], donor_id=st.session_state["user_id"],
                            name=name, contact=contact, contribution=bring,
                        )
                        st.success(f"{name}, you're registered as a volunteer for {c['title']}!")
                        st.rerun()

    render_chat_bubble()