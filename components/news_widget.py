import streamlit as st
from services.news_service import get_ngo_news


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