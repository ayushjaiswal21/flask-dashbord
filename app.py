from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, User, Quiz, Classroom, Question
import os
import time
import json
import logging
import requests
import mysql.connector
from flask_cors import CORS
from dotenv import load_dotenv
from mysql.connector import Error as DBError

# Set up logging with DEBUG level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
app = Flask(__name__, template_folder='templates')
CORS(app)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///classquiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Replace before_first_request with app context
with app.app_context():
    db.create_all()

class DatabaseManager:
    @staticmethod
    def get_connection():
        try:
            return mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME'),
                port=int(os.getenv('DB_PORT', 3306)),
                connect_timeout=5
            )
        except DBError as e:
            logger.error(f"Database connection failed: {str(e)}")
            return None

    @staticmethod
    def save_questions(questions):
        db = DatabaseManager.get_connection()
        if not db:
            return False, "Database unavailable"
        try:
            with db.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS questions (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        topics JSON NOT NULL,
                        question_text TEXT NOT NULL,
                        correct_answer TEXT NOT NULL,
                        question_type VARCHAR(50) NOT NULL,
                        difficulty VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.executemany(
                    """INSERT INTO questions 
                    (topics, question_text, correct_answer, question_type, difficulty) 
                    VALUES (%s, %s, %s, %s, %s)""",
                    questions
                )
                db.commit()
                return True, ""
        except Exception as e:
            db.rollback()
            logger.error(f"Database error: {str(e)}")
            return False, str(e)
        finally:
            if db.is_connected():
                db.close()

class QuizGenerator:
    _last_request_time = 0
    
    def __init__(self):
        self.api_url = "http://localhost:11434/api/generate"
        self.model = "mistral"
        self.timeout = 180
        self.max_questions = 20
        self.min_request_interval = 1

    def generate_questions(self, prompt_data):
        try:
            if not prompt_data.get('topics'):
                raise ValueError("At least one topic is required")
                
            question_type = prompt_data.get('type', 'multiple choice').lower()
            num_questions = min(int(prompt_data.get('num_questions', 1)), self.max_questions)
            difficulty = prompt_data.get('difficulty', 'medium').lower()

            current_time = time.time()
            elapsed = current_time - self._last_request_time
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)
            self._last_request_time = time.time()

            prompt = f"""Generate exactly {num_questions} {difficulty} difficulty {question_type} questions about {', '.join(prompt_data['topics'])}.
            
            Format each question as follows:
            1. Question text?
            ||CorrectAnswer
            
            For multiple choice, include options like:
            1. Question text?
            A) Option 1
            B) Option 2
            C) Option 3
            D) Option 4
            ||CorrectLetter
            
            Return ONLY the questions in this format, one per line.
            Do NOT include any additional text or explanations."""

            logger.debug(f"Sending request to API: {self.api_url}")
            logger.debug(f"Request prompt: {prompt}")
            
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7}
                },
                timeout=self.timeout
            )
            
            print(f"Raw API response status code: {response.status_code}")
            print(f"Raw API response content: {response.text[:500]}...")
            
            response.raise_for_status()
            
            response_data = response.json()
            print(f"API response type: {type(response_data)}")
            print(f"API response keys: {response_data.keys() if isinstance(response_data, dict) else 'Not a dict'}")
            
            generated_text = ""
            if isinstance(response_data, dict):
                generated_text = response_data.get("response", "")
                if not isinstance(generated_text, str):
                    print(f"Warning: Response is not a string but a {type(generated_text)}")
                    generated_text = str(generated_text)
            else:
                print(f"Warning: Response is not a dictionary but a {type(response_data)}")
                generated_text = str(response_data)
            
            logger.debug(f"Extracted generated text (first 200 chars):\n{generated_text[:200]}...")
            print(f"Full generated text:\n{generated_text}")
            
            questions = []
            question_blocks = []
            
            if '1.' in generated_text:
                import re
                question_blocks = re.split(r'\n\s*\d+\.', generated_text)
                question_blocks = [block.strip() for block in question_blocks if block.strip()]
                if question_blocks and not question_blocks[0].startswith('1.'):
                    question_blocks.pop(0) if not '||' in question_blocks[0] else None
            else:
                question_blocks = [block.strip() for block in generated_text.split('\n\n') if block.strip()]
            
            print(f"Found {len(question_blocks)} potential question blocks")
            
            for block in question_blocks:
                if '||' in block:
                    parts = block.split('||', 1)
                    question_text = parts[0].strip()
                    answer_text = parts[1].strip()
                    
                    # Check for invalid content
                    if '[object Object]' in question_text or '[object Object]' in answer_text:
                        print(f"Skipping invalid block with [object Object]: {block[:100]}...")
                        continue
                    if not question_text or not answer_text:
                        print(f"Skipping empty question/answer in block: {block[:100]}...")
                        continue
                    
                    questions.append((question_text, answer_text))
                    print(f"Parsed question: {question_text[:50]}... Answer: {answer_text}")
                else:
                    print(f"Skipping block without delimiter: {block[:50]}...")
            
            if not questions:
                print("Trying line-by-line parsing")
                current_question = []
                for line in generated_text.split('\n'):
                    line = line.strip()
                    if '||' in line:
                        parts = line.split('||', 1)
                        question_part = parts[0].strip()
                        answer_part = parts[1].strip()
                        if question_part:
                            current_question.append(question_part)
                        if current_question:
                            question_text = '\n'.join(current_question)
                            questions.append((question_text, answer_part))
                            current_question = []
                    else:
                        if line and line[0].isdigit() and '. ' in line and current_question:
                            current_question = [line]
                        elif line:
                            current_question.append(line)
                if current_question:
                    print(f"Unprocessed lines: {current_question}")
            
            if not questions:
                raise ValueError("No valid questions found in response")
                
            print(f"Successfully parsed {len(questions)} questions")
            return questions[:num_questions], None
            
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}", exc_info=True)
            return None, str(e)

# Create instance of QuizGenerator
quiz_generator = QuizGenerator()

def generate_quiz(subject, num_questions, difficulty):
    """Adapter function to bridge the old and new quiz generation logic"""
    prompt_data = {
        'topics': [subject],
        'num_questions': num_questions,
        'difficulty': difficulty,
        'type': 'multiple choice'
    }
    
    questions_tuples, error = quiz_generator.generate_questions(prompt_data)
    
    if error or not questions_tuples:
        logger.error(f"Quiz generation failed: {error}")
        return []
    
    # Convert to format expected by the original application
    formatted_questions = []
    for question_text, answer in questions_tuples:
        # Extract options for multiple choice questions
        options = []
        
        # Parse options from question text if it's multiple choice
        lines = question_text.split('\n')
        
        # Filter out the first line (the question itself)
        option_lines = [line for line in lines[1:] if line.strip()]
        
        # Extract options if they exist
        if option_lines and any(line.startswith(('A)', 'B)', 'C)', 'D)')) for line in option_lines):
            for line in option_lines:
                if line.strip() and any(line.startswith(prefix) for prefix in ['A)', 'B)', 'C)', 'D)']):
                    options.append(line[2:].strip())  # Remove option letter and parenthesis
        
        # If we couldn't parse options properly, create dummy options
        if not options and answer.upper() in ['A', 'B', 'C', 'D']:
            options = ["Option A", "Option B", "Option C", "Option D"]
        
        # Create the question object
        question = {
            'question': lines[0] if lines else question_text,
            'options': options,
            'correct_answer': answer
        }
        
        formatted_questions.append(question)
    
    return formatted_questions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'student')
        
        user = User.query.filter_by(email=email, user_type=role).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            session['name'] = user.name
            flash('Login successful!', 'success')
            return redirect(url_for('teacher_dashboard' if user.user_type == 'teacher' else 'student_dashboard'))
        else:
            flash('Invalid email/password or account type', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/teacher-dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session['user_type'] != 'teacher':
        return redirect(url_for('login'))
    
    teacher_id = session['user_id']
    quizzes = Quiz.query.filter_by(teacher_id=teacher_id).all()
    classrooms = Classroom.query.filter_by(teacher_id=teacher_id).all()
    
    return render_template('teacher_dashboard.html', quizzes=quizzes, classrooms=classrooms)

@app.route('/student-dashboard')
def student_dashboard():
    if 'user_id' not in session or session['user_type'] != 'student':
        return redirect(url_for('login'))
    
    student_id = session['user_id']
    student = User.query.get(student_id)  # Changed from Student.query to User.query
    
    available_quizzes = []
    completed_quizzes = []
    avg_score = 0
    
    # Get classrooms the student belongs to
    for classroom in student.enrolled_classrooms:
        for quiz in classroom.quizzes:
            # Check if student has completed this quiz
            result = QuizResult.query.filter_by(
                user_id=student.id,
                quiz_id=quiz.id
            ).first()
            
            if result:
                completed_quizzes.append({
                    'quiz': quiz,
                    'result': result
                })
            else:
                available_quizzes.append(quiz)
    
    # Calculate average score if there are completed quizzes
    if completed_quizzes:
        total = sum(result['result'].score for result in completed_quizzes)
        avg_score = round(total / len(completed_quizzes), 2)
    
    return render_template('student_dashboard.html',
                         available_quizzes=available_quizzes,
                         completed_quizzes=completed_quizzes,
                         avg_score=avg_score)

@app.route('/quizzes')
def quizzes():
    if 'user_id' not in session or session['user_type'] != 'teacher':
        return redirect(url_for('login'))
    
    teacher_id = session['user_id']
    quizzes = Quiz.query.filter_by(teacher_id=teacher_id).all()
    
    return render_template('quizzes.html', quizzes=quizzes)

@app.route('/classrooms')
def classrooms():
    if 'user_id' not in session or session['user_type'] != 'teacher':
        return redirect(url_for('login'))
    
    teacher_id = session['user_id']
    classrooms = Classroom.query.filter_by(teacher_id=teacher_id).all()
    
    return render_template('classrooms.html', classrooms=classrooms)

@app.route('/create-quiz', methods=['GET', 'POST'])
def create_quiz():
    if 'user_id' not in session or session['user_type'] != 'teacher':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        
        new_quiz = Quiz(
            title=title,
            description=description,
            teacher_id=session['user_id']
        )
        
        db.session.add(new_quiz)
        db.session.commit()
        
        # Handle questions creation here
        # We'll extract questions from the form
        questions_data = []
        i = 1
        while f'question_{i}' in request.form:
            question_text = request.form[f'question_{i}']
            options = []
            
            # Get options if they exist
            j = 1
            while f'option_{i}_{j}' in request.form:
                options.append(request.form[f'option_{i}_{j}'])
                j += 1
            
            correct_answer = request.form.get(f'correct_{i}', '')
            
            # Create a new question
            question = Question(
                quiz_id=new_quiz.id,
                text=question_text,
                options=",".join(options) if options else "",
                correct_answer=correct_answer
            )
            
            db.session.add(question)
            i += 1
        
        db.session.commit()
        flash('Quiz created successfully!')
        return redirect(url_for('quizzes'))
    
    return render_template('create_quiz.html')

@app.route('/ai-generate-quiz', methods=['GET', 'POST'])
def ai_generate_quiz():
    if 'user_id' not in session or session['user_type'] != 'teacher':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        subject = request.form['subject']
        num_questions = int(request.form['num_questions'])
        difficulty = request.form['difficulty']
        
        # Call AI quiz generation function
        questions = generate_quiz(subject, num_questions, difficulty)
        
        if not questions:
            flash('Failed to generate quiz. Please try again.')
            return redirect(url_for('ai_generate_quiz'))
        
        new_quiz = Quiz(
            title=f"{subject} Quiz",
            description=f"AI-generated quiz about {subject}",
            teacher_id=session['user_id']
        )
        
        db.session.add(new_quiz)
        db.session.commit()
        
        # Add AI generated questions to the quiz
        for q in questions:
            question = Question(
                quiz_id=new_quiz.id,
                text=q['question'],
                options=",".join(q['options']),
                correct_answer=q['correct_answer']
            )
            db.session.add(question)
        
        db.session.commit()
        flash('AI-generated quiz created successfully!')
        return redirect(url_for('quizzes'))
    
    return render_template('create_quiz.html', ai_generate=True)

@app.route('/assign-quiz/<int:quiz_id>', methods=['POST'])
def assign_quiz(quiz_id):
    if 'user_id' not in session or session['user_type'] != 'teacher':
        return redirect(url_for('login'))
    
    # Logic to assign quiz to classroom
    classroom_id = request.form['classroom_id']
    
    # Verify both quiz and classroom exist and belong to this teacher
    quiz = Quiz.query.get(quiz_id)
    classroom = Classroom.query.get(classroom_id)
    
    if not quiz or not classroom or quiz.teacher_id != session['user_id'] or classroom.teacher_id != session['user_id']:
        flash('Invalid quiz or classroom')
        return redirect(url_for('quizzes'))
    
    # Add the quiz to the classroom
    # This assumes there's a many-to-many relationship between Quiz and Classroom
    # If your model is different, adjust this code accordingly
    if classroom not in quiz.classrooms:
        quiz.classrooms.append(classroom)
        db.session.commit()
        flash(f'Quiz "{quiz.title}" has been assigned to classroom "{classroom.name}"')
    else:
        flash(f'Quiz is already assigned to this classroom')
    
    return redirect(url_for('quizzes'))

@app.route("/api/generate-quiz-api", methods=["POST"])
def generate_quiz_api():
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
            
        data = request.get_json()
        logger.debug(f"Received request data: {data}")
        
        if not data.get('topics'):
            return jsonify({"error": "At least one topic required"}), 400

        questions, error = quiz_generator.generate_questions(data)
        if error:
            return jsonify({"error": error}), 400

        if not questions:
            return jsonify({"error": "No questions could be generated"}), 400

        db_questions = [
            (
                json.dumps(data['topics']),
                question,
                answer,
                data.get('type', 'multiple choice'),
                data.get('difficulty', 'medium')
            )
            for question, answer in questions
        ]

        success, db_error = DatabaseManager.save_questions(db_questions)
        
        response = {
            "success": True,
            "questions": [{"question": q, "answer": a} for q, a in questions],
            "count": len(questions)
        }
        
        # Debugging: Print final questions to check data
        print("\nFinal questions to be sent in response:")
        for idx, qa in enumerate(response["questions"]):
            print(f"Question {idx + 1}: {qa['question']}")
            print(f"Answer {idx + 1}: {qa['answer']}\n")
        
        if not success:
            response.update({
                "warning": "Questions generated but not saved",
                "db_error": db_error
            })
            return jsonify(response), 207
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# Add these routes before the if __name__ == '__main__' block

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            role = request.form.get('role', 'student')
            
            if not all([name, email, password]):
                flash('All fields are required')
                return redirect(url_for('signup'))

            if User.query.filter_by(email=email).first():
                flash('Email already exists')
                return redirect(url_for('signup'))
                
            new_user = User(
                name=name,
                email=email,
                user_type=role
            )
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Account created successfully! Please login')
            return redirect(url_for('login'))
        
        except Exception as e:
            db.session.rollback()
            flash('Error creating account')
            logger.error(f"Signup error: {str(e)}")
    
    return render_template('signup.html')

@app.route('/teacher-login')
def teacher_login():
    return render_template('login.html', role='teacher')

@app.route('/student-login')
def student_login():
    return render_template('login.html', role='student')

if __name__ == "__main__":
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        logger.warning(f"Missing environment variables: {', '.join(missing)}")
        logger.warning("Database connection for external storage may not work")
    
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('DEBUG', 'true').lower() == 'true'
    )