import sqlite3
import hashlib
from datetime import datetime

class Database:
    def __init__(self, db_name='quizzer.db'):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        # Users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User sessions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                topic TEXT,
                subtopic TEXT,
                skill_level TEXT,
                score INTEGER,
                total_questions INTEGER,
                time_taken INTEGER,
                session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Quiz results table
        c.execute('''
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_id INTEGER,
                question TEXT,
                user_answer TEXT,
                correct_answer TEXT,
                is_correct BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def add_user(self, username, password, email="", full_name=""):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users (username, password, email, full_name) VALUES (?, ?, ?, ?)",
                (username, self.hash_password(password), email, full_name)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            return False
    
    def verify_user(self, username, password):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute(
            "SELECT id, username, full_name FROM users WHERE username = ? AND password = ?",
            (username, self.hash_password(password))
        )
        user = c.fetchone()
        conn.close()
        return user
    
    def record_session(self, user_id, topic, subtopic, skill_level, score=0, total_questions=0, time_taken=0):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute(
            """INSERT INTO user_sessions (user_id, topic, subtopic, skill_level, score, total_questions, time_taken) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, topic, subtopic, skill_level, score, total_questions, time_taken)
        )
        session_id = c.lastrowid
        conn.commit()
        conn.close()
        return session_id
    
    def save_quiz_result(self, user_id, session_id, question, user_answer, correct_answer, is_correct):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute(
            """INSERT INTO quiz_results (user_id, session_id, question, user_answer, correct_answer, is_correct) 
            VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, session_id, question, user_answer, correct_answer, is_correct)
        )
        conn.commit()
        conn.close()
    
    def get_user_stats(self, user_id):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM user_sessions WHERE user_id = ?", (user_id,))
        total = c.fetchone()[0]
        
        c.execute("SELECT AVG(score) FROM user_sessions WHERE user_id = ?", (user_id,))
        avg_score = c.fetchone()[0] or 0
        
        conn.close()
        return total, round(avg_score, 1)
    
    def update_session_results(self, session_id, score, total_questions, time_taken):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute(
            "UPDATE user_sessions SET score = ?, total_questions = ?, time_taken = ? WHERE id = ?",
            (score, total_questions, time_taken, session_id)
        )
        conn.commit()
        conn.close()