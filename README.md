Here is the final, comprehensive `README.md` file, ready for you to copy and paste directly into your GitHub repository:

-----

# 🧠 Smart Quizzer: AI-Powered Adaptive Learning Platform

## 🎯 Project Overview

The Smart Quizzer is an innovative web application that leverages **Generative AI** and a custom **Adaptive Learning Engine** to create personalized, highly efficient quizzes. Its core objective is to move beyond static assessment, providing a dynamic learning environment that constantly challenges the user at their individual **Skill Level**.

Users can input or upload educational content (text, simulated PDFs/PPTs), and the system instantly generates tailored question pools, adjusting the subsequent question's difficulty in **real-time** based on their performance.

-----

## ✨ Core Feature Breakdown

| Feature | Technical Mechanism | Impact on Learning |
| :--- | :--- | :--- |
| **AI Question Generation** | Utilizes **Gemini API** via `gemini_engine.py` with structured **Prompt Engineering** to ensure JSON output includes `question_text`, `options`, `correct_answer`, `difficulty`, and a detailed `explanation`. | Guarantees instant content creation and provides immediate, context-specific feedback. |
| **Real-time Adaptivity** | Implemented in `simple_adaptive_engine.py` by adjusting the `session['current_difficulty_index']` after *every* answer (increment/decrement). | Keeps the user in the optimal learning zone (neither too easy nor too hard), maximizing engagement and retention. |
| **Skill Level Tracking** | The final quiz score is used by the adaptive engine to update the user's overall **Skill Level** (Beginner, Medium, Advanced) in the database. | Personalizes the starting point of new quizzes and tracks long-term mastery. |
| **Comprehensive Analytics** | The system logs every user response (`is_correct`, `response_time`) for every question answered, feeding data to the `performance_analysis.html` view. | Provides actionable insights into accuracy across specific difficulty levels and topics. |
| **Dual Quiz Modes** | Logic in `create_quiz.html` and `app.py` allows selection between **Adaptive** (one-question flow) and **Simple** (bulk-submission flow). | Offers flexibility for both diagnostic testing (Adaptive) and quick knowledge checks (Simple). |

-----

## 🛠️ Technology Stack and Architecture

| Component | Technology | Role in the Application |
| :--- | :--- | :--- |
| **Backend/Core** | **Python (Flask)** | Handles the HTTP requests, manages the user session, and acts as the central orchestrator between the UI, Database, and AI Engines. |
| **AI Layer** | **Google Gemini API** | Provides the sophisticated text generation capability for quiz creation. |
| **Database** | **SQLite3** | Used for all persistent data storage (Users, Quizzes, Performance). |
| **Frontend/Design** | **Tailwind CSS & JavaScript** | **Tailwind** for high-quality, responsive styling. **JavaScript** for client-side interactivity, timers, and the feedback mechanism. |

-----

## ⚙️ Getting Started

Follow these instructions to get a copy of the project running locally.

### Prerequisites

  * **Python 3.9+**
  * A **Gemini API Key** (required for quiz generation)

### Installation Steps

1.  **Clone the Repository:**

    ```bash
    git clone [YOUR GITHUB REPO URL HERE]
    cd SmartQuizzer
    ```

2.  **Create and Activate a Virtual Environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate     # On Windows
    ```

3.  **Install Required Packages:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up API Key:**
    Create a file named **`.env`** in the root directory to store your API key:

    ```env
    # .env file content
    GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY_HERE"
    FLASK_SECRET_KEY="A_STRONG_RANDOM_SECRET_KEY_FOR_SESSION"
    ```

    *(Note: Ensure your `gemini_engine.py` is configured to load this key, or for quick setup, ensure the placeholder key in that file is replaced with a valid key for local testing.)*

5.  **Run the Application:**

    ```bash
    python app.py
    ```

    The application will initialize the `quizzes.db` file and run on `http://127.0.0.1:5000/`.

-----

## 📂 Project Structure (Key Files)

| File/Folder | Primary Responsibility |
| :--- | :--- |
| `app.py` | **Core Logic:** All Flask routing, session management, and database setup. |
| `gemini_engine.py` | **AI Prompting:** Generates structured quiz data via the Gemini API. |
| `simple_adaptive_engine.py` | **Adaptive Rules:** Contains the logic for difficulty adjustment, performance logging, and skill level calculation. |
| `templates/` | **UI Templates:** Houses all Jinja2 views (HTML), including `Base.html`, quiz interfaces, and analysis pages. |
| `quizzes.db` | **Database:** Stores structured data for `users`, `quizzes`, and granular `performances` logs. |

-----

## 🤝 Contribution and Feedback

This project is a functional demonstration of integrating AI with a full-stack learning platform.

We welcome feedback and suggestions\! Please use the dedicated **Feedback** page within the application after logging in.
