"""
Reusable floating chatbot bubble for donor-facing pages.

Usage in any donor page file:

    from components.chat_widget import render_chat_bubble
    ...
    def some_donor_page():
        ...page content...
        render_chat_bubble()   # call once, anywhere in the page function

Calling render_chat_bubble() injects its own scoped CSS and renders a
bottom-right floating chat bubble. Safe to call on multiple pages — each
page's own rerun re-injects the same CSS, which is harmless.
"""
import streamlit as st
from services.chat_service import get_chatbot_response

_CHAT_WIDGET_CSS = """
<style>
/* ---------------- Floating chatbot bubble (shared across pages) ---------------- */
.st-key-chat_bubble {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 9999;
    width: auto !important;
}
/* Only the popover TRIGGER button (direct child of stPopover) becomes the
   round bubble — deliberately does not match buttons inside the open panel
   (Send / Clear), which keep their normal appearance. */
.st-key-chat_bubble div[data-testid="stPopover"] > button {
    border-radius: 50% !important;
    width: 56px !important;
    height: 56px !important;
    font-size: 22px !important;
    background: #4f8cff !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.35) !important;
}
/* Our own inner wrapper controls the visible panel's size/background */
.st-key-chat_panel {
    background: #131a2b !important;
    border: 1px solid #232b40 !important;
    border-radius: 12px;
    padding: 6px 4px;
    width: 300px;
}
/* Compact chat messages so more fit on screen at once */
.st-key-chat_panel [data-testid="stChatMessage"] {
    padding: 4px 6px !important;
    margin-bottom: 2px !important;
    gap: 6px !important;
}
.st-key-chat_panel [data-testid="stChatMessage"] p {
    font-size: 12.5px !important;
    line-height: 1.35 !important;
    margin: 0 !important;
}
.st-key-chat_panel [data-testid="stChatMessageAvatarUser"],
.st-key-chat_panel [data-testid="stChatMessageAvatarAssistant"] {
    width: 22px !important;
    height: 22px !important;
    font-size: 13px !important;
}
</style>
"""


def render_chat_bubble():
    """Renders the floating chatbot bubble. Call once per page, anywhere
    (position in code doesn't matter — it's pinned via fixed CSS)."""
    st.markdown(_CHAT_WIDGET_CSS, unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_input_counter" not in st.session_state:
        st.session_state.chat_input_counter = 0

    with st.container(key="chat_bubble"):
        with st.popover("💬"):
            with st.container(key="chat_panel"):
                st.markdown("**TransparencyBot**")
                st.caption("Ask about donations, campaigns, reports, or scores.")

                chat_box = st.container(height=220)
                with chat_box:
                    if not st.session_state.chat_history:
                        st.caption("Say hi to get started!")
                    for turn in st.session_state.chat_history:
                        role = "user" if turn["role"] == "user" else "assistant"
                        with st.chat_message(role):
                            st.write(turn["text"])

                input_key = f"bubble_text_input_{st.session_state.chat_input_counter}"
                user_msg = st.text_input(
                    "Your question",
                    key=input_key,
                    label_visibility="collapsed",
                    placeholder="Type your question...",
                )
                send_clicked = st.button(
                    "Send", key="bubble_send_btn", use_container_width=True, type="primary"
                )

                if send_clicked and user_msg.strip():
                    msg = user_msg.strip()
                    st.session_state.chat_history.append({"role": "user", "text": msg})
                    reply = get_chatbot_response(msg, st.session_state.chat_history[:-1])
                    st.session_state.chat_history.append({"role": "model", "text": reply})
                    st.session_state.chat_input_counter += 1  # fresh key clears the box
                    st.rerun()

                if st.session_state.chat_history:
                    if st.button("Clear conversation", key="bubble_clear_chat"):
                        st.session_state.chat_history = []
                        st.rerun()