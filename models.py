from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Association Tables
student_classroom = db.Table('student_classroom',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('classroom_id', db.Integer, db.ForeignKey('classroom.id'), primary_key=True)
)

quiz_classroom = db.Table('quiz_classroom',
    db.Column('quiz_id', db.Integer, db.ForeignKey('quiz.id'), primary_key=True),
    db.Column('classroom_id', db.Integer, db.ForeignKey('classroom.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    user_type = db.Column(db.String(10), nullable=False)  # 'teacher' or 'student'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    quizzes = db.relationship('Quiz', backref='teacher', lazy=True)
    classrooms = db.relationship('Classroom', backref='teacher', lazy=True)
    quiz_results = db.relationship('QuizResult', backref='student', lazy=True)
    enrolled_classrooms = db.relationship('Classroom', 
        secondary=student_classroom,
        backref=db.backref('students', lazy='dynamic')
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)  # Fixed missing parenthesis

class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    difficulty = db.Column(db.String(20), default='medium')
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    questions = db.relationship('Question', backref='quiz', lazy=True)
    assigned_classrooms = db.relationship('Classroom',
        secondary=quiz_classroom,
        backref=db.backref('quizzes', lazy='dynamic')
    )

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text)  # Comma-separated
    correct_answer = db.Column(db.String(100), nullable=False)

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    completed_date = db.Column(db.DateTime, default=datetime.utcnow)