import streamlit as st
from pymongo import MongoClient
import bcrypt
from quiz_module import dashboard
import os
from dotenv import load_dotenv
load_dotenv()

#from quiz_module import paragraph_quiz, subject_topic_quiz  # Import quiz functions
from forgot_password import forgot_password_app  # Import forgot password app

# Get the MongoDB URI from the .env file
mongo_uri = os.getenv("MONGO_URI")

# --- MongoDB Connection ---
mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    st.error("❌ MONGO_URI not found in .env file")
else:
    client = MongoClient(mongo_uri)
    db = client["quizApp"]          # ✅ Select database
    users_collection = db["users"]  # ✅ Select collection


# --- Helper Functions ---
def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def verify_password(password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed)

def register_user(username: str, email: str, password: str):
    if users_collection.find_one({"username": username}):
        return False, "⚠ Username already exists"
    if users_collection.find_one({"email": email}):
        return False, "⚠ Email already registered"
    hashed = hash_password(password)
    users_collection.insert_one({
        "username": username,
        "email": email,
        "password": hashed
    })
    return True, "✅ Registration successful! Please log in."

def login_user(email: str, password: str):
    user = users_collection.find_one({"email": email})
    if user and verify_password(password, user["password"]):
        return True, user["username"]
    return False, None

# --- User Dashboard ---
def user_dashboard(username: str):
    st.subheader(f"Welcome, {username} 🎉")
    dashboard()

# --- Main App ---
def main():
    st.set_page_config(page_title="SmartQuizzer Auth", layout="centered")
    st.title("SmartQuizzer - Learn. Adapt. Excel")

    # Initialize session state
    if "page" not in st.session_state:
        st.session_state["page"] = "login"  # Default page

    # ---------------- LOGIN PAGE ----------------
    if st.session_state["page"] == "login":
        st.subheader("🔑 Login to Your Account")

        email = st.text_input("Email ID")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            success, username = login_user(email, password)
            if success:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success(f"Welcome {username}! 🎉")
                st.session_state["page"] = "dashboard"
                st.rerun()

            else:
                st.error("❌ Invalid email or password")

        # Links below the login form
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🆕 New User? Register"):
                st.session_state["page"] = "register"
                st.rerun()

        with col2:
            if st.button("🔁 Forgot Password?"):
                st.session_state["page"] = "forgot"
                st.rerun()


    # ---------------- REGISTER PAGE ----------------
    elif st.session_state["page"] == "register":
        st.subheader("📝 Create a New Account")
        with st.form("register_form"):
            username = st.text_input("Username")
            email = st.text_input("Email ID")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Register")

            if submitted:
                if password != confirm_password:
                    st.error("❌ Passwords do not match!")
                elif len(password) < 6:
                    st.warning("⚠ Password should be at least 6 characters long")
                else:
                    success, msg = register_user(username, email, password)
                    if success:
                        st.success(msg)
                        st.session_state["page"] = "login"
                        st.rerun()

                    else:
                        st.error(msg)

        if st.button("⬅ Back to Login"):
            st.session_state["page"] = "login"
            st.rerun()


    # ---------------- FORGOT PASSWORD PAGE ----------------
    elif st.session_state["page"] == "forgot":
        forgot_password_app()
        if st.button("⬅ Back to Login"):
            st.session_state["page"] = "login"
            st.rerun()


    # ---------------- DASHBOARD ----------------
    elif st.session_state.get("logged_in") and st.session_state["page"] == "dashboard":
        user_dashboard(st.session_state["username"])
        if st.button(" Logout"):
            st.session_state.clear()
            st.rerun()


if __name__ == "__main__":
    main()