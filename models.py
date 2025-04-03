from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Many-to-many relationship table for students and classrooms
student_classroom = db.Table('student_classroom',
    db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True),
    db.Column('classroom_id', db.Integer, db.ForeignKey('classroom.id'), primary_key=True)
)

# Many-to-many relationship table for quizzes and classrooms
quiz_classroom = db.Table('quiz_classroom',
    db.Column('quiz_id', db.Integer, db.ForeignKey('quiz.id'), primary_key=True),
    db.Column('classroom_id', db.Integer, db.ForeignKey('classroom.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(10), nullable=False)  # 'teacher' or 'student'
    
class Teacher(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    quizzes = db.relationship('Quiz', backref='teacher', lazy=True)
    classrooms = db.relationship('Classroom', backref='teacher', lazy=True)

class Student(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    quiz_results = db.relationship('QuizResult', backref='student', lazy=True)
    # Add many-to-many relationship with classrooms
    classrooms = db.relationship('Classroom', secondary=student_classroom, 
                             backref=db.backref('students', lazy='dynamic'))

class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    # Add many-to-many relationship with quizzes
    quizzes = db.relationship('Quiz', secondary=quiz_classroom,
                          backref=db.backref('classrooms', lazy='dynamic'))

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    questions = db.relationship('Question', backref='quiz', lazy=True)
    difficulty = db.Column(db.String(20), default='medium')
    
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=False)  # Comma-separated options
    correct_answer = db.Column(db.String(100), nullable=False)

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    completed_date = db.Column(db.DateTime, default=datetime.utcnow)
    quiz = db.relationship('Quiz', backref='results')