import sqlite3
from datetime import datetime
import time

class SimpleAdaptiveEngine:
    def __init__(self):
        self.difficulty_levels = ['easy', 'medium', 'hard']
    
    def calculate_next_difficulty(self, user_id, topic, current_score):
        """Calculate next difficulty based on current score (80% threshold)."""
        
        # 1. Fetch user's latest overall difficulty for this topic
        conn = sqlite3.connect('quizzes.db')
        cursor = conn.cursor()
        
        # Check the user's current overall skill level, not just the last performance record
        cursor.execute('''
            SELECT skill_level FROM users WHERE id = ?
        ''', (user_id,))
        
        user_skill_level = cursor.fetchone()[0] if cursor.fetchone() else 'medium'
        conn.close()
        
        current_difficulty = user_skill_level.lower()
        
        # 2. Apply 80% adaptive logic
        try:
            current_index = self.difficulty_levels.index(current_difficulty)
        except ValueError:
            current_index = 1 # Default to medium
        
        if current_score >= 80:
            # Move to next difficulty level
            next_index = min(current_index + 1, len(self.difficulty_levels) - 1)
        elif current_score < 50:
            # Move to easier level (Use 50% for a stronger decrease signal)
            next_index = max(current_index - 1, 0)
        else:
            next_index = current_index
        
        next_difficulty = self.difficulty_levels[next_index]
        
        # NOTE: The actual user skill level update is handled in app.py after this call.
        return next_difficulty
    
    def update_performance(self, user_id, topic, difficulty, is_correct, response_time):
        """Update performance tracking in the dedicated 'performances' database table."""
        conn = sqlite3.connect('quizzes.db')
        cursor = conn.cursor()
        
        # Ensure the performance record is looked up by topic AND difficulty for granular tracking
        cursor.execute('''
            SELECT * FROM performances 
            WHERE user_id = ? AND topic = ? AND difficulty = ?
        ''', (user_id, topic, difficulty))
        
        performance = cursor.fetchone()
        
        if performance:
            # Update existing performance
            perf_id, _, _, _, accuracy, total_questions, correct_answers, avg_time, _ = performance
            
            total_questions += 1
            if is_correct:
                correct_answers += 1
            
            new_accuracy = correct_answers / total_questions
            
            # Update average response time using exponential moving average (0.7 old, 0.3 new)
            if avg_time == 0:
                new_avg_time = response_time
            else:
                new_avg_time = (0.7 * avg_time) + (0.3 * response_time)
            
            cursor.execute('''
                UPDATE performances 
                SET accuracy = ?, total_questions = ?, correct_answers = ?, 
                    average_response_time = ?, updated_at = ?
                WHERE id = ?
            ''', (new_accuracy, total_questions, correct_answers, new_avg_time, datetime.now(), perf_id))
        else:
            # Create new performance record
            total_questions = 1
            correct_answers = 1 if is_correct else 0
            accuracy = 1.0 if is_correct else 0.0
            
            cursor.execute('''
                INSERT INTO performances 
                (user_id, topic, difficulty, accuracy, total_questions, correct_answers, average_response_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, topic, difficulty, accuracy, total_questions, correct_answers, response_time))
        
        conn.commit()
        conn.close()
