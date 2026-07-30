import streamlit as st
from services.chat_service import get_chatbot_response


def donor_chatbot():
    if not st.session_state.get("logged_in") or st.session_state.get("role") != "donor":
        st.error("Access restricted to Donor accounts.")
        st.stop()

    st.title("💬 TransparencyBot")
    st.caption("Ask me about donations, campaigns, reports, or transparency scores.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []  # list of {"role": "user"/"model", "text": str}

    # Render past messages
    for turn in st.session_state.chat_history:
        role = "user" if turn["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.write(turn["text"])

    # New message input
    user_msg = st.chat_input("Type your question...")
    if user_msg:
        st.session_state.chat_history.append({"role": "user", "text": user_msg})
        with st.chat_message("user"):
            st.write(user_msg)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = get_chatbot_response(user_msg, st.session_state.chat_history[:-1])
            st.write(reply)

        st.session_state.chat_history.append({"role": "model", "text": reply})

    if st.session_state.chat_history:
        if st.button("Clear conversation"):
            st.session_state.chat_history = []
            st.rerun()