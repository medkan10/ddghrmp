import streamlit as st
# from db_operations import insert_user  # Make sure this is correctly imported
from auth import register_user

st.title("👤 Register a New User")

def run():
    # --- Registration Form ---
    with st.form("register_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name", max_chars=50)
            middle_name = st.text_input("Middle Name (Optional)", max_chars=50)
            username = st.text_input("Username", max_chars=50)
        with col2:
            last_name = st.text_input("Last Name", max_chars=50)
            role = st.selectbox("User Role", ["Admin", "Staff", "Viewer"])

        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        added_by = st.text_input("Added By (optional)", placeholder="Leave blank if self-registered")

        submitted = st.form_submit_button("Register")

        if submitted:
            if not first_name or not last_name or not username or not password or not confirm_password:
                st.warning("⚠️ Please fill out all required fields.")
            elif password != confirm_password:
                st.error("🚫 Passwords do not match.")
            else:
                try:
                    register_user(
                        first_name, middle_name, last_name,
                        username, password, role
                    )
                    st.success(f"✅ User '{username}' registered successfully.")
                except Exception as e:
                    st.error(f"❌ Registration failed: {e}")
