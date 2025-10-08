import streamlit as st
from pymongo import MongoClient
import bcrypt
import os
from dotenv import load_dotenv
load_dotenv()


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
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def reset_password(email, new_password):
    user = users_collection.find_one({"email": email})
    if user:
        hashed = hash_password(new_password)
        users_collection.update_one({"email": email}, {"$set": {"password": hashed}})
        return True
    return False

# --- Forgot Password App ---
def forgot_password_app():
    st.title("🔑 Reset Your Password")

    email = st.text_input("Enter your registered Email")
    new_password = st.text_input("Enter New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")

    if st.button("Reset Password"):
        if new_password != confirm_password:
            st.error("❌ Passwords do not match!")
        elif reset_password(email, new_password):
            st.success("✅ Password reset successful! You can log in now.")
        else:
            st.error("⚠️ Email not found. Please register first.")

# Run the forgot password page directly
if __name__ == "__main__":
    forgot_password_app()
