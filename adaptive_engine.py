# --- adaptive_engine.py ---
import os
from datetime import datetime
from pymongo import MongoClient
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- MongoDB Connection ---
def connect_db():
    """Connect to MongoDB and return the user_performance collection."""
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        st.error("❌ MONGO_URI not found in environment variables.")
        return None

    try:
        client = MongoClient(mongo_uri)
        db = client["smartquizzer_db"]
        return db["user_performance"]
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        return None

# --- Save User Performance ---
def save_performance(username, subject, topic, score, total, accuracy, level):
    """
    Store user performance after each quiz attempt.
    """
    collection = connect_db()
    if collection is None:
        st.warning("⚠️ No database connection — skipping save.")
        return

    record = {
        "username": username,
        "subject": subject,
        "topic": topic,
        "score": score,
        "total": total,
        "accuracy": accuracy,
        "level": level,
        "timestamp": datetime.now(),
    }

    try:
        collection.insert_one(record)
        # st.success("✅ Performance saved successfully!")
    except Exception as e:
        st.warning(f"⚠️ Could not save performance: {e}")

# --- Compute Next Difficulty ---
def get_next_difficulty(username, subject=None, topic=None):
    """
    Determine the next recommended difficulty.
    If subject and topic are provided, consider only that combination.
    Defaults to 'Medium' if no record exists.
    """
    collection = connect_db()
    if collection is None:
        return "Medium"

    query = {"username": username}
    if subject:
        query["subject"] = subject
    if topic:
        query["topic"] = topic

    # Get the last quiz record for this user + subject + topic
    last_record = collection.find_one(query, sort=[("timestamp", -1)])
    
    if not last_record:
        return "Medium"  # Default for first attempt

    accuracy = last_record.get("accuracy", 0)
    
    if accuracy >= 80:
        return "Hard"
    elif accuracy >= 50:
        return "Medium"
    else:
        return "Easy"

# --- Show Recommendation in Streamlit ---
def show_recommendation(username, subject=None, topic=None):
    """
    Display the suggested next difficulty in Streamlit and store in session_state.
    """
    next_diff = get_next_difficulty(username, subject, topic)
    
    st.markdown(
        f"""
        <div style="
            background-color:#E3F2FD;
            color:#0D47A1;
            padding:15px;
            border-radius:10px;
            border:2px solid #2196F3;
            text-align:center;
            font-size:18px;
            margin-top:20px;">
            💡 Based on your performance, your next quiz in 
            <b>{subject or 'this subject'}</b> - <b>{topic or 'this topic'}</b> 
            is recommended at <b>{next_diff}</b> difficulty.
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Store in Streamlit session for auto-preselection in quiz
    st.session_state.next_difficulty = next_diff
    return next_diff

# --- Get Difficulty for Current Quiz ---
def get_quiz_difficulty(username, subject, topic):
    """
    Returns the difficulty level that should be set when the user starts a quiz.
    - Uses recommended difficulty if user has previous attempts.
    - Defaults to Medium if no attempts exist.
    """
    return get_next_difficulty(username, subject, topic)
