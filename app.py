import os
import json
import sqlite3
from datetime import datetime
from urllib.parse import urlparse

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# NOTE: models.py uses Flask-SQLAlchemy, but app.py uses raw sqlite3. 
# We are sticking to the raw sqlite3 implementation in app.py for consistency.
from simple_adaptive_engine import SimpleAdaptiveEngine
from gemini_engine import GeminiQuizEngine

# --- Configuration & Initialization ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart-quizzer-final-key-45678'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

adaptive_engine = SimpleAdaptiveEngine()
quiz_engine = GeminiQuizEngine()

# --- Utility Functions ---

def is_url(content):
    """Checks if a string is a valid URL."""
    try:
        result = urlparse(content)
        # Check for scheme (http/https) and network location (domain)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except ValueError:
        return False
        
def extract_text_from_file(filepath):
    """Placeholder for file content extraction. Simulates PDF/PPTX parsing."""
    filename = os.path.basename(filepath)
    ext = filename.split('.')[-1].lower()
    
    # Placeholder Logic
    if ext == 'pdf':
        return f"Content from PDF about {filename}: Machine Learning models are categorized into Supervised, Unsupervised, and Reinforcement Learning. Supervised learning requires labeled data, which includes input features and corresponding output labels. The concept of backpropagation is central to training neural networks, updating weights based on the loss function's gradient."
    elif ext in ['pptx', 'ppt']:
        return f"Presentation Summary: The project architecture includes an NLP processor and an Adaptive Engine. User engagement is tracked by response time and accuracy. The difficulty index increases by 1 on correct answers and decreases by 1 on incorrect answers. The adaptive quiz stops after 10 questions."
    elif ext == 'txt': 
        with open(filepath, 'r') as f:
            return f.read()
    elif is_url(filepath):
         # In a real app, you would fetch the content from the URL
        return f"Content from URL {filepath}: The first principle of a learning system is the acquisition of knowledge. The second is the application of that knowledge to novel situations."
    return ""

def get_db_connection(dict_cursor=True):
    conn = sqlite3.connect('quizzes.db')
    if dict_cursor:
        conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection(dict_cursor=False)
    c = conn.cursor()
    
    # NOTE: The tables below are based on the Raw SQLite implementation found in the user's initial app.py
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            security_q TEXT,
            security_a TEXT,
            skill_level TEXT DEFAULT 'Medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            topic TEXT NOT NULL,
            content TEXT NOT NULL,
            questions TEXT NOT NULL, -- JSON string of all pool questions (adaptive) or all quiz questions (simple)
            difficulty TEXT DEFAULT 'Medium',
            quiz_type TEXT DEFAULT 'adaptive', -- New column for quiz type
            score REAL DEFAULT 0,
            status TEXT DEFAULT 'in_progress',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        CREATE TABLE IF NOT EXISTS performances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            accuracy REAL DEFAULT 0.0,
            total_questions INTEGER DEFAULT 0,
            correct_answers INTEGER DEFAULT 0,
            average_response_time REAL DEFAULT 0.0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS question_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            question_id TEXT,
            user_id INTEGER,
            feedback_type TEXT,
            comment TEXT,
            flagged INTEGER DEFAULT 0,
            resolved INTEGER DEFAULT 0,
            question_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    ''')
    
    def add_column_if_not_exists(table, column, definition):
        try:
            c.execute(f"SELECT {column} FROM {table} LIMIT 1")
        except sqlite3.OperationalError:
            c.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')

    # Ensure all necessary columns exist
    add_column_if_not_exists('users', 'security_q', 'TEXT')
    add_column_if_not_exists('users', 'security_a', 'TEXT')
    add_column_if_not_exists('users', 'skill_level', 'TEXT DEFAULT "Medium"')
    add_column_if_not_exists('quizzes', 'difficulty', 'TEXT DEFAULT "Medium"')
    add_column_if_not_exists('quizzes', 'quiz_type', 'TEXT DEFAULT "adaptive"') # Ensure this is added
    
    conn.commit()

    # Ensure there is at least one admin account available for dashboard access
    default_admin_username = 'admin'
    default_admin_password = 'Admin@123'

    existing_admin = c.execute('SELECT id FROM admins WHERE username = ?', (default_admin_username,)).fetchone()
    if not existing_admin:
        c.execute(
            'INSERT INTO admins (username, password) VALUES (?, ?)',
            (default_admin_username, generate_password_hash(default_admin_password))
        )
        conn.commit()

    conn.close()

init_db()

def is_logged_in():
    return 'user_id' in session


def is_admin_logged_in():
    return session.get('is_admin')

def get_current_user_data(user_id):
    with get_db_connection() as conn:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return user

def get_user_skill_level(user_id):
    user_data = get_current_user_data(user_id)
    return user_data['skill_level'] if user_data else 'Medium'

# --- ROUTES ---

@app.route('/')
def index():
    if is_logged_in():
        return redirect('/dashboard')
    return render_template('index.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        with get_db_connection() as conn:
            admin = conn.execute('SELECT * FROM admins WHERE username = ?', (username,)).fetchone()

        if admin and check_password_hash(admin['password'], password):
            session.clear()  # ensure any user session data is cleared before promoting admin access
            session['is_admin'] = True
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            flash('Admin login successful.', 'success')
            return redirect(url_for('admin_dashboard'))

        flash('Invalid admin credentials.', 'danger')

    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Admin logged out successfully.', 'info')
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    with get_db_connection() as conn:
        total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        active_users = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM quizzes WHERE created_at >= datetime('now', '-30 day')"
        ).fetchone()[0]
        total_quizzes = conn.execute('SELECT COUNT(*) FROM quizzes').fetchone()[0]
        completed_quizzes = conn.execute(
            "SELECT COUNT(*) FROM quizzes WHERE status = 'completed'"
        ).fetchone()[0]
        total_feedback = conn.execute('SELECT COUNT(*) FROM question_feedback').fetchone()[0]
        flagged_open = conn.execute(
            'SELECT COUNT(*) FROM question_feedback WHERE flagged = 1 AND resolved = 0'
        ).fetchone()[0]

        feedback_breakdown = conn.execute(
            'SELECT feedback_type, COUNT(*) as count FROM question_feedback GROUP BY feedback_type'
        ).fetchall()

        user_rows = conn.execute(
            'SELECT id, username, email, skill_level, created_at FROM users ORDER BY created_at DESC'
        ).fetchall()

        content_rows = conn.execute(
            'SELECT id, title, topic, status, created_at FROM quizzes ORDER BY created_at DESC LIMIT 12'
        ).fetchall()

        flagged_rows = conn.execute(
            '''
            SELECT qf.*, u.username AS reported_by, q.title AS quiz_title
            FROM question_feedback qf
            LEFT JOIN users u ON qf.user_id = u.id
            LEFT JOIN quizzes q ON qf.quiz_id = q.id
            WHERE qf.flagged = 1 AND qf.resolved = 0
            ORDER BY qf.created_at DESC
            '''
        ).fetchall()

        recent_feedback_rows = conn.execute(
            '''
            SELECT qf.*, u.username AS reported_by, q.title AS quiz_title
            FROM question_feedback qf
            LEFT JOIN users u ON qf.user_id = u.id
            LEFT JOIN quizzes q ON qf.quiz_id = q.id
            ORDER BY qf.created_at DESC
            LIMIT 15
            '''
        ).fetchall()

        leaderboard_rows = conn.execute(
            '''
            SELECT u.id,
                   u.username,
                   COUNT(q.id) AS completed_quizzes,
                   AVG(q.score) AS avg_score,
                   MAX(q.score) AS best_score
            FROM users u
            JOIN quizzes q ON q.user_id = u.id AND q.status = 'completed'
            GROUP BY u.id
            ORDER BY avg_score DESC, completed_quizzes DESC, best_score DESC
            LIMIT 10
            '''
        ).fetchall()

    feedback_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    for row in feedback_breakdown:
        f_type = (row['feedback_type'] or '').lower()
        if f_type in feedback_counts:
            feedback_counts[f_type] += row['count']

    sentiment_total = feedback_counts['positive'] + feedback_counts['negative']
    positive_pct = (feedback_counts['positive'] / sentiment_total * 100) if sentiment_total else 0
    negative_pct = (feedback_counts['negative'] / sentiment_total * 100) if sentiment_total else 0

    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'total_quizzes': total_quizzes,
        'completed_quizzes': completed_quizzes,
        'total_feedback': total_feedback,
        'flagged_open': flagged_open,
        'positive_pct': round(positive_pct, 1),
        'negative_pct': round(negative_pct, 1),
        'neutral_count': feedback_counts['neutral']
    }

    users = [dict(row) for row in user_rows]
    content_items = [dict(row) for row in content_rows]
    flagged_items = [dict(row) for row in flagged_rows]
    recent_feedback = [dict(row) for row in recent_feedback_rows]
    leaderboard = [
        {
            'user_id': row['id'],
            'username': row['username'],
            'completed_quizzes': row['completed_quizzes'],
            'avg_score': round(row['avg_score'], 1) if row['avg_score'] is not None else 0,
            'best_score': round(row['best_score'], 1) if row['best_score'] is not None else 0,
        }
        for row in leaderboard_rows
    ]

    return render_template(
        'admin_dashboard.html',
        stats=stats,
        users=users,
        content_items=content_items,
        flagged_items=flagged_items,
        recent_feedback=recent_feedback,
        feedback_counts=feedback_counts,
        leaderboard=leaderboard
    )


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
def admin_delete_user(user_id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    with get_db_connection(dict_cursor=False) as conn:
        conn.execute('DELETE FROM question_feedback WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM performances WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM quizzes WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()

    flash('User removed successfully.', 'info')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/feedback/<int:feedback_id>/resolve', methods=['POST'])
def admin_resolve_feedback(feedback_id):
    if not is_admin_logged_in():
        return redirect(url_for('admin_login'))

    with get_db_connection(dict_cursor=False) as conn:
        conn.execute('UPDATE question_feedback SET resolved = 1 WHERE id = ?', (feedback_id,))
        conn.commit()

    flash('Feedback marked as resolved.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        security_q = request.form['security_q']
        security_a = request.form['security_a'].lower().strip()

        with get_db_connection() as conn:
            existing_user = conn.execute('SELECT id FROM users WHERE username = ? OR email = ?', 
                                       (username, email)).fetchone()
            
            if existing_user:
                flash('Username or email already exists', 'danger')
                return render_template('register.html')
            
            hashed_password = generate_password_hash(password)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, password, security_q, security_a) 
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, hashed_password, security_q, security_a))
            
            user_id = cursor.lastrowid
            conn.commit()
        
        # --- IMPORTANT: Populate Session with ALL required profile data ---
        session.clear()  # reset any prior session state (including admin logins) before signing in new user
        session['user_id'] = user_id
        session['username'] = username
        session['email'] = email
        session['join_date'] = datetime.now().strftime('%Y-%m-%d') # Use string for consistency
        session['skill_level'] = 'Medium' # Default
        
        # Calculate and store dynamic stats
        with get_db_connection() as conn:
            total_quizzes = conn.execute('SELECT COUNT(*) FROM quizzes WHERE user_id = ?', (user_id,)).fetchone()[0]
            avg_score_result = conn.execute('SELECT AVG(score) FROM quizzes WHERE user_id = ? AND status = ?', 
                                          (user_id, 'completed')).fetchone()[0]
        session['quizzes_taken'] = total_quizzes
        session['avg_score'] = round(avg_score_result, 1) if avg_score_result else 0
        
        flash('Registration successful!', 'success')
        return redirect('/dashboard')
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and check_password_hash(user['password'], password):
            # --- IMPORTANT: Populate Session with ALL required profile data ---
            session.clear()  # drop any previous admin or user state to avoid dual logins
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            session['skill_level'] = user['skill_level']
            session['join_date'] = user['created_at'][:10] # Assuming format like 'YYYY-MM-DD HH:MM:SS'
            
            # Calculate and store dynamic stats
            user_id = user['id']
            with get_db_connection() as conn:
                total_quizzes = conn.execute('SELECT COUNT(*) FROM quizzes WHERE user_id = ?', (user_id,)).fetchone()[0]
                avg_score_result = conn.execute('SELECT AVG(score) FROM quizzes WHERE user_id = ? AND status = ?', 
                                              (user_id, 'completed')).fetchone()[0]
            
            session['quizzes_taken'] = total_quizzes
            session['avg_score'] = round(avg_score_result, 1) if avg_score_result else 0
            
            flash('Login successful!', 'success')
            return redirect('/dashboard')
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        stage = request.form.get('stage')
        username = request.form.get('username')
        
        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            if not user:
                flash('Username not found.', 'danger')
                # If stage is provided, render that stage again with error
                if stage in ['verify_q', 'reset_p']:
                    return render_template('forgot_password.html', stage=stage)
                return render_template('forgot_password.html', stage='ask_username')

            if stage == 'verify_q':
                security_a = request.form.get('security_a', '').lower().strip()
                
                # Use a dummy user object for templating if recovery is ongoing
                user_dict = dict(user)
                
                if security_a == user_dict['security_a'].lower().strip():
                    flash('Security question answered successfully. Reset your password now.', 'success')
                    return render_template('forgot_password.html', user=user_dict, stage='reset_p')
                else:
                    flash('Incorrect security answer.', 'danger')
                    return render_template('forgot_password.html', user=user_dict, stage='verify_q')

            elif stage == 'reset_p':
                new_password = request.form.get('new_password')
                confirm_password = request.form.get('confirm_password')

                if new_password != confirm_password:
                    flash('Passwords do not match.', 'danger')
                    user_dict = dict(user)
                    return render_template('forgot_password.html', user=user_dict, stage='reset_p')
                
                hashed_password = generate_password_hash(new_password)
                conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user['id']))
                conn.commit()
                
                flash('Password successfully reset! Please login.', 'success')
                return redirect(url_for('login'))
        
        # This part handles the initial request with only username
        if username:
            user_dict = dict(user)
            return render_template('forgot_password.html', user=user_dict, stage='verify_q')
        
        # Default fallback
        return render_template('forgot_password.html', stage='ask_username')
        
    return render_template('forgot_password.html', stage='ask_username')


@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        return redirect('/login')
    
    user_id = session['user_id']
    with get_db_connection() as conn:
        total_quizzes = conn.execute('SELECT COUNT(*) FROM quizzes WHERE user_id = ?', (user_id,)).fetchone()[0]
        completed_quizzes = conn.execute('SELECT COUNT(*) FROM quizzes WHERE user_id = ? AND status = ?', 
                                   (user_id, 'completed')).fetchone()[0]
        recent_quizzes = conn.execute('SELECT * FROM quizzes WHERE user_id = ? ORDER BY created_at DESC LIMIT 5', 
                                    (user_id,)).fetchall()
    
    # Convert sqlite3.Row objects to dicts for easier use in Jinja
    recent_quizzes_list = [dict(q) for q in recent_quizzes]

    return render_template('dashboard.html',
                         username=session['username'],
                         total_quizzes=total_quizzes,
                         completed_quizzes=completed_quizzes,
                         recent_quizzes=recent_quizzes_list)

@app.route('/profile')
def profile():
    if not is_logged_in():
        return redirect('/login')

    user = get_current_user_data(session['user_id'])
    
    # 1. Prepare user data for display (handling date format for Jinja)
    user_data_display = dict(user)
    if user_data_display and user_data_display['created_at'] and isinstance(user_data_display['created_at'], str):
        try:
            # Convert SQLite string to Python datetime object for strftime in template
            # Assumes 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD HH:MM:SS.SSS' format
            user_data_display['created_at'] = datetime.strptime(user_data_display['created_at'].split('.')[0], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass # Keep as string if parsing fails
    
    # 2. Fetch Aggregated Performance Analytics
    with get_db_connection() as conn:
        quizzes = conn.execute('SELECT id, topic, score, questions FROM quizzes WHERE user_id = ? AND status = ?', 
                               (user['id'], 'completed')).fetchall()

    topic_summary = {}
    total_completed = 0
    total_average_score = 0
    
    for q in quizzes:
        total_completed += 1
        total_average_score += q['score']
        
        topic = q['topic']
        try:
            questions = json.loads(q['questions'])
        except json.JSONDecodeError:
            continue # Skip if questions data is corrupted
        
        # Filter for actually answered questions within this quiz for more accurate stats
        answered_questions_in_quiz = [qn for qn in questions if 'user_answer' in qn]
        
        total_time_in_quiz = sum(qn.get('response_time', 0) for qn in answered_questions_in_quiz)
        total_q_in_quiz = len(answered_questions_in_quiz)
        correct_q_in_quiz = sum(1 for qn in answered_questions_in_quiz if qn.get('is_correct', False))
        
        if topic not in topic_summary:
            topic_summary[topic] = {
                'total_score': 0, 
                'quiz_count': 0,
                'total_response_time': 0,
                'total_questions': 0,
                'total_correct_answers': 0 
            }
        
        summary = topic_summary[topic]
        summary['total_score'] += q['score']
        summary['quiz_count'] += 1
        summary['total_response_time'] += total_time_in_quiz
        summary['total_questions'] += total_q_in_quiz
        summary['total_correct_answers'] += correct_q_in_quiz


    performances_list = []
    for topic, summary in topic_summary.items():
        # Ensure division by zero is handled for average calculations
        avg_score = summary['total_score'] / summary['quiz_count'] if summary['quiz_count'] > 0 else 0
        avg_accuracy = (summary['total_correct_answers'] / summary['total_questions']) * 100 if summary['total_questions'] > 0 else 0
        avg_time = summary['total_response_time'] / summary['total_questions'] if summary['total_questions'] > 0 else 0
        
        performances_list.append({
            'topic': topic,
            'difficulty': user['skill_level'], # Use user's overall skill for this
            'accuracy': avg_accuracy,      
            'total_questions': summary['total_questions'],
            'correct_answers': summary['total_correct_answers'], 
            'average_response_time': avg_time
        })
    
    overall_avg_score = total_average_score / total_completed if total_completed > 0 else 0
    
    # 3. Render Profile Template
    return render_template('profile.html', 
                           user=user_data_display,
                           total_quizzes=total_completed, # This is actually total completed quizzes
                           completed_quizzes=total_completed,
                           average_score=overall_avg_score,
                           performances=performances_list)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if not is_logged_in():
        return redirect('/login')
    
    user_id = session['user_id']
    username_new = request.form.get('username', '').strip()
    skill_level_new = request.form.get('skill_level', 'Medium')
    
    with get_db_connection() as conn:
        # Check if new username is taken by another user
        existing_user = conn.execute('SELECT id FROM users WHERE username = ? AND id != ?', 
                                   (username_new, user_id)).fetchone()
        
        if existing_user:
            flash('Username is already taken.', 'danger')
            return redirect('/profile')
            
        # Update user profile
        conn.execute('''
            UPDATE users 
            SET username = ?, 
                skill_level = ?
            WHERE id = ?
        ''', (username_new, skill_level_new, user_id))
        
        conn.commit()
        
        # Update session variables
        session['username'] = username_new
        session['skill_level'] = skill_level_new
    
    flash('Profile updated successfully!', 'success')
    return redirect('/profile')


# =========================================================================
# === QUIZ CREATION AND SUBMISSION ROUTES
# =========================================================================

@app.route('/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    if not is_logged_in():
        return redirect('/login')

    user_id = session['user_id']
    current_difficulty = get_user_skill_level(user_id)
    
    if request.method == 'POST':
        topic = request.form.get('topic', 'General').strip()
        user_difficulty = request.form.get('difficulty', current_difficulty).capitalize()
        num_questions = int(request.form.get('num_questions', 5))
        quiz_type = request.form.get('quiz_type', 'adaptive') # Default to adaptive
        
        content_text = request.form.get('content_text', '').strip()
        content_file = request.files.get('content_file')
        
        final_content = content_text

        # 1. Handle file upload/extraction
        if content_file and content_file.filename:
            filename = secure_filename(content_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            content_file.save(filepath)
            final_content = extract_text_from_file(filepath)
            
        # 2. Handle URL/Text input
        if not final_content and content_text:
            if is_url(content_text):
                 # In a real app, this would fetch content from the URL
                final_content = extract_text_from_file(content_text)
            else:
                final_content = content_text
        
        if not final_content:
            flash('Please provide content either by pasting text, a URL, or uploading a file.', 'danger')
            return render_template('create_quiz.html', current_difficulty=current_difficulty)

        # 3. Generate Questions (Pool Size is 2x the requested number for better adaptivity)
        pool_size = num_questions * 2 if quiz_type == 'adaptive' else num_questions
        
        # NOTE: The gemini_engine generates a pool of questions with mixed difficulty.
        question_pool = quiz_engine.generate_questions(
            content=final_content, 
            num_questions=pool_size,
            topic=topic
        )
        
        if not question_pool:
            flash('Could not generate quiz questions. Please try different content or topic.', 'danger')
            return render_template('create_quiz.html', current_difficulty=current_difficulty)

        # 4. Save Quiz to Database
        quiz_title = f"{topic} Quiz ({user_difficulty} - {quiz_type.capitalize()})"
        
        with get_db_connection(dict_cursor=False) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO quizzes (user_id, title, topic, content, questions, difficulty, quiz_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, quiz_title, topic, final_content, json.dumps(question_pool), user_difficulty, quiz_type))
            
            quiz_id = cursor.lastrowid
            conn.commit()
            
        flash(f'Quiz "{quiz_title}" created successfully!', 'success')
        
        # 5. Redirect to the appropriate quiz start page
        if quiz_type == 'adaptive':
            # Store the requested length for the adaptive route's stopping condition
            session['user_quiz_length'] = num_questions 
            return redirect(url_for('take_quiz', quiz_id=quiz_id))
        else:
            return redirect(url_for('take_simple_quiz', quiz_id=quiz_id))

    return render_template('create_quiz.html', current_difficulty=current_difficulty)

@app.route('/quiz/<int:quiz_id>')
def take_quiz(quiz_id):
    """Handles the start and display of the ADAPTIVE quiz, one question at a time."""
    if not is_logged_in():
        return redirect('/login')
    
    with get_db_connection() as conn:
        quiz = conn.execute('SELECT * FROM quizzes WHERE id = ? AND user_id = ? AND quiz_type = ?', 
                           (quiz_id, session['user_id'], 'adaptive')).fetchone()
    
    if not quiz:
        flash('Adaptive Quiz not found or is a simple quiz.', 'danger')
        return redirect('/dashboard')
    
    questions_pool = json.loads(quiz['questions'])
    
    # Initialize session tracking for the quiz
    if session.get('current_quiz_id') != quiz_id:
        session['current_quiz_id'] = quiz_id
        session['current_question_index'] = 0 # Index of how many questions the user has *answered*
        session['score'] = 0
        session['answered_questions'] = [] # Log of answered questions {q_id, difficulty, is_correct, time, user_answer}
        
        # Determine the initial difficulty based on user preference from DB
        start_difficulty = quiz['difficulty'].lower()
        session['current_difficulty_index'] = adaptive_engine.get_difficulty_index(start_difficulty)
        
        # Filter the pool to get the first question based on starting difficulty
        # NOTE: We pick the first matching question from the pool
        initial_q = next((q for q in questions_pool if q['difficulty'].lower() == start_difficulty), None)
        
        if initial_q:
            # We only send one question at a time to the template
            # Ensure the template has a length of 10 for the progress bar, or use the actual requested length
            quiz_length = session.get('user_quiz_length', 10) 
            return render_template('single_question_quiz.html', 
                                 quiz=dict(quiz), 
                                 questions=[initial_q],
                                 quiz_length=quiz_length,
                                 current_index=session['current_question_index'], 
                                 show_evaluation=False)
        else:
            flash('No questions found for the starting difficulty level. Try recreating the quiz with more content.', 'danger')
            return redirect('/dashboard')
    
    # If continuing, try to find and display the next question
    return redirect(url_for('next_question_adaptive', quiz_id=quiz_id))


# --- Adaptive Quiz Flow (submit_answer and next_question_adaptive are fine) ---
@app.route('/submit_answer/<int:quiz_id>', methods=['POST'])
def submit_answer(quiz_id):
    """Handles submission of a single question for an ADAPTIVE quiz."""
    if not is_logged_in() or session.get('current_quiz_id') != quiz_id:
        return redirect('/dashboard')
    
    current_difficulty_index = session.get('current_difficulty_index', 1)
    
    with get_db_connection() as conn:
        quiz = conn.execute('SELECT * FROM quizzes WHERE id = ? AND user_id = ?', 
                           (quiz_id, session['user_id'])).fetchone()
    
    if not quiz:
        flash('Quiz not found', 'danger')
        return redirect('/dashboard')
    
    # Get submitted data
    question_id = int(request.form.get('question_id', 0))
    user_answer = request.form.get('answer', '').strip()
    time_taken = int(request.form.get('time_taken', 1)) 
    
    # Find the current question in the full pool
    questions_pool = json.loads(quiz['questions'])
    current_question = next((q for q in questions_pool if q.get('id') == question_id), None)
    
    if not current_question:
        flash("Could not locate the current question in the pool. Quitting.", 'danger')
        return redirect(url_for('finalize_quiz', quiz_id=quiz_id))

    # 1. Evaluate Answer (FIXED ROBUST EVALUATION)
    user_normalized = user_answer.lower().strip()
    correct_normalized_list = [a.lower().strip() for a in current_question['correct_answer'].split(',') if a.strip()]
    is_correct = user_normalized in correct_normalized_list
    
    # Capture optional user feedback on the question
    feedback_type = request.form.get('feedback_type', '').strip().lower()
    feedback_comment = request.form.get('feedback_comment', '').strip()
    flag_question = 1 if request.form.get('flag_question') else 0

    if feedback_type not in {'positive', 'negative', 'neutral'}:
        feedback_type = None

    if feedback_type or feedback_comment or flag_question:
        with get_db_connection(dict_cursor=False) as feedback_conn:
            feedback_conn.execute(
                '''
                INSERT INTO question_feedback (quiz_id, question_id, user_id, feedback_type, comment, flagged, question_text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    quiz_id,
                    str(question_id),
                    session['user_id'],
                    feedback_type,
                    feedback_comment,
                    flag_question,
                    current_question.get('question_text', '')
                )
            )
            feedback_conn.commit()

    # 2. Update session score and answered questions log
    if is_correct:
        session['score'] = session.get('score', 0) + 1
        
    session['answered_questions'].append({
        'q_id': question_id,
        'user_answer': user_answer, 
        'difficulty': current_question['difficulty'],
        'is_correct': is_correct,
        'response_time': time_taken
    })
    
    # 3. Apply immediate, question-by-question adaptivity
    if is_correct:
        current_difficulty_index = min(current_difficulty_index + 1, 2)
        flash('✅ Correct! Increasing difficulty for the next question.', 'success')
    else:
        current_difficulty_index = max(current_difficulty_index - 1, 0)
        flash('❌ Incorrect. Decreasing difficulty for the next question.', 'warning')
    
    session['current_difficulty_index'] = current_difficulty_index
    session['current_question_index'] = session.get('current_question_index', 0) + 1
    
    # Update current question with user's specific response details for evaluation page
    current_question['user_answer'] = user_answer
    current_question['is_correct'] = is_correct
    current_question['response_time'] = time_taken
    
    # Determine quiz length for the progress bar/next button
    quiz_length = session.get('user_quiz_length', 10) 

    # Show evaluation on the current question
    return render_template('single_question_quiz.html',
                         quiz=dict(quiz),
                         questions=[current_question], 
                         quiz_length=quiz_length, # Pass to template
                         current_index=session['current_question_index'],
                         show_evaluation=True,
                         user_answer=user_answer,
                         is_correct=is_correct,
                         correct_answer=current_question['correct_answer'],
                         explanation=current_question.get('explanation', 'No explanation available.'))

@app.route('/next_question_adaptive/<int:quiz_id>')
def next_question_adaptive(quiz_id):
    """Finds and displays the next question for an ADAPTIVE quiz."""
    if not is_logged_in() or session.get('current_quiz_id') != quiz_id:
        return redirect('/dashboard')
    
    answered_count = session['current_question_index']
    quiz_length = session.get('user_quiz_length', 10) # Use the stored length
    
    # Stop after user's requested number of questions
    if answered_count >= quiz_length: 
        return redirect(url_for('finalize_quiz', quiz_id=quiz_id))
    
    # 1. Determine the required difficulty
    required_difficulty_index = session.get('current_difficulty_index', 1)
    required_difficulty = adaptive_engine.get_difficulty_by_index(required_difficulty_index)

    # 2. Find the next question from the pool that hasn't been answered
    with get_db_connection() as conn:
        quiz = conn.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
        questions_pool = json.loads(quiz['questions'])
    
    answered_q_ids = {q['q_id'] for q in session.get('answered_questions', [])}
    
    # Find the next question that matches the required difficulty and hasn't been answered
    next_question = next((q for q in questions_pool 
                           if q['difficulty'].lower() == required_difficulty.lower() and q['id'] not in answered_q_ids), None)
    
    if next_question:
        # 3. Render the next question
        return render_template('single_question_quiz.html',
                             quiz=dict(quiz),
                             questions=[next_question], # Only render the single next question
                             quiz_length=quiz_length, # Pass to template
                             current_index=answered_count, 
                             show_evaluation=False)
    else:
        # 4. If no more questions in the required pool, finish the quiz early
        flash("You've exhausted the question pool for the required adaptive path. Finalizing quiz.", 'info')
        return redirect(url_for('finalize_quiz', quiz_id=quiz_id))

@app.route('/finalize_quiz/<int:quiz_id>')
def finalize_quiz(quiz_id):
    """Finalizes an ADAPTIVE quiz, saves results, and updates user profile."""
    if not is_logged_in() or session.get('current_quiz_id') != quiz_id:
        return redirect('/dashboard')

    answered_log = session.get('answered_questions', [])
    total_answered = len(answered_log)
    total_correct = session.get('score', 0)
    
    final_score = (total_correct / total_answered) * 100 if total_answered > 0 else 0
    
    with get_db_connection() as conn:
        quiz = conn.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
        
        # 1. Update Performance Table using the log from session
        full_pool = json.loads(quiz['questions'])
        final_questions_map = {q['id']: q for q in full_pool}

        for log in answered_log:
            # Fetch question difficulty from the full pool using q_id
            q_detail = final_questions_map.get(log['q_id'], {})
            
            # Update performance tracking
            adaptive_engine.update_performance(
                user_id=session['user_id'],
                topic=quiz['topic'],
                difficulty=q_detail.get('difficulty', 'medium'),
                is_correct=log['is_correct'],
                response_time=log['response_time']
            )
            
            # Merge user response data into the final question map for saving
            if log['q_id'] in final_questions_map:
                final_questions_map[log['q_id']]['user_answer'] = log.get('user_answer', '') 
                final_questions_map[log['q_id']]['is_correct'] = log['is_correct']
                final_questions_map[log['q_id']]['response_time'] = log['response_time']

        # 2. Update overall user skill level
        next_difficulty = adaptive_engine.calculate_next_difficulty(
            user_id=session['user_id'],
            topic=quiz['topic'],
            current_score=final_score
        )
        conn.execute('UPDATE users SET skill_level = ? WHERE id = ?', 
                     (next_difficulty.capitalize(), session['user_id']))
        
        # Also update session skill level
        session['skill_level'] = next_difficulty.capitalize()

        # 3. Update quiz status in DB
        conn.execute('''UPDATE quizzes 
                       SET score = ?, status = ?, questions = ?
                       WHERE id = ?''',
                    (final_score, 'completed', json.dumps(list(final_questions_map.values())), quiz_id))
        conn.commit()
    
    # 4. Clear session and redirect
    session.pop('current_quiz_id', None)
    session.pop('current_question_index', None)
    session.pop('score', None)
    session.pop('answered_questions', None)
    session.pop('current_difficulty_index', None)
    session.pop('user_quiz_length', None) # Clear the length too
    
    # Update session stats for the profile modal
    user_id = session['user_id']
    with get_db_connection() as conn:
        total_quizzes = conn.execute('SELECT COUNT(*) FROM quizzes WHERE user_id = ?', (user_id,)).fetchone()[0]
        avg_score_result = conn.execute('SELECT AVG(score) FROM quizzes WHERE user_id = ? AND status = ?', 
                                      (user_id, 'completed')).fetchone()[0]
    session['quizzes_taken'] = total_quizzes
    session['avg_score'] = round(avg_score_result, 1) if avg_score_result else 0
    
    return redirect(f'/performance/{quiz_id}')

# =========================================================================
# === NEW ROUTES FOR NON-ADAPTIVE QUIZ FLOW (CRITICAL ADDITION)
# =========================================================================

@app.route('/quiz_simple/<int:quiz_id>')
def take_simple_quiz(quiz_id):
    """Handles the start and display of a SIMPLE quiz (all questions on one page)."""
    if not is_logged_in():
        return redirect('/login')
    
    with get_db_connection() as conn:
        quiz = conn.execute('SELECT * FROM quizzes WHERE id = ? AND user_id = ? AND quiz_type = ?', 
                           (quiz_id, session['user_id'], 'simple')).fetchone()
    
    if not quiz:
        flash('Simple Quiz not found or is an adaptive quiz.', 'danger')
        return redirect('/dashboard')
    
    # Check if already completed and redirect to results
    if quiz['status'] == 'completed':
        return redirect(url_for('performance_analysis', quiz_id=quiz_id))
        
    questions = json.loads(quiz['questions'])
    
    return render_template('simple_quiz.html', quiz=dict(quiz), questions=questions)

@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
def submit_quiz(quiz_id):
    """Handles submission of all questions for a SIMPLE quiz."""
    if not is_logged_in():
        return redirect('/login')

    user_id = session['user_id']
    
    with get_db_connection() as conn:
        quiz = conn.execute('SELECT * FROM quizzes WHERE id = ? AND user_id = ? AND quiz_type = ?', 
                           (quiz_id, user_id, 'simple')).fetchone()

    if not quiz or quiz['status'] == 'completed':
        flash('Quiz not found or already completed.', 'danger')
        return redirect('/dashboard')

    # 1. Evaluate Answers
    questions = json.loads(quiz['questions'])
    total_questions = len(questions)
    correct_count = 0
    answered_log = []
    feedback_entries = []
    
    # Create a map of question IDs to their details for easy access
    question_map = {q['id']: q for q in questions}

    for question in questions:
        q_id = question['id']
        user_answer = request.form.get(f'answer_{q_id}', '').strip()
        time_taken = int(request.form.get(f'time_{q_id}', 1))
        
        # Robust evaluation logic
        user_normalized = user_answer.lower().strip()
        correct_normalized_list = [a.lower().strip() for a in question['correct_answer'].split(',') if a.strip()]
        is_correct = user_normalized in correct_normalized_list
        
        if is_correct:
            correct_count += 1
            
        # Update question object with user response for saving
        question['user_answer'] = user_answer
        question['is_correct'] = is_correct
        question['response_time'] = time_taken
        
        # Prepare log for performance tracking
        answered_log.append({
            'q_id': q_id,
            'user_answer': user_answer,
            'difficulty': question['difficulty'],
            'is_correct': is_correct,
            'response_time': time_taken
        })

        feedback_type = request.form.get(f'feedback_type_{q_id}', '').strip().lower()
        feedback_comment = request.form.get(f'feedback_comment_{q_id}', '').strip()
        flag_question = 1 if request.form.get(f'flag_question_{q_id}') else 0

        if feedback_type not in {'positive', 'negative', 'neutral'}:
            feedback_type = None

        if feedback_type or feedback_comment or flag_question:
            feedback_entries.append({
                'quiz_id': quiz_id,
                'question_id': str(q_id),
                'feedback_type': feedback_type,
                'feedback_comment': feedback_comment,
                'flagged': flag_question,
                'question_text': question.get('question_text', '')
            })
    
    final_score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
    
    # Persist collected feedback before updating analytics
    if feedback_entries:
        with get_db_connection(dict_cursor=False) as feedback_conn:
            for entry in feedback_entries:
                feedback_conn.execute(
                    '''
                    INSERT INTO question_feedback (quiz_id, question_id, user_id, feedback_type, comment, flagged, question_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        entry['quiz_id'],
                        entry['question_id'],
                        user_id,
                        entry['feedback_type'],
                        entry['feedback_comment'],
                        entry['flagged'],
                        entry['question_text']
                    )
                )
            feedback_conn.commit()

    # 2. Update Performance Table and User Skill Level
    for log in answered_log:
        q_detail = question_map.get(log['q_id'], {})
        adaptive_engine.update_performance(
            user_id=user_id,
            topic=quiz['topic'],
            difficulty=q_detail.get('difficulty', 'medium'),
            is_correct=log['is_correct'],
            response_time=log['response_time']
        )
    
    next_difficulty = adaptive_engine.calculate_next_difficulty(
        user_id=user_id,
        topic=quiz['topic'],
        current_score=final_score
    )
    conn.execute('UPDATE users SET skill_level = ? WHERE id = ?', 
                 (next_difficulty.capitalize(), user_id))
    session['skill_level'] = next_difficulty.capitalize()


    # 3. Update Quiz in DB
    conn.execute('''UPDATE quizzes 
                   SET score = ?, status = ?, questions = ?
                   WHERE id = ?''',
                (final_score, 'completed', json.dumps(questions), quiz_id))
    conn.commit()

    # Update session stats for the profile modal
    with get_db_connection() as conn_stats:
        total_quizzes_stat = conn_stats.execute('SELECT COUNT(*) FROM quizzes WHERE user_id = ?', (user_id,)).fetchone()[0]
        avg_score_result = conn_stats.execute('SELECT AVG(score) FROM quizzes WHERE user_id = ? AND status = ?', 
                                      (user_id, 'completed')).fetchone()[0]
    session['quizzes_taken'] = total_quizzes_stat
    session['avg_score'] = round(avg_score_result, 1) if avg_score_result else 0
    
    flash(f'Quiz completed! Your score: {final_score:.1f}%', 'success')
    return redirect(url_for('performance_analysis', quiz_id=quiz_id))


# --- Existing Routes (Performance/Logout/Results) ---

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect('/')

@app.route('/performance/<int:quiz_id>')
def performance_analysis(quiz_id):
    if not is_logged_in():
        return redirect('/login')

    with get_db_connection() as conn:
        quiz = conn.execute('SELECT * FROM quizzes WHERE id = ? AND user_id = ?', 
                           (quiz_id, session['user_id'])).fetchone()

    if not quiz or quiz['status'] != 'completed':
        flash('Quiz not found or not completed.', 'danger')
        return redirect('/dashboard')
    
    questions = json.loads(quiz['questions'])
    
    # Filter questions to include only those answered by the user (which have 'user_answer' set)
    # This correctly handles both adaptive (where questions not asked don't have 'user_answer') and simple quizzes.
    final_questions = [q for q in questions if 'user_answer' in q]

    total_questions = len(final_questions)
    correct_count = sum(1 for q in final_questions if q.get('is_correct'))
    
    # FIX: Calculate score correctly based on answered count
    score = (correct_count / total_questions) * 100 if total_questions else 0
    incorrect_count = total_questions - correct_count

    # Initialize breakdown dictionaries with 0 counts
    difficulty_breakdown = {'Easy': {'correct': 0, 'total': 0}, 'Medium': {'correct': 0, 'total': 0}, 'Hard': {'correct': 0, 'total': 0}}
    type_breakdown = {'mcq': {'correct': 0, 'total': 0}, 'true_false': {'correct': 0, 'total': 0}, 'short_answer': {'correct': 0, 'total': 0}}
    total_time = 0
    time_per_q_list = []
    
    for q in final_questions:
        diff = q.get('difficulty', 'Medium').capitalize()
        # Fallback for question type
        q_type = q.get('question_type', 'mcq').lower()
        if 'true' in q_type or 'false' in q_type: q_type = 'true_false'
        
        is_correct = q.get('is_correct', False)
        response_time = q.get('response_time', 0)
        
        difficulty_breakdown.setdefault(diff, {'correct': 0, 'total': 0})['total'] += 1
        if is_correct:
            difficulty_breakdown[diff]['correct'] += 1
        
        type_breakdown.setdefault(q_type, {'correct': 0, 'total': 0})['total'] += 1
        if is_correct:
            type_breakdown[q_type]['correct'] += 1
            
        total_time += response_time
        time_per_q_list.append(response_time) # Collect times for the bottom graph

    avg_time_per_q = total_time / total_questions if total_questions else 0

    return render_template('performance_analysis.html', 
                           quiz=dict(quiz),
                           score=score, 
                           correct_count=correct_count,
                           incorrect_count=incorrect_count,
                           difficulty_breakdown=difficulty_breakdown,
                           type_breakdown=type_breakdown,
                           total_time=total_time,
                           avg_time_per_q=avg_time_per_q,
                           questions=final_questions,
                           time_per_q_list=time_per_q_list)


@app.route('/results/<int:quiz_id>')
def quiz_results(quiz_id):
    """Alias for performance analysis as results.html wasn't the main view."""
    return redirect(f'/performance/{quiz_id}')

# --- FEEDBACK ROUTES ---

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if not is_logged_in():
        flash('You must be logged in to leave feedback.', 'danger')
        return redirect('/login')
        
    if request.method == 'POST':
        feedback_type = request.form.get('feedback_type')
        rating = request.form.get('rating')
        comments = request.form.get('comments', '').strip()
        
        user_id = session['user_id']
        username = session['username']
        
        # NOTE: In a real application, you would INSERT this data into a dedicated 'feedback' database table here.
        # For now, we'll print to console and flash a message.
        
        print("-" * 40)
        print(f"🚨 NEW FEEDBACK RECEIVED (User ID: {user_id}, Username: {username})")
        print(f"Type: {feedback_type}")
        print(f"Rating: {rating}/5")
        print(f"Comments: {comments}")
        print("-" * 40)
        
        flash(f'Thank you for your feedback ({feedback_type})! We appreciate you helping us improve.', 'success')
        return redirect('/dashboard')
        
    return render_template('feedback.html')

# --- END FEEDBACK ROUTES ---


if __name__ == '__main__':
    print("🚀 SMART QUIZZER STARTING...")
    # Ensure database is initialized before running
    with app.app_context():
        init_db()
    app.run(debug=True, port=5000)