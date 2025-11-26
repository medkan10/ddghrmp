import streamlit as st
import bcrypt
from sqlalchemy import text
from db.database import get_engine
from datetime import datetime


def hash_password(password: str) -> str:
    """Hashes a plain password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def check_password(plain_password: str, hashed_password: str) -> bool:
    """Checks if the plain password matches the hashed password."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def authenticate_user(username, password):
    engine = get_engine()
    query = text("SELECT * FROM users WHERE username = :username")
    
    with engine.connect() as conn:
        result = conn.execute(query, {"username": username}).mappings().fetchone()

    if result and check_password(password, result["password"]):
        return {
            "id": result["id"],
            "username": result["username"],
            "role": result["role"],
            "first_name":result["first_name"]
        }
    return None


def register_user(first_name, middle_name, last_name, username, password, role):
    try:
        current_user = st.session_state.get("user", {}).get("username", "system")
        now = datetime.now()
        date = str(now.date())
        time = str(now.time())
        hashed_password = hash_password(password)
        engine = get_engine()
        
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO users 
                    (first_name, middle_name, last_name, username, password, role, added_by, date, time)
                    VALUES 
                    (:first_name, :middle_name, :last_name, :username, :password, :role, :added_by, :date, :time)
                """), 
                {
                    "first_name": first_name,
                    "middle_name": middle_name,
                    "last_name": last_name,
                    "username": username,
                    "password": hashed_password,
                    "role": role,
                    "added_by": current_user,
                    "date": date,
                    "time": time
                }
            )
        return True

    except Exception as e:
        print("Registration Error:", e)
        return False

def login_page_format():
    col1, col2, col3 = st.columns(3)
    with col2:
        st.image("csa.png")
    st.markdown(
        """
        <div style='text-align: center;'>
            <h1>Office of the DDG-HRM/P</h1>
            <p>Welcome to the Office of the DDG-HRM/P's Reporting Platform 🗃️</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def login():
    # st.subheader("🔐 User Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    if login_button:
        user = authenticate_user(username, password)
        if user:
            st.session_state["authenticated"] = True
            st.session_state["user"] = user
            st.session_state["user_id"] = user['id']
            st.success(f"✅ Welcome, {user['username']}!")
            st.rerun()
        else:
            st.error("Invalid username or password")

def logout():
    st.session_state.clear()
    st.rerun()
