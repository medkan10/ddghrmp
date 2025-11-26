import os, sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

UTILS_DIR = os.path.join(ROOT_DIR, "utils")
if UTILS_DIR not in sys.path:
    sys.path.insert(0, UTILS_DIR)


import streamlit as st
import importlib
from auth import login, logout, login_page_format  
import os, sys


st.set_page_config(page_title="Office of the DDG-HRM/P Reporting System", layout="wide")
col1, col2, col3 = st.columns(3)
with col2:
    login_page_format()

# Role-based page definitions
PAGE_CONFIG = {
    "Admin": {
        "Dashboard": "dashboard",
        "Upload Transactions": "bulk_upload",
        "Change Password": "change_password",
        "Add User": "register_user"
    },
    "Staff": {
        "Dashboard": "dashboard",
    }

}

# Main control flow
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    with col2:
        login()
else:
    role = st.session_state["user"]["role"]
    username = st.session_state["user"]["username"]
    first_name = st.session_state["user"]["first_name"]

    st.sidebar.image("csa.png")
    st.sidebar.title(f"👋 Welcome, {first_name}")
    st.sidebar.caption(f"Role: `{role}`")

    # Navigation based on role
    allowed_pages = PAGE_CONFIG.get(role, {})
    page_choice = st.sidebar.radio("📂 Application Menu", list(allowed_pages.keys()))

    # Load and run selected page
    module_name = allowed_pages[page_choice]
    module = importlib.import_module(module_name)
    module.run()

    # Logout button
    if st.sidebar.button("🚪 Logout"):
        logout()

def footer():
    style = """
    <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: white;
            color: black;
            text-align: center;
            padding: 10px;
        }
        .footer p {
        line-height: .5em;
        }
    </style>
    """
    
    footer_html = f"""
    <div class="footer">
        <p>© 2025 Office of the DDG-HRM/P.</p>
        <p>Developed with ❤️ by <a href="https://web.facebook.com/ahmed.kanneh.1" target="_blank">Ahmed (Technical Assistant)</a></p>
    </div>
    """
    
    st.markdown(style + footer_html, unsafe_allow_html=True)

# Your app content here...

# Add footer at the end
footer()