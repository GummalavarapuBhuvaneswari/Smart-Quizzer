import random
from database import Database

class QuizBackend:
    def __init__(self):
        self.db = Database()
    
    def get_questions(self, topic, subtopic, level, count=10):
        # Sample questions database
        questions_db = {
            "Computer Science": {
                "Python": {
                    "Beginner": [
                        {
                            "question": "Which keyword is used to define a function in Python?",
                            "options": ["function", "def", "define", "func"],
                            "correct": 1
                        },
                        {
                            "question": "What is the output of print(2 ** 3)?",
                            "options": ["6", "8", "9", "5"],
                            "correct": 1
                        },
                        {
                            "question": "Which data type is mutable in Python?",
                            "options": ["tuple", "string", "list", "int"],
                            "correct": 2
                        }
                    ],
                    "Intermediate": [
                        {
                            "question": "What does the 'self' parameter represent in Python class methods?",
                            "options": ["The class itself", "The instance of the class", "A static method", "A decorator"],
                            "correct": 1
                        },
                        {
                            "question": "Which method is used to add an element to a set?",
                            "options": ["append()", "add()", "insert()", "push()"],
                            "correct": 1
                        }
                    ],
                    "Advanced": [
                        {
                            "question": "What is the time complexity of searching in a Python dictionary?",
                            "options": ["O(n)", "O(log n)", "O(1)", "O(n²)"],
                            "correct": 2
                        }
                    ]
                },
                "Java": {
                    "Beginner": [
                        {
                            "question": "What is the entry point of a Java program?",
                            "options": ["main() method", "start() method", "run() method", "execute() method"],
                            "correct": 0
                        },
                        {
                            "question": "Which keyword is used to inherit a class in Java?",
                            "options": ["implements", "extends", "inherits", "super"],
                            "correct": 1
                        }
                    ],
                    "Intermediate": [
                        {
                            "question": "What is method overloading in Java?",
                            "options": [
                                "Same method name with different return types",
                                "Same method name with different parameters",
                                "Same method name in different classes",
                                "Same method name with different access modifiers"
                            ],
                            "correct": 1
                        }
                    ],
                    "Advanced": [
                        {
                            "question": "What is the purpose of the 'volatile' keyword in Java?",
                            "options": [
                                "To make variable constant",
                                "To indicate variable may be changed by multiple threads",
                                "To improve performance",
                                "To prevent garbage collection"
                            ],
                            "correct": 1
                        }
                    ]
                },
                "C++": {
                    "Beginner": [
                        {
                            "question": "Which operator is used for dynamic memory allocation in C++?",
                            "options": ["malloc", "new", "alloc", "create"],
                            "correct": 1
                        }
                    ],
                    "Intermediate": [
                        {
                            "question": "What is a virtual function in C++?",
                            "options": [
                                "A function that doesn't exist",
                                "A function that can be overridden in derived classes",
                                "A function that runs faster",
                                "A function that uses virtual memory"
                            ],
                            "correct": 1
                        }
                    ]
                }
            },
            "Mathematics": {
                "Algebra": {
                    "Beginner": [
                        {
                            "question": "Solve for x: 2x + 5 = 15",
                            "options": ["5", "10", "7.5", "8"],
                            "correct": 0
                        }
                    ]
                }
            }
        }
        
        # Get questions for the selected topic, subtopic and level
        try:
            questions = questions_db[topic][subtopic][level]
            return random.sample(questions, min(count, len(questions)))
        except:
            # Return some default questions if specific ones not found
            return [
                {
                    "question": f"Sample question for {subtopic} ({level})",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct": 0
                }
            ] * min(count, 5)
    
    def calculate_results(self, questions, user_answers):
        score = 0
        total_questions = len(questions)
        results = []
        
        for i, (question, user_answer) in enumerate(zip(questions, user_answers)):
            correct_index = question['correct']
            correct_answer = question['options'][correct_index]
            is_correct = (user_answer == correct_answer)
            
            if is_correct:
                score += 1
            
            results.append({
                'question': question['question'],
                'user_answer': user_answer or "Not answered",
                'correct_answer': correct_answer,
                'is_correct': is_correct
            })
        
        percentage = (score / total_questions) * 100
        
        return {
            'score': score,
            'total_questions': total_questions,
            'percentage': percentage,
            'results': results
        }
    
    def get_performance_message(self, percentage):
        if percentage >= 80:
            return "🎉 Excellent! You're a master!", "#22c55e"
        elif percentage >= 60:
            return "👍 Good job! Keep practicing!", "#3b82f6"
        elif percentage >= 40:
            return "💪 Not bad! Room for improvement.", "#f59e0b"
        else:
            return "📚 Keep learning! You'll get better.", "#ef4444"