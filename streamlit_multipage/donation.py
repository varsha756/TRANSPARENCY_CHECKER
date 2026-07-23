import streamlit as st
from datetime import datetime
from services.pdf_service import generate_donation_certificate
from services.donation_service import record_donation, get_or_create_org_id


def donation():
    # Full-page: hide sidebar for this step
    st.markdown(
        """<style>[data-testid="stSidebar"] {display: none;}</style>""",
        unsafe_allow_html=True
    )

    st.title("💳 Make a Donation")

    ngo_name = st.session_state.get("selected_ngo", "an NGO")
    st.subheader(f"You're donating to: {ngo_name}")
    st.caption("Every rupee helps. Thank you for your generosity.")

    amount = st.number_input("Enter donation amount (₹)", min_value=10, step=10)

    payment_method = st.selectbox(
        "Select payment method",
        ["UPI", "Credit/Debit Card", "Net Banking"]
    )

    if st.button("Confirm Donation"):
        if amount <= 0:
            st.error("Please enter a valid donation amount.")
        else:
            donor_id = st.session_state.get("user_id")
            donor_name = st.session_state.get("user", {}).get("username", "Donor")
            org_id = get_or_create_org_id(ngo_name)

            txn_id = record_donation(
                donor_id=donor_id,
                org_id=org_id,
                amount=amount,
                category=None,
            )

            if txn_id is None:
                st.error("Something went wrong saving your donation. Please try again.")
            else:
                donated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                st.success(f"🎉 Thank you! Your donation of ₹{amount} to {ngo_name} was successful.")
                st.balloons()

                certificate_bytes = generate_donation_certificate(
                    donor_name=donor_name,
                    ngo_name=ngo_name,
                    amount=amount,
                    donated_at=donated_at,
                )

                st.download_button(
                    label="📄 Download Donation Certificate (PDF)",
                    data=certificate_bytes,
                    file_name=f"donation_certificate_{ngo_name.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                )

    st.divider()

    if st.button("⬅ Back to Marketplace"):
        st.session_state["page"] = "Marketplace"
        st.rerun()