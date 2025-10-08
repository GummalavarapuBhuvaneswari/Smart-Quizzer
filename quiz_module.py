import streamlit as st
import os
import ast
import time
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# --- Groq Client ---
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    st.error("❌ GROQ_API_KEY not found in environment variables.")
client_groq = Groq(api_key=groq_api_key)

# --- Initialize Session State ---
for key in ["quiz_active","quiz_finished","show_instructions",
            "generated_questions","selected_options",
            "current_question","time_limit","deadline"]:
    if key not in st.session_state:
        st.session_state[key] = False if "quiz" in key else None if key != "selected_options" else []

# --- Helper: Generate Questions ---
def generate_questions(prompt):
    try:
        response = client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",  # updated model
            messages=[
                {"role": "system", "content": "You are a quiz generator. Return only Python list."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=800,
        )
        raw = response.choices[0].message.content
        return ast.literal_eval(raw)
    except Exception as e:
        st.error(f"⚠️ Error generating quiz: {e}")
        return []

# --- Instruction Page ---
def show_instructions():
    st.title("📝 Quiz Instructions")

    # Initialize start_time if it doesn't exist
    if "start_time" not in st.session_state or st.session_state.start_time is None:
        st.session_state.start_time = time.time()
    
    
    # Calculate dynamic time based on difficulty and number of questions
    time_per_question = {"Easy":60, "Medium":90, "Hard":120}  # seconds per question
    total_time = time_per_question[st.session_state.level] * st.session_state.num_questions
    st.session_state.time_limit = total_time  # ensure time_limit is consistent
    
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
    
    # Add spacing below instruction box
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    # Start Quiz button centered in columns
    col1, col2, col3 = st.columns([2, 2, 1])
    with col2:
        if st.button("🚀 Start Quiz", key="start_quiz_button"):
            st.session_state.quiz_active = True
            st.session_state.show_instructions = False
            st.session_state.deadline = st.session_state.start_time + st.session_state.time_limit
            st.rerun()

    # Style button with green color
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
    # Dynamic deadline
    if not st.session_state.deadline:
        # Example: Easy = 60 sec per question, Medium = 90 sec, Hard = 120 sec
        time_per_question = {"Easy":60, "Medium":90, "Hard":120}
        st.session_state.deadline = time.time() + time_per_question[st.session_state.level]*len(questions)
        st.session_state.time_limit = time_per_question[st.session_state.level]*len(questions)

    remaining_time = int(st.session_state.deadline - time.time())
    if remaining_time <= 0:
        st.session_state.quiz_active = False
        st.session_state.quiz_finished = True
        st.rerun()

    minutes, seconds = divmod(remaining_time, 60)
    st.info(f"⏳ Time Remaining: {minutes:02d}:{seconds:02d}")

    q = questions[st.session_state.current_question]
    st.subheader(f"Q{st.session_state.current_question+1}. {q['question']}")
    st.session_state.selected_options[st.session_state.current_question] = st.radio(
        "Choose an option:",
        q["options"],
        index=None if st.session_state.selected_options[st.session_state.current_question] is None
        else q["options"].index(st.session_state.selected_options[st.session_state.current_question]),
        key=f"q{st.session_state.current_question}"
    )

    col1, col2, col3 = st.columns(3)
    if col1.button("⬅️ Previous", disabled=st.session_state.current_question == 0):
        st.session_state.current_question -= 1
        st.rerun()
    if col2.button("➡️ Next", disabled=st.session_state.current_question == len(questions)-1):
        st.session_state.current_question += 1
        st.rerun()
    
    # Submit button only on the last question
    if st.session_state.current_question == len(questions)-1:
        if col3.button("✅ Submit"):
            st.session_state.quiz_active = False
            st.session_state.quiz_finished = True
            st.rerun()

# --- Show Results ---
def show_results(questions):
    correct = sum(1 for i,q in enumerate(questions) if st.session_state.selected_options[i] == q["answer"])
    total = len(questions)
    accuracy = (correct/total)*100 if total>0 else 0

    st.success("🎉 Quiz Completed!")
    st.markdown("### 📊 Accuracy Overview")
    st.progress(accuracy / 100)
    #st.write(f"✅ Score: {correct}/{total}")

     # Highlighted Score
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
        """, unsafe_allow_html=True
    )

    # Initialize review_clicked flag if not present
    if "review_clicked" not in st.session_state:
        st.session_state.review_clicked = False

    # Add space before Review button
    st.markdown("<div style='margin-top:25px;'></div>", unsafe_allow_html=True)

    # Review button
    if not st.session_state.review_clicked:  # Show only if not clicked yet
        if st.button("📝 Review Result"):
            st.session_state.review_clicked = True
            st.rerun()

    # Show review section only if button was clicked
    if st.session_state.review_clicked:
        st.subheader("Review Your Answers")
        for i, q in enumerate(questions):
            user_ans = st.session_state.selected_options[i]
            correct_ans = q["answer"]

            if user_ans == correct_ans:
                color = "green"
                symbol = "✅"
            else:
                color = "red"
                symbol = "❌"

            st.markdown(f"**Q{i+1}: {q['question']}**")
            st.markdown(
                f"Your Answer: <span style='color:{color}; font-weight:bold'>{user_ans} {symbol}</span>", 
                unsafe_allow_html=True
            )
            if user_ans != correct_ans:
                st.markdown(
                    f"Correct Answer: <span style='color:green; font-weight:bold'>{correct_ans} ✅</span>", 
                    unsafe_allow_html=True
                )
            st.markdown("---")

    # Buttons: Reset Quiz (left) & Logout (right)
    col_left, col_right = st.columns([3,1])
    with col_right:
        if st.button("🔄 Reset Quiz"):
            for key in ["quiz_active", "quiz_finished", "show_instructions",
                    "generated_questions", "selected_options",
                    "current_question", "time_limit", "deadline",
                    "start_time", "review_clicked"]:
                st.session_state[key] = None
            st.rerun()
    


# --- Quiz Modes ---
def paragraph_quiz():
    text = st.text_area("📖 Enter a paragraph:")
    num_qs = st.number_input("🔢 Number of Questions", min_value=1, max_value=20, value=3)
    level = st.selectbox("⚡ Difficulty Level", ["Easy","Medium","Hard"])
    if st.button("Generate Quiz"):
        prompt = f"Generate {num_qs} MCQs from the paragraph:\n{text}\nDifficulty: {level}.\nReturn Python list with dicts: question, options, answer."
        questions = generate_questions(prompt)
        if questions:
            st.session_state.generated_questions = questions
            st.session_state.quiz_type = "paragraph"
            st.session_state.quiz_active = False
            st.session_state.show_instructions = True
            st.session_state.current_question = 0
            st.session_state.selected_options = [None]*len(questions)
            st.session_state.time_limit = {"Easy":3,"Medium":5,"Hard":8}[level]*60
            st.session_state.level = level
            st.session_state.num_questions = len(questions)
            st.rerun()

def subject_topic_quiz():
    subject = st.text_input("📘 Enter Subject:")
    topic = st.text_input("📌 Enter Topic:")
    num_qs = st.number_input("🔢 Number of Questions", min_value=1, max_value=20, value=3)
    level = st.selectbox("⚡ Difficulty Level", ["Easy","Medium","Hard"])
    if st.button("Generate Quiz"):
        prompt = f"Generate {num_qs} MCQs from {subject}, topic {topic}. Difficulty: {level}. Return Python list with dicts: question, options, answer."
        questions = generate_questions(prompt)
        if questions:
            st.session_state.generated_questions = questions
            st.session_state.quiz_type = "subject_topic"
            st.session_state.quiz_active = False
            st.session_state.show_instructions = True
            st.session_state.current_question = 0
            st.session_state.selected_options = [None]*len(questions)
            st.session_state.time_limit = {"Easy":3,"Medium":5,"Hard":8}[level]*60
            st.session_state.level = level
            st.session_state.num_questions = len(questions)
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

    # Quiz mode selection
    if "selected_mode" not in st.session_state:
        st.session_state.selected_mode = None
    mode = st.radio(
        "Choose Mode",
        ["By Subject & Topic", "From Paragraph"],
        index=None  # ensures nothing is pre-selected
    )
    st.session_state.selected_mode = mode

    # Proceed button to confirm the choice
    if st.button("➡️ Proceed"):
        st.session_state.mode_confirmed = True
        st.rerun()

    # Show input fields only after proceed
    if st.session_state.get("mode_confirmed"):
        if st.session_state.selected_mode == "By Subject & Topic":
            subject_topic_quiz()
        elif st.session_state.selected_mode == "From Paragraph":
            paragraph_quiz()
