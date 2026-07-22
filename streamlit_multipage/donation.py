import streamlit as st

NGO_DATA = [
    {"name": "Youth Sanstha", "tagline": "Skilling India's next workforce", "category": "Youth Empowerment",
     "image": "https://images.unsplash.com/photo-1529390079861-591de354faf5?w=600&h=400&fit=crop", "score": 82},
    {"name": "Sarswati Yojna", "tagline": "Keeping girls in school", "category": "Girls' Education",
     "image": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=600&h=400&fit=crop", "score": 91},
    {"name": "Jal Seva Foundation", "tagline": "Clean water, closer to home", "category": "Water & Sanitation",
     "image": "https://images.unsplash.com/photo-1541480601022-2308c0f02487?w=600&h=400&fit=crop", "score": 76},
    {"name": "Asha Kiran Trust", "tagline": "Healthcare for children", "category": "Child Healthcare",
     "image": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=600&h=400&fit=crop", "score": 68},
    {"name": "Anna Sewa", "tagline": "No one sleeps hungry", "category": "Food Security",
     "image": "https://images.unsplash.com/photo-1593113630400-ea4288922497?w=600&h=400&fit=crop", "score": 88},
]


def _score_class(score: int) -> str:
    if score >= 80:
        return "🟢 High"
    if score >= 60:
        return "🟡 Medium"
    return "🔴 Low"


def market():
    st.title("🌱 NGO Marketplace")
    st.caption("Browse NGOs and pick one to donate.")

    categories = ["All"] + sorted({ngo["category"] for ngo in NGO_DATA})
    selected_category = st.selectbox("Filter by cause", categories)

    filtered = [n for n in NGO_DATA if selected_category == "All" or n["category"] == selected_category]

    cols_per_row = 3
    for i in range(0, len(filtered), cols_per_row):
        row_ngos = filtered[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, ngo in zip(cols, row_ngos):
            with col:
                st.image(ngo["image"], use_container_width=True)
                st.subheader(ngo["name"])
                st.caption(ngo["tagline"])
                st.write(f"Transparency Score: {_score_class(ngo['score'])}")
                if st.button(f"View {ngo['name']} →", key=f"view_{ngo['name']}"):
                    st.session_state.selected_ngo = ngo["name"]
                    # FIX: this app uses a custom function-based router (see main.py),
                    # not Streamlit's native pages/ folder, so st.switch_page("donation.py")
                    # can never work here. Instead we flip the router's session-state key
                    # and force a rerun, exactly like the sidebar navigation does.
                    st.session_state["page"] = "Donation"
                    st.rerun()