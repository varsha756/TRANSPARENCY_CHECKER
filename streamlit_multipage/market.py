"""
market.py
---------
Donor-facing marketplace page for the Transparency Checker app.

Shows a grid of NGOs with photo, transparency score, mission ("why it was
built"), a breakdown of how donated money is used, and any red flags pulled
from the scoring engine. Donors pick an NGO straight from the card and land
in a donation form for it.

Wire NGO_DATA up to your `scoring_service.py` / `database.py` later — for now
it ships with 5 sample NGOs so the page is demo-ready.

Usage (from main.py):
    from streamlit_multipage.market import market
    market()

Note on implementation: earlier versions of this file built each card as one
big block of raw HTML passed to st.markdown(..., unsafe_allow_html=True).
That's fragile — Streamlit's markdown renderer can misparse long, deeply
nested HTML strings and fall back to showing tags as literal text. This
version avoids that entirely by using native Streamlit components
(st.image, st.progress, st.warning, st.container) for all structural content,
and only uses raw HTML for small, single, unnested <span> tags (the category
pill and score badge), which render reliably.
"""

import streamlit as st

# ----------------------------------------------------------------------------
# Sample data — replace this with a call into your scoring_service / database
# e.g. NGO_DATA = fetch_ngos_with_scores()
# ----------------------------------------------------------------------------
NGO_DATA = [
    {
        "name": "Youth Sanstha",
        "tagline": "Skilling India's next workforce",
        "category": "Youth Empowerment",
        "image": "https://images.unsplash.com/photo-1529390079861-591de354faf5?w=600&h=400&fit=crop",
        "why_built": (
            "Founded in 2014 after its founders saw thousands of rural graduates "
            "leaving college with degrees but no employable skills. Youth Sanstha "
            "runs free vocational training, interview prep, and placement drives "
            "in Tier-2 and Tier-3 towns."
        ),
        "score": 82,
        "fund_use": {"Skill Training Programs": 62, "Placement Drives & Mentorship": 18,
                      "Operations": 13, "Fundraising": 7},
        "red_flags": [],
        "registration_no": "NGO/YS/2014/0417",
    },
    {
        "name": "Sarswati Yojna",
        "tagline": "Keeping girls in school, one scholarship at a time",
        "category": "Girls' Education",
        "image": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=600&h=400&fit=crop",
        "why_built": (
            "Started by a group of teachers in Punjab who noticed girls dropping "
            "out after Class 8 due to school fees and safety concerns. Sarswati "
            "Yojna covers tuition, uniforms, and safe transport for girls from "
            "low-income households."
        ),
        "score": 91,
        "fund_use": {"Scholarships & Fees": 70, "Safe Transport": 15,
                      "Operations": 10, "Fundraising": 5},
        "red_flags": [],
        "registration_no": "NGO/SY/2011/0182",
    },
    {
        "name": "Jal Seva Foundation",
        "tagline": "Clean water, closer to home",
        "category": "Water & Sanitation",
        "image": "https://images.unsplash.com/photo-1541480601022-2308c0f02487?w=600&h=400&fit=crop",
        "why_built": (
            "Set up in 2016 in response to a groundwater contamination crisis "
            "in Malwa. The foundation builds and maintains borewells, water "
            "filtration units, and runs hygiene awareness camps in affected "
            "villages."
        ),
        "score": 76,
        "fund_use": {"Borewells & Filtration Units": 58, "Hygiene Camps": 20,
                      "Operations": 14, "Fundraising": 8},
        "red_flags": ["Annual audit for FY24 filed 5 weeks late"],
        "registration_no": "NGO/JSF/2016/0905",
    },
    {
        "name": "Asha Kiran Trust",
        "tagline": "Healthcare for children who can't wait",
        "category": "Child Healthcare",
        "image": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=600&h=400&fit=crop",
        "why_built": (
            "Launched after a 2018 survey found high rates of untreated childhood "
            "illness in urban slum clusters. Asha Kiran runs mobile clinics and "
            "subsidizes emergency treatment for children under 12."
        ),
        "score": 68,
        "fund_use": {"Mobile Clinics": 48, "Emergency Treatment Subsidy": 22,
                      "Operations": 21, "Fundraising": 9},
        "red_flags": [
            "Transparency score dropped 9 points after Q1 2026 review",
            "No third-party audit on file since 2023",
        ],
        "registration_no": "NGO/AKT/2018/0663",
    },
    {
        "name": "Anna Sewa",
        "tagline": "No one sleeps hungry",
        "category": "Food Security",
        "image": "https://images.unsplash.com/photo-1593113630400-ea4288922497?w=600&h=400&fit=crop",
        "why_built": (
            "Born out of a single soup kitchen during the 2020 lockdowns, Anna "
            "Sewa now runs daily meal distribution and dry-ration kits for "
            "homeless and daily-wage families across three states."
        ),
        "score": 88,
        "fund_use": {"Daily Meal Distribution": 65, "Dry Ration Kits": 15,
                      "Operations": 12, "Fundraising": 8},
        "red_flags": [],
        "registration_no": "NGO/AS/2020/0221",
    },
]


def _score_class(score: int) -> str:
    if score >= 80:
        return "score-high"
    if score >= 60:
        return "score-mid"
    return "score-low"


def _inject_css():
    st.markdown(
        "<style>"
        ".category-pill{display:inline-block;font-size:11px;font-weight:700;"
        "letter-spacing:.04em;text-transform:uppercase;color:#2E7D5B;"
        "background:#E5F3EC;padding:4px 10px;border-radius:20px;}"
        ".score-badge{display:inline-block;font-size:18px;font-weight:800;"
        "padding:3px 10px;border-radius:8px;}"
        ".score-high{background:#E5F3EC;color:#1E7A4C;}"
        ".score-mid{background:#FDF3DA;color:#9A6B00;}"
        ".score-low{background:#FBE7E4;color:#B23A2C;}"
        ".score-label{font-size:12px;color:#888;margin-left:6px;}"
        ".reg-no{font-size:11px;color:#999;margin-top:6px;}"
        "</style>",
        unsafe_allow_html=True,
    )


def _render_card(ngo: dict):
    with st.container(border=True):
        st.image(ngo["image"], use_container_width=True)

        st.markdown(
            f'<span class="category-pill">{ngo["category"]}</span>',
            unsafe_allow_html=True,
        )
        st.markdown(f"#### {ngo['name']}")
        st.caption(ngo["tagline"])

        st.markdown(
            f'<span class="score-badge {_score_class(ngo["score"])}">{ngo["score"]}/100</span>'
            f'<span class="score-label">Transparency Score</span>',
            unsafe_allow_html=True,
        )

        with st.expander("Why it was built"):
            st.write(ngo["why_built"])

        st.markdown("**How funds are used:**")
        for label, pct in ngo["fund_use"].items():
            st.progress(pct / 100, text=f"{label} — {pct}%")

        if ngo["red_flags"]:
            for flag in ngo["red_flags"]:
                st.warning(flag, icon="⚠️")

        st.markdown(f'<div class="reg-no">Reg. No: {ngo["registration_no"]}</div>', unsafe_allow_html=True)

        if st.button(f"Donate to {ngo['name']} →", key=f"donate_{ngo['name']}", use_container_width=True):
            st.session_state.selected_ngo = ngo["name"]


def market():
    """Render the NGO marketplace. Call this from main.py after donor login."""

    _inject_css()

    st.title("🌱 Find an NGO to Support")
    st.caption(
        "Every organization below is scored by our transparency engine based on "
        "audit filings, fund utilization, and reporting consistency. Pick one and "
        "see exactly how your money will be used before you donate."
    )

    if "selected_ngo" not in st.session_state:
        st.session_state.selected_ngo = None

    categories = ["All"] + sorted({ngo["category"] for ngo in NGO_DATA})
    selected_category = st.selectbox("Filter by cause", categories)

    filtered = [n for n in NGO_DATA if selected_category == "All" or n["category"] == selected_category]

    cols_per_row = 3
    for i in range(0, len(filtered), cols_per_row):
        row_ngos = filtered[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, ngo in zip(cols, row_ngos):
            with col:
                _render_card(ngo)

    st.divider()

    if st.session_state.selected_ngo:
        chosen = next(n for n in NGO_DATA if n["name"] == st.session_state.selected_ngo)
        st.subheader(f"💳 Donate to {chosen['name']}")
        st.write(f"Transparency Score: **{chosen['score']}/100** · {chosen['category']}")

        with st.form("donation_form"):
            c1, c2 = st.columns(2)
            with c1:
                donor_name = st.text_input("Your name")
                amount = st.number_input("Amount (₹)", min_value=100, step=100, value=1000)
            with c2:
                donor_email = st.text_input("Email")
                anonymous = st.checkbox("Donate anonymously")

            submitted = st.form_submit_button("Confirm donation & generate report", use_container_width=True)
            if submitted:
                if not donor_name or not donor_email:
                    st.error("Please fill in your name and email.")
                else:
                    st.success(
                        f"Thank you{'' if anonymous else ', ' + donor_name}! "
                        f"₹{amount:,.0f} has been directed to {chosen['name']}. "
                        "Your transparency report is being generated — this is where "
                        "you'd call your existing `report_service.py` / `donor_report.py` "
                        "to produce the PDF/QR receipt."
                    )
    else:
        st.info("Select an NGO above to start a donation.")