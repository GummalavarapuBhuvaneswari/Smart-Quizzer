import google.generativeai as genai
import json
import os
import random

class GeminiQuizEngine:
    def __init__(self):
        try:
            # NOTE: Using the placeholder key found in your uploaded files.
            genai.configure(api_key="AIzaSyD4Qofgsr6eiSYf0OROUjTwbWhJXwYwL2A")
            self.model = genai.GenerativeModel("gemini-2.5-flash")
            self.demo_mode = False
            print("✅ Gemini 2.5 Flash initialized successfully!")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini: {e}")
            self.demo_mode = True
    
    def generate_questions(self, content, num_questions, difficulty='mixed', topic='General Knowledge'):
        print(f"🔍 Generating pool of {num_questions} questions for topic: '{topic}' based on input content...")
        
        if self.demo_mode:
            print("🚨 Using demo mode - Gemini not available")
            return self._generate_fallback_questions(content, num_questions)
        
        try:
            # The prompt is constructed to demand a pool of questions (mixed difficulty)
            prompt = self._build_strict_prompt(content, num_questions, topic)
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean and parse JSON response
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            data = json.loads(response_text)
            questions = data['questions']
            
            # Add unique IDs and set topic/difficulty for adaptive filtering
            for i, question in enumerate(questions):
                question['id'] = i + 1
                # Ensure difficulty is lowercase for engine comparison
                question['difficulty'] = question.get('difficulty', 'medium').lower()
                question['topic'] = topic
                
                if 'explanation' not in question:
                    question['explanation'] = "No explanation provided by AI."
            
            # Final check to ensure we generated enough questions
            if len(questions) < num_questions:
                 # If AI fails to meet the count, fill with fallback questions
                print(f"WARNING: AI only returned {len(questions)} questions. Using fallback to reach target.")
                return questions + self._generate_fallback_questions(content, num_questions - len(questions))
            
            print(f"✅ Generated {len(questions)} questions for the adaptive pool.")
            
            return questions
            
        except Exception as e:
            print(f"❌ Gemini error: {e}. Using content-based fallback.")
            return self._generate_fallback_questions(content, num_questions)
    
    def _build_strict_prompt(self, content, num_questions_pool, topic):
        """Builds a prompt requiring a strict JSON output with mixed difficulty."""
        
        return f"""
        CONTENT ABOUT {topic.upper()}:
        "{content}"

        TASK: Create a pool of exactly {num_questions_pool} quiz questions that test understanding of THE ACTUAL CONCEPTS and facts in the content above. The questions must be distributed across Easy, Medium, and Hard difficulties.

        QUESTION TYPES: Use a mix of Multiple Choice (MCQ) and True/False questions. DO NOT use short answer.

        DIFFICULTY ASSIGNMENT: Explicitly label each question with one of the following: "Easy", "Medium", or "Hard". Ensure roughly equal distribution among the three levels.
        
        STRICT RULES:
        1. All questions must be derived ONLY from the provided CONTENT.
        2. Provide a clear, detailed 'explanation' for why the correct answer is right.
        3. The total number of questions MUST equal {num_questions_pool}.

        OUTPUT FORMAT (JSON array of objects only):
        {{
            "questions": [
                {{
                    "id": 1,
                    "question_text": "Direct question about the content...",
                    "question_type": "mcq",
                    "options": ["...", "...", "...", "..."],
                    "correct_answer": "Correct Option",
                    "explanation": "This answer is correct because...",
                    "difficulty": "Easy" 
                }},
                {{
                    "id": 2,
                    "question_text": "True or False: Statement about content.",
                    "question_type": "true_false",
                    "options": ["True", "False"],
                    "correct_answer": "True",
                    "explanation": "This is true because...",
                    "difficulty": "Medium" 
                }}
            ]
        }}

        Return ONLY the raw JSON object. Do not include any introductory or concluding text.
        """
    
    def _generate_fallback_questions(self, content, num_questions):
        """Generates simple, fixed fallback questions for testing when Gemini fails."""
        questions = []
        
        for i in range(num_questions):
            diff = ['easy', 'medium', 'hard'][i % 3] # Cycle through difficulties
            
            if i % 2 == 0:  # MCQ
                questions.append({
                    "id": i + 1,
                    "question_text": f"FALLBACK Q{i+1}: What is the core subject based on your content size ({len(content)} chars)?",
                    "question_type": "mcq",
                    "options": ["Adaptive Systems", "Database Design", "AI Models", "Fallback Topic"],
                    "correct_answer": "Adaptive Systems",
                    "explanation": "This is a fixed fallback question.",
                    "difficulty": diff,
                    "topic": "Fallback"
                })
            else:  # True/False
                questions.append({
                    "id": i + 1,
                    "question_text": f"FALLBACK Q{i+1}: It is true that this app uses Flask.",
                    "question_type": "true_false",
                    "options": ["True", "False"],
                    "correct_answer": "True",
                    "explanation": "This is a fixed fallback question, confirming the stack.",
                    "difficulty": diff,
                    "topic": "Fallback"
                })
        
        return questions