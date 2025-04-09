
# **Student-Teacher Portal**  
*A Classroom Management System with AI-Generated Quizzes*  

## **✨ Overview**  
The **Student-Teacher Portal** is a **web-based platform** that empowers teachers to **create virtual classrooms, manage students, and assign auto-generated quizzes** using **Ollama (LLM)**. Students can take these quizzes, and the system generates **detailed performance reports** visible to both teachers and students.  

Built with **Flask (Backend), Django templates (Frontend), and SQLAlchemy (Database)**, this project leverages **Ollama’s open-source LLM** (instead of OpenAI) for **dynamic quiz generation**, making it a **privacy-friendly** alternative.  

---

## **🚀 Key Features**  

### **👨‍🏫 For Teachers:**  
✔ **Create & Manage Classrooms** – Organize students into different classes.  
✔ **Add/Remove Students** – Simple enrollment management.  
✔ **AI-Powered Quiz Generation** – Uses **Ollama LLM** to generate quizzes (MCQs, short answers) based on topic/difficulty.  
✔ **Assign & Schedule Quizzes** – Set deadlines and distribute quizzes.  
✔ **Automated Grading & Analytics** – Instant reports on student performance.  

### **👨‍🎓 For Students:**  
✔ **Take Quizzes** – Attempt assigned quizzes before deadlines.  
✔ **Real-Time Results** – View scores immediately after submission.  
✔ **Performance Reports** – Analyze strengths/weaknesses with detailed feedback.  

---

## **🛠 Technology Stack**  
| Category       | Technologies Used |  
|----------------|------------------|  
| **Backend**    | Flask (Python)   |  
| **Frontend**   | Django Templates (HTML, CSS, JS) |  
| **Database**   | SQLAlchemy (SQLite/PostgreSQL) |  
| **AI Model**   | **Ollama** (Local LLM for quiz generation) |  
| **Auth**       | Flask-Login / JWT |  

---

## **🔧 How It Works?**  
1. **Teacher Signs Up** → Creates a **classroom** and **invites students**.  
2. **AI Quiz Generation** → Teacher inputs a topic, and **Ollama generates questions**.  
3. **Quiz Assignment** → Teacher schedules quizzes for students.  
4. **Students Attempt Quizzes** → Submit answers before the deadline.  
5. **Auto-Grading & Reports** → System evaluates responses and generates **performance analytics**.  
6. **Progress Tracking** → Both teachers and students view reports.  

---

## **📌 Future Improvements**  
- **Multi-language support** (for non-English quizzes).  
- **Plagiarism detection** in student submissions.  
- **Mobile responsiveness** for better accessibility.  
- **Integration with Google Classroom/Microsoft Teams**.  

---

## **⚙️ Setup & Installation**  
1. **Clone the repo:**  
   ```bash
   git clone https://github.com/your-repo/student-teacher-portal.git
   cd student-teacher-portal
   ```

2. **Set up a virtual environment:**  
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate    # Windows
   ```

3. **Install dependencies:**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Ollama (LLM):**  
   - Download & install [Ollama](https://ollama.ai/).  
   - Run the desired model (e.g., `ollama pull llama3`).  

5. **Database setup:**  
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. **Run the app:**  
   ```bash
   flask run
   ```
   Access at **`http://127.0.0.1:5000`**  

---

## **🤝 Contributing**  
Contributions are welcome! Open an **issue** or submit a **PR** for improvements.  

---

### **📜 License**  
This project is licensed under **MIT License**.  
