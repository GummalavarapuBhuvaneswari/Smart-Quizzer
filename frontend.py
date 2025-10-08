import streamlit as st
import time
from datetime import datetime
from backend import QuizBackend

class QuizFrontend:
    def __init__(self):
        self.backend = QuizBackend()
        self.setup_page()
        self.init_session_state()
    
    def setup_page(self):
        st.set_page_config(
            page_title="Smart Quizzer",
            page_icon="🧠",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Enhanced CSS with better button styling
        st.markdown("""
        <style>
            /* Main background */
            .stApp {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }

            /* Header */
            .main-title {
                font-size: 4rem;
                font-weight: bold;
                text-align: center;
                color: white;
                text-shadow: 3px 3px 6px rgba(0,0,0,0.5);
                margin-bottom: 1rem;
                padding: 40px 0 20px 0;
            }

            .sub-title {
                font-size: 1.5rem;
                text-align: center;
                color: white;
                font-weight: 500;
                margin-bottom: 3rem;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }

            /* Navigation container */
            .nav-container {
                position: fixed;
                top: 15px;
                right: 20px;
                z-index: 999999;
                background: rgba(255,255,255,0.95);
                backdrop-filter: blur(10px);
                padding: 10px 20px;
                border-radius: 25px;
                border: 2px solid rgba(255,255,255,0.5);
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            }

            /* NAVIGATION buttons - teal/green */
            div[data-testid="column"] button {
                background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%) !important;
                color: white !important;
                border: none !important;
                padding: 10px 20px !important;
                border-radius: 20px !important;
                font-weight: bold !important;
                font-size: 0.9rem !important;
                margin: 2px !important;
                min-width: 100px !important;
                transition: all 0.3s ease !important;
            }

            div[data-testid="column"] button:hover {
                background: linear-gradient(135deg, #0072ff 0%, #00c6ff 100%) !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 15px rgba(0,0,0,0.25) !important;
            }

            /* Main action buttons (Login/Register/Start/Submit) - opposite warm gradient */
            .stButton button {
                background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
                color: white;
                border: none;
                padding: 14px 28px;
                border-radius: 12px;
                font-weight: bold;
                width: 100%;
                font-size: 1.1rem;
                transition: all 0.3s ease;
            }

            .stButton button:hover {
                background: linear-gradient(135deg, #ffd200 0%, #f7971e 100%);
                color: #333;
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0,0,0,0.25);
            }

            /* Cards */
            .card {
                background: white;
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                margin: 1rem 0;
            }
            
            .feature-card {
                background: white;
                padding: 2rem;
                border-radius: 15px;
                text-align: center;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                height: 100%;
                transition: transform 0.3s ease;
            }
            
            .feature-card:hover {
                transform: translateY(-5px);
            }
            
            .feature-icon {
                font-size: 3rem;
                margin-bottom: 1rem;
                color: #667eea;
            }
            
            .feature-title {
                font-size: 1.3rem;
                font-weight: bold;
                color: #333;
                margin-bottom: 1rem;
            }
            
            .feature-desc {
                color: #666;
                line-height: 1.5;
            }
            
            .timer {
                font-size: 1.5rem;
                font-weight: bold;
                color: #ff6b6b;
                text-align: center;
                padding: 10px;
                background: rgba(255,255,255,0.9);
                border-radius: 10px;
                margin: 10px 0;
            }
            
            .instructions {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 15px;
                margin: 20px 0;
            }
            
            .question-card {
                background: white;
                padding: 25px;
                border-radius: 15px;
                margin: 15px 0;
                border-left: 5px solid #667eea;
            }
        </style>
        """, unsafe_allow_html=True)
    
    def init_session_state(self):
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'page' not in st.session_state:
            st.session_state.page = 'home'
        if 'quiz_started' not in st.session_state:
            st.session_state.quiz_started = False
        if 'quiz_questions' not in st.session_state:
            st.session_state.quiz_questions = []
        if 'current_question' not in st.session_state:
            st.session_state.current_question = 0
        if 'user_answers' not in st.session_state:
            st.session_state.user_answers = []
        if 'quiz_start_time' not in st.session_state:
            st.session_state.quiz_start_time = None
        if 'session_id' not in st.session_state:
            st.session_state.session_id = None
    
    def create_navigation(self):
        st.markdown("""
        <div class="nav-container">
            <div class="nav-btn-container">
        """, unsafe_allow_html=True)
        
        next_page = st.session_state.page
        
        if st.session_state.user is None:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("🏠 Home", key="nav_home_top", use_container_width=True):
                    next_page = 'home'
            with col2:
                if st.button("🔐 Login", key="nav_login_top", use_container_width=True):
                    next_page = 'login'
            with col3:
                if st.button("📝 Register", key="nav_register_top", use_container_width=True):
                    next_page = 'register'
        else:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("🏠 Home", key="nav_home_auth_top", use_container_width=True):
                    next_page = 'home'
            with col2:
                if st.button("📊 Dashboard", key="nav_dashboard_top", use_container_width=True):
                    next_page = 'dashboard'
            with col3:
                if st.button("🚪 Logout", key="nav_logout_top", use_container_width=True):
                    st.session_state.user = None
                    next_page = 'home'
        
        st.markdown("""
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if next_page != st.session_state.page:
            st.session_state.page = next_page
            st.rerun()
    
    def show_home_page(self):
        st.markdown("""
        <div style='text-align: center; color: white; font-size: 1.3rem; margin: 2rem 0;'>
            Transform your learning experience with AI-powered adaptive quizzes that adjust to your skill level.
        </div>
        """, unsafe_allow_html=True)

        # Features
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🤖</div>
                <div class="feature-title">AI Powered</div>
                <div class="feature-desc">Intelligent question generation using advanced algorithms</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🎯</div>
                <div class="feature-title">Adaptive Learning</div>
                <div class="feature-desc">Difficulty adjusts based on your performance</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Progress Tracking</div>
                <div class="feature-desc">Monitor your learning journey with analytics</div>
            </div>
            """, unsafe_allow_html=True)

        # CTA
        st.markdown("""
        <div style='text-align: center; color: white; font-size: 1.2rem; margin: 3rem 0;'>
            Ready to start your learning journey?
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Get Started For Free", use_container_width=True, key="get_started_home"):
                if st.session_state.user:
                    st.session_state.page = 'dashboard'
                else:
                    st.session_state.page = 'register'
                st.rerun()
    
    def show_login_page(self):
        st.markdown("""
        <div style='text-align: center; color: white; font-size: 1.5rem; margin: 2rem 0;'>
            Welcome Back!
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=True):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                
                username = st.text_input("👤 Username", placeholder="Enter your username", key="login_username")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter your password", key="login_password")
                
                submit = st.form_submit_button("🚀 Sign In", use_container_width=True)
                if submit:
                    if username and password:
                        user = self.backend.db.verify_user(username, password)
                        if user:
                            st.session_state.user = {
                                'id': user[0],
                                'username': user[1],
                                'full_name': user[2]
                            }
                            st.session_state.page = 'dashboard'
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    else:
                        st.error("Please fill all fields")
                
                st.markdown("""
                <div style='text-align: center; margin-top: 20px;'>
                    <p>Don't have an account? <strong>Click Register button above</strong></p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    def show_register_page(self):
        st.markdown("""
        <div style='text-align: center; color: white; font-size: 1.5rem; margin: 2rem 0;'>
            Create Your Account
        </div>
        """, unsafe_allow_html=True)

        with st.form("register_form", clear_on_submit=True):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                
                full_name = st.text_input("👤 Full Name", placeholder="Enter your full name", key="reg_fullname")
                email = st.text_input("📧 Email", placeholder="Enter your email", key="reg_email")
                username = st.text_input("👤 Username", placeholder="Choose a username", key="reg_username")
                password = st.text_input("🔒 Password", type="password", placeholder="Create a password", key="reg_password")
                confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm your password", key="reg_confirm")
                
                submit = st.form_submit_button("🚀 Create Account", use_container_width=True)
                if submit:
                    if all([full_name, username, password, confirm_password]):
                        if password == confirm_password:
                            if self.backend.db.add_user(username, password, email, full_name):
                                st.success("Account created successfully! Please login.")
                                st.session_state.page = 'login'
                                st.rerun()
                            else:
                                st.error("Username already exists")
                        else:
                            st.error("Passwords do not match")
                    else:
                        st.error("Please fill all fields")
                
                st.markdown("""
                <div style='text-align: center; margin-top: 20px;'>
                    <p>Already have an account? <strong>Click Login button above</strong></p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    def show_dashboard(self):
        if not st.session_state.user:
            st.session_state.page = 'login'
            st.rerun()
            return

        user_stats, avg_score = self.backend.db.get_user_stats(st.session_state.user['id'])
        
        st.markdown(f"""
        <div style='text-align: center; color: white; font-size: 1.5rem; margin: 2rem 0;'>
            Welcome, {st.session_state.user['full_name'] or st.session_state.user['username']}!
        </div>
        """, unsafe_allow_html=True)

        # Stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="card">
                <h3>📊 Total Quizzes</h3>
                <p style='font-size: 2rem; color: #3B82F6;'>{user_stats}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="card">
                <h3>⭐ Average Score</h3>
                <p style='font-size: 2rem; color: #3B82F6;'>{avg_score}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="card">
                <h3>🎯 Ready to Learn?</h3>
                <p>Start a new quiz session</p>
            </div>
            """, unsafe_allow_html=True)

        # Quiz start
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 🚀 Start New Quiz")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            topic = st.selectbox("Subject", ["Computer Science", "Mathematics", "Science", "History", "Geography"], key="topic_select")
        with col2:
            if topic == "Computer Science":
                subtopic = st.selectbox("Sub-topic", ["Python", "Java", "C++", "JavaScript", "Data Structures"], key="cs_subtopic")
            elif topic == "Mathematics":
                subtopic = st.selectbox("Sub-topic", ["Algebra", "Calculus", "Geometry", "Statistics"], key="math_subtopic")
            else:
                subtopic = st.selectbox("Sub-topic", ["Fundamentals", "Advanced Concepts"], key="other_subtopic")
        with col3:
            level = st.selectbox("Skill Level", ["Beginner", "Intermediate", "Advanced"], key="level_select")
        
        # Instructions
        st.markdown("""
        <div class="instructions">
            <h4>📝 Quiz Instructions:</h4>
            <ul>
                <li>You will have <strong>10 minutes</strong> to complete the quiz</li>
                <li>Total questions: <strong>10</strong></li>
                <li>Each question carries equal marks</li>
                <li>No negative marking for wrong answers</li>
                <li>Timer will start once you begin the quiz</li>
                <li>You cannot pause or restart the quiz once started</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🎯 Start Quiz", use_container_width=True, key="start_quiz_btn"):
            # Initialize quiz session
            st.session_state.quiz_started = True
            st.session_state.quiz_questions = self.backend.get_questions(topic, subtopic, level, 10)
            st.session_state.current_question = 0
            st.session_state.user_answers = [None] * len(st.session_state.quiz_questions)
            st.session_state.quiz_start_time = datetime.now()
            st.session_state.session_id = self.backend.db.record_session(
                st.session_state.user['id'], 
                topic, 
                subtopic, 
                level
            )
            st.session_state.page = 'quiz'
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def show_quiz_page(self):
        if not st.session_state.user or not st.session_state.quiz_started:
            st.session_state.page = 'dashboard'
            st.rerun()
            return

        # Timer calculation
        elapsed_time = datetime.now() - st.session_state.quiz_start_time
        remaining_time = max(600 - elapsed_time.total_seconds(), 0)  # 10 minutes = 600 seconds
        
        if remaining_time <= 0:
            # Time's up - auto submit
            st.session_state.page = 'results'
            st.rerun()
            return
        
        # Display timer
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        st.markdown(f"""
        <div class="timer">
            ⏰ Time Remaining: {minutes:02d}:{seconds:02d}
        </div>
        """, unsafe_allow_html=True)

        # Current question
        question_data = st.session_state.quiz_questions[st.session_state.current_question]
        
        st.markdown(f"""
        <div class="question-card">
            <h3>Question {st.session_state.current_question + 1} of {len(st.session_state.quiz_questions)}</h3>
            <p style='font-size: 1.2rem;'>{question_data['question']}</p>
        </div>
        """, unsafe_allow_html=True)

        # Answer options
        selected_option = st.radio(
            "Select your answer:",
            question_data['options'],
            key=f"q_{st.session_state.current_question}"
        )
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.session_state.current_question > 0:
                if st.button("⬅️ Previous", use_container_width=True, key=f"prev_{st.session_state.current_question}"):
                    st.session_state.user_answers[st.session_state.current_question] = selected_option
                    st.session_state.current_question -= 1
                    st.rerun()
        
        with col2:
            st.markdown(f"<div style='text-align: center;'>Question {st.session_state.current_question + 1} of {len(st.session_state.quiz_questions)}</div>", unsafe_allow_html=True)
        
        with col3:
            if st.session_state.current_question < len(st.session_state.quiz_questions) - 1:
                if st.button("Next ➡️", use_container_width=True, key=f"next_{st.session_state.current_question}"):
                    st.session_state.user_answers[st.session_state.current_question] = selected_option
                    st.session_state.current_question += 1
                    st.rerun()
            else:
                if st.button("✅ Submit Quiz", use_container_width=True, key="submit_quiz", type="primary"):
                    st.session_state.user_answers[st.session_state.current_question] = selected_option
                    st.session_state.page = 'results'
                    st.rerun()
    
    def show_results_page(self):
        if not st.session_state.user:
            st.session_state.page = 'login'
            st.rerun()
            return

        # Calculate results
        results_data = self.backend.calculate_results(
            st.session_state.quiz_questions, 
            st.session_state.user_answers
        )
        
        time_taken = (datetime.now() - st.session_state.quiz_start_time).total_seconds()

        # Save individual results to database
        for result in results_data['results']:
            self.backend.db.save_quiz_result(
                st.session_state.user['id'],
                st.session_state.session_id,
                result['question'],
                result['user_answer'],
                result['correct_answer'],
                result['is_correct']
            )

        # Update session with final results
        self.backend.db.update_session_results(
            st.session_state.session_id,
            results_data['score'],
            results_data['total_questions'],
            time_taken
        )

        # 🎉 Show confetti if all answers correct
        if results_data['score'] == results_data['total_questions']:
            st.markdown("""
            <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
            <script>
            function launchConfetti() {
                var duration = 5 * 1000;
                var end = Date.now() + duration;
                (function frame() {
                    confetti({ particleCount: 7, angle: 60, spread: 70, origin: { x: 0 } });
                    confetti({ particleCount: 7, angle: 120, spread: 70, origin: { x: 1 } });
                    if (Date.now() < end) requestAnimationFrame(frame);
                }());
            }
            launchConfetti();
            </script>
            """, unsafe_allow_html=True)

        # Performance message
        performance_msg, performance_color = self.backend.get_performance_message(results_data['percentage'])
        
        st.markdown(f"""
        <div style='text-align: center; background: {performance_color}; color: white; padding: 20px; border-radius: 15px; margin: 20px 0;'>
            <h3>{performance_msg}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Review answers
        st.markdown("### 📝 Review Your Answers")
        for i, result in enumerate(results_data['results']):
            status_icon = "✅" if result['is_correct'] else "❌"
            status_color = "#22c55e" if result['is_correct'] else "#ef4444"
            
            st.markdown(f"""
            <div class="question-card" style='border-left: 5px solid {status_color};'>
                <h4>Q{i+1}: {result['question']} {status_icon}</h4>
                <p><strong>Your answer:</strong> {result['user_answer']}</p>
                <p><strong>Correct answer:</strong> {result['correct_answer']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🏠 Back to Dashboard", use_container_width=True, key="back_to_dashboard"):
                # Reset quiz state
                st.session_state.quiz_started = False
                st.session_state.quiz_questions = []
                st.session_state.current_question = 0
                st.session_state.user_answers = []
                st.session_state.quiz_start_time = None
                st.session_state.session_id = None
                
                st.session_state.page = 'dashboard'
                st.rerun()
    
    def run(self):
        # Main header - ALWAYS VISIBLE
        st.markdown('<div class="main-title">🧠 Smart Quizzer</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-title">AI-Powered Adaptive Learning Platform</div>', unsafe_allow_html=True)

        # CREATE NAVIGATION BUTTONS AFTER THE HEADER
        self.create_navigation()

        # Page routing - FAST AND SIMPLE
        if st.session_state.page == 'home':
            self.show_home_page()
        elif st.session_state.page == 'login':
            self.show_login_page()
        elif st.session_state.page == 'register':
            self.show_register_page()
        elif st.session_state.page == 'dashboard':
            self.show_dashboard()
        elif st.session_state.page == 'quiz':
            self.show_quiz_page()
        elif st.session_state.page == 'results':
            self.show_results_page()

if __name__ == "__main__":
    app = QuizFrontend()
    app.run()