import sqlite3
from datetime import datetime

class SimpleAdaptiveEngine:
    def __init__(self):
        self.difficulty_levels = ['easy', 'medium', 'hard']
    
    def get_difficulty_index(self, difficulty):
        """Returns the index of a difficulty level (0=easy, 1=medium, 2=hard)."""
        return self.difficulty_levels.index(difficulty.lower()) if difficulty.lower() in self.difficulty_levels else 1
    
    def get_difficulty_by_index(self, index):
        """Returns the difficulty string from its index, clamped between 0 and 2."""
        clamped_index = max(0, min(index, len(self.difficulty_levels) - 1))
        return self.difficulty_levels[clamped_index]

    def calculate_next_difficulty(self, user_id, topic, current_score):
        """
        Calculates the new overall skill level based on final quiz score (for analytics update).
        """
        conn = sqlite3.connect('quizzes.db')
        cursor = conn.cursor()
        
        # Fetch user's current skill level from the 'users' table
        result = cursor.execute('SELECT skill_level FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        
        current_difficulty = result[0].lower() if result else 'medium'
        current_index = self.get_difficulty_index(current_difficulty)
        
        # Calculate next difficulty based on score thresholds (50% and 80%)
        if current_score >= 80:
            next_index = min(current_index + 1, len(self.difficulty_levels) - 1)
        elif current_score < 50:
            next_index = max(current_index - 1, 0)
        else:
            next_index = current_index
        
        return self.difficulty_levels[next_index]
    
    def update_performance(self, user_id, topic, difficulty, is_correct, response_time):
        """Update performance tracking in the dedicated 'performances' database table."""
        conn = sqlite3.connect('quizzes.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM performances 
            WHERE user_id = ? AND topic = ? AND difficulty = ?
        ''', (user_id, topic, difficulty.lower()))
        
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
            ''', (user_id, topic, difficulty.lower(), accuracy, total_questions, correct_answers, response_time))
        
        conn.commit()
        conn.close()