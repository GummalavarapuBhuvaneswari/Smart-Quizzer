# quiz_module.py
import streamlit as st
import os
import ast
import time
import threading
from dotenv import load_dotenv
from groq import Groq
from streamlit_autorefresh import st_autorefresh
from adaptive_engine import save_performance, get_quiz_difficulty, show_recommendation

load_dotenv()

def save_performance_async(username, subject, topic, score, total, accuracy, level):
    """Save performance in background so UI doesn't wait."""
    thread = threading.Thread(
        target=save_performance,
        args=(username, subject, topic, score, total, accuracy, level),
        daemon=True
    )
    thread.start()


# --- Groq Client ---
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    st.error("❌ GROQ_API_KEY not found in environment variables.")
client_groq = Groq(api_key=groq_api_key)

# --- Initialize Session State ---
for key in ["quiz_active","quiz_finished","show_instructions",
            "generated_questions","selected_options",
            "current_question","time_limit","deadline",
            "quiz_type","num_questions","level"]:
    if key not in st.session_state:
        st.session_state[key] = False if "quiz" in key else None if key != "selected_options" else []

# --- Helper: Generate Questions ---
def generate_questions(prompt):
    
    try:
        response = client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a quiz generator. Return only Python list of dictionaries."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=800,
        )
        raw = response.choices[0].message.content
        questions= ast.literal_eval(raw)

         # Ensure every question has an explanation key
        for q in questions:
            if "explanation" not in q:
                q["explanation"] = "No explanation provided."
        return questions
    except Exception as e:
        st.error(f"⚠️ Error generating quiz: {e}")
        return []

# --- Instruction Page ---
def show_instructions():
    st.title("📝 Quiz Instructions")

    if "start_time" not in st.session_state or st.session_state.start_time is None:
        st.session_state.start_time = time.time()

    time_per_question = {"Easy":60, "Medium":90, "Hard":120}
    total_time = time_per_question[st.session_state.level] * st.session_state.num_questions
    st.session_state.time_limit = total_time

    st.markdown(
        f"""
        <div style="border:2px solid #FF9800; border-radius:10px; padding:20px; background-color:#FFF3E0;">
            <h3>📌 Please read before you start</h3>
            <ul>
                <li><b>Total Questions:</b> {st.session_state.num_questions}</li>
                <li><b>Difficulty:</b> {st.session_state.level}</li>
                <li><b>Total Time:</b> {total_time//60} minutes {total_time%60} seconds</li>
                <li><b>Marking Scheme:</b> +1 for correct, 0 for incorrect</li>
                <li><b>No negative marking</b></li>
                <li>Once the timer ends, the quiz will auto-submit ⏳</li>
            </ul>
        </div>
        """, unsafe_allow_html=True
    )

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 1])
    with col2:
        if st.button("🚀 Start Quiz", key="start_quiz_button"):
            st.session_state.quiz_active = True
            st.session_state.show_instructions = False
            st.session_state.deadline = st.session_state.start_time + st.session_state.time_limit
            st.rerun()

    st.markdown(
        """
        <style>
        div.stButton > button:first-child {
            background-color: #4CAF50;
            color: white;
            padding: 10px 25px;
            border-radius: 5px;
            font-size: 18px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# --- Display Quiz ---
def display_quiz(questions):
    if st.session_state.get("quiz_active", True) and not st.session_state.get("quiz_finished", False):
        st_autorefresh(interval=1000, key="quiz_timer_refresh")

    if "deadline" not in st.session_state or st.session_state.deadline is None:
        time_per_question = {"Easy": 60, "Medium": 90, "Hard": 120}
        total_time = time_per_question[st.session_state.level] * len(questions)
        st.session_state.deadline = time.time() + total_time
        st.session_state.time_limit = total_time

    remaining_time = int(st.session_state.deadline - time.time())

    if remaining_time <= 0:
        st.session_state.quiz_active = False
        st.session_state.quiz_finished = True
        st.success("⏰ Time's up! Quiz submitted automatically.")
        st.rerun()

    minutes, seconds = divmod(max(remaining_time, 0), 60)
    st.markdown(
        f"""
        <div style="
            background-color:#FFF3E0;
            border:2px solid #FF9800;
            border-radius:8px;
            padding:8px;
            font-size:18px;
            text-align:center;
            width:220px;
        ">
            ⏳ <b>Time Left:</b> {minutes:02d}:{seconds:02d}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.get("quiz_finished", False):
        st.write("✅ Quiz has been submitted.")
        return

    q = questions[st.session_state.current_question]
    st.subheader(f"Q{st.session_state.current_question + 1}. {q['question']}")

    st.session_state.selected_options[st.session_state.current_question] = st.radio(
        "Choose an option:",
        q["options"],
        index=None if st.session_state.selected_options[st.session_state.current_question] is None
        else q["options"].index(st.session_state.selected_options[st.session_state.current_question]),
        key=f"q{st.session_state.current_question}",
    )

    col1, col2, col3 = st.columns(3)
    if col1.button("⬅️ Previous", disabled=st.session_state.current_question == 0):
        st.session_state.current_question -= 1
        st.rerun()

    if col2.button("➡️ Next", disabled=st.session_state.current_question == len(questions) - 1):
        st.session_state.current_question += 1
        st.rerun()

    if col3.button("✅ Submit"):
        st.session_state.quiz_active = False
        st.session_state.quiz_finished = True
        st.success("✅ Quiz submitted successfully.")
        st.rerun()

# --- Show Results ---
def show_results(questions):
    correct = sum(
        1 for i, q in enumerate(questions)
        if st.session_state.selected_options[i] == q["answer"]
    )
    total = len(questions)
    accuracy = (correct / total) * 100 if total > 0 else 0

    username = st.session_state.get("username", "Guest")
    subject = st.session_state.get("subject", "")
    topic = st.session_state.get("topic", "")

    # --- Save performance only once ---
    if "performance_saved" not in st.session_state:
        st.session_state.performance_saved = False

    if not st.session_state.performance_saved:
        try:
            save_performance_async(
                username,
                subject,
                topic,
                correct,
                total,
                accuracy,
                st.session_state.level
            )
            st.session_state.performance_saved = True  # ✅ mark as saved
        except Exception as e:
            st.error(f"⚠️ Could not save performance: {e}")

    st.success("🎉 Quiz Completed!")
    st.markdown("### 📊 Accuracy Overview")
    st.progress(accuracy / 100)
    st.markdown(
        f"""
        <div style="
            background-color:#DFF2BF;
            color:#4F8A10;
            padding:20px;
            border-radius:10px;
            text-align:center;
            font-size:24px;
            font-weight:bold;
            border: 2px solid #4F8A10;
        ">
            ✅ Your Score: {correct} / {total} ({accuracy:.2f}%)
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Show recommended next difficulty ---
    try:
        show_recommendation(username, subject, topic)
    except Exception as e:
        st.warning(f"⚠️ Could not generate recommendation: {e}")

    # --- Review Result Button ---
    if "review_clicked" not in st.session_state:
        st.session_state.review_clicked = False

    st.markdown("<div style='margin-top:25px;'></div>", unsafe_allow_html=True)
    if not st.session_state.review_clicked:
        if st.button("📝 Review Result"):
            st.session_state.review_clicked = True
            st.rerun()

    # --- Review Answers ---
    if st.session_state.review_clicked:
        st.subheader("Review Your Answers")
        review_html = ""
        for i, q in enumerate(questions):
            user_ans = st.session_state.selected_options[i]
            correct_ans = q["answer"]
            explanation = q.get("explanation", "No explanation provided.")
            color = "green" if user_ans == correct_ans else "red"
            symbol = "✅" if user_ans == correct_ans else "❌"

            review_html += f"<b>Q{i+1}: {q['question']}</b><br>"
            review_html += f"Your Answer: <span style='color:{color}; font-weight:bold'>{user_ans} {symbol}</span><br>"
            if user_ans != correct_ans:
                review_html += f"Correct Answer: <span style='color:green; font-weight:bold'>{correct_ans} ✅</span><br>"
            review_html += f"💡 Explanation: {explanation}<br>"
            review_html += "<hr>"

        st.markdown(review_html, unsafe_allow_html=True)

    # --- Reset Quiz ---
    col_left, col_right = st.columns([3, 1])
    with col_right:
        if st.button("🔄 Reset Quiz"):
            for key in [
                "quiz_active", "quiz_finished", "show_instructions",
                "generated_questions", "selected_options",
                "current_question", "time_limit", "deadline",
                "start_time", "review_clicked", "level", "num_questions",
                "subject", "topic", "quiz_type", "performance_saved"
            ]:
                st.session_state[key] = None
            st.rerun()


# --- Quiz Modes ---
def paragraph_quiz():
    text = st.text_area("📖 Enter a paragraph:")
    num_qs = st.number_input("🔢 Number of Questions", min_value=1, max_value=20, value=3)

    if st.button("Generate Quiz"):
        username = st.session_state.get("username","Guest")

        # Use first 30 chars of paragraph as pseudo-topic
        pseudo_topic = text[:30]

        # Automatically get recommended difficulty
        recommended_level = get_quiz_difficulty(username, "Paragraph", pseudo_topic)

        # Generate prompt using recommended level
        prompt = f"Generate {num_qs} MCQs from the paragraph:\n{text}\nDifficulty: {recommended_level}.\nReturn Python list with dicts: question, options, answer,explanation (one-line explanation for the correct answer)."
        questions = generate_questions(prompt)
        if questions:
            st.session_state.generated_questions = questions
            st.session_state.quiz_type = "paragraph"
            st.session_state.quiz_active = False
            st.session_state.show_instructions = True
            st.session_state.current_question = 0
            st.session_state.selected_options = [None]*len(questions)
            st.session_state.time_limit = {"Easy":3,"Medium":5,"Hard":8}[recommended_level]*60
            st.session_state.level = recommended_level
            st.session_state.num_questions = len(questions)
            st.session_state.subject = "Paragraph"
            st.session_state.topic = pseudo_topic
            st.rerun()

def subject_topic_quiz():
    subject = st.text_input("📘 Enter Subject:")
    topic = st.text_input("📌 Enter Topic:")
    num_qs = st.number_input("🔢 Number of Questions", min_value=1, max_value=20, value=3)

    if st.button("Generate Quiz"):
        username = st.session_state.get("username","Guest")
        
        # Automatically get recommended difficulty
        recommended_level = get_quiz_difficulty(username, subject, topic)

        # Generate prompt using recommended level (no dropdown needed)
        prompt = f"Generate {num_qs} MCQs from {subject}, topic {topic}. Difficulty: {recommended_level}. Return Python list with dicts: question, options, answer,explanation (one-line explanation for the correct answer)."
        questions = generate_questions(prompt)
        if questions:
            st.session_state.generated_questions = questions
            st.session_state.quiz_type = "subject_topic"
            st.session_state.quiz_active = False
            st.session_state.show_instructions = True
            st.session_state.current_question = 0
            st.session_state.selected_options = [None]*len(questions)
            st.session_state.time_limit = {"Easy":3,"Medium":5,"Hard":8}[recommended_level]*60
            st.session_state.level = recommended_level
            st.session_state.num_questions = len(questions)
            st.session_state.subject = subject
            st.session_state.topic = topic
            st.rerun()


# --- Dashboard ---
def dashboard():
    if st.session_state.get("quiz_finished"):
        show_results(st.session_state.generated_questions)
        return
    if st.session_state.get("show_instructions"):
        show_instructions()
        return
    if st.session_state.get("quiz_active"):
        display_quiz(st.session_state.generated_questions)
        return

    st.title("🎯 SmartQuizzer")
    st.subheader("Welcome to the Quiz Dashboard")
    st.markdown("Select how you want to generate the quiz:")

    if "selected_mode" not in st.session_state:
        st.session_state.selected_mode = None
    mode = st.radio("Choose Mode", ["By Subject & Topic", "From Paragraph"], index=None)
    st.session_state.selected_mode = mode

    if st.button("➡️ Proceed"):
        st.session_state.mode_confirmed = True
        st.rerun()

    if st.session_state.get("mode_confirmed"):
        if st.session_state.selected_mode == "By Subject & Topic":
            subject_topic_quiz()
        elif st.session_state.selected_mode == "From Paragraph":
            paragraph_quiz()
