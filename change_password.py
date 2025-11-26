import streamlit as st
from db_operations import update_user_password

st.title("🔐 Change Your Password")
def run():
    current_user = st.session_state.get("user", {}).get("username", "system")

    # Replace this with your login logic or session
    username = st.text_input("Username", value=current_user, disabled=True)

    with st.form("change_password_form", clear_on_submit=True):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")

        submitted = st.form_submit_button("Update Password")

        if submitted:
            if not username or not current_password or not new_password or not confirm_password:
                st.warning("⚠️ All fields are required.")
            elif new_password != confirm_password:
                st.error("🚫 New passwords do not match.")
            else:
                try:
                    update_user_password(username, current_password, new_password)
                    st.success("✅ Password updated successfully.")
                except ValueError as ve:
                    st.error(f"❌ {ve}")
                except Exception as e:
                    st.error(f"❌ Failed to update password: {e}")
