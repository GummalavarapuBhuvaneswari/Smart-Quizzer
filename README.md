# 🧠 Smart Quizzer: AI-Powered Adaptive Learning Platform

## 🎯 Project Overview

Smart Quizzer is an innovative web application that leverages **Generative AI** and a custom **Adaptive Learning Engine** to create highly personalized quizzes from any educational content. Users can upload text, PDFs, or PPTs, and the system instantly generates tailored quizzes, adjusting question difficulty in real-time based on the user's performance.

**Key Features:**

* **AI Question Generation:** Instantly creates multiple-choice and true/false questions, complete with correct answers and explanations, using the **Gemini API**.
* **Real-time Adaptivity:** A custom algorithm adjusts the next question's difficulty level (Easy, Medium, Hard) after every submission, keeping the user in the optimal learning zone.
* **Dual Quiz Modes:** Supports **Adaptive (1-question-at-a-time)** and **Simple (all-on-one-page)** quiz formats.
* **Comprehensive Analytics:** Tracks user performance, response time, and accuracy across different topics and difficulty levels.
* **User Management:** Secure user registration, login, and personalized profile management, including an adaptable **Skill Level**.

## 🛠️ Technology Stack

| Category | Technology | Role |
| :--- | :--- | :--- |
| **Backend/Core** | **Python (Flask)** | The web framework for routing, session management, and backend logic. |
| **AI Integration** | **Google Gemini API** | Used by `gemini_engine.py` for content processing and question generation. |
| **Database** | **SQLite3** | Lightweight, file-based database for storing users, quizzes, and performance logs. |
| **Frontend** | **HTML5, Jinja2** | Templating for dynamic data injection into the user interface. |
| **Styling** | **Tailwind CSS** | Utility-first framework for responsive, modern UI design. |
| **Client-Side** | **JavaScript** | Handles the interactive star rating, quiz timers, and modal functionality. |

## ⚙️ Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### Prerequisites

You need **Python 3.9+** installed on your system.

### Installation Steps

1.  **Clone the Repository:**
    ```bash
    git clone [YOUR GITHUB REPO URL HERE]
    cd SmartQuizzer
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate     # On Windows
    ```

3.  **Install Required Packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Environment Variables:**
    Create a file named **`.env`** in the root directory and add your API key for the Gemini service.
    ```env
    # .env file content
    GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY_HERE"
    FLASK_SECRET_KEY="A_STRONG_RANDOM_SECRET" 
    ```
    *(Note: You must replace the placeholder key in `gemini_engine.py` with the environment variable loading logic for production, but for now, ensure your API key is correctly configured in your project files.)*

5.  **Run the Application:**
    ```bash
    python app.py
    ```

The application should now be running at `http://127.0.0.1:5000/`.

## 📂 Project Structure (Key Files)

| File/Folder | Description |
| :--- | :--- |
| `app.py` | **Main App:** Contains all Flask routes, session management, and core application logic. |
| `gemini_engine.py` | **AI Generator:** Handles the connection and prompting for the Gemini API to generate structured quiz data. |
| `simple_adaptive_engine.py` | **Adaptive Logic:** Implements the custom algorithm for adjusting difficulty and calculating user skill level. |
| `quizzes.db` | The main **SQLite database** file storing all persistent data. |
| `templates/` | Contains all HTML templates rendered via Jinja2. |
| `requirements.txt` | Lists all necessary Python dependencies. |

## 🤝 Contribution and Feedback

This project was built to demonstrate proficiency in integrating AI with a full-stack web application.

We welcome feedback and suggestions! Please use the dedicated **Feedback** page within the application or submit an issue on GitHub.

---
*(This structure provides a comprehensive overview for any reviewer, clearly separating the 'what' (Project Overview), the 'how' (Technology Stack & Installation), and the 'why' (Adaptive Logic).)*
