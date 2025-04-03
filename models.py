from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    # Moodle user ID for integration
    moodle_user_id = db.Column(db.Integer, unique=True)
    chat_sessions = db.relationship('ChatSession', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    moodle_course_id = db.Column(db.Integer, unique=True, nullable=False)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    content = db.relationship('CourseContent', backref='course', lazy='dynamic')
    
    def __repr__(self):
        return f'<Course {self.title}>'

class CourseContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(256), nullable=False)
    content_type = db.Column(db.String(50))  # document, video, quiz, etc.
    content_text = db.Column(db.Text)
    url = db.Column(db.String(512))
    
    def __repr__(self):
        return f'<CourseContent {self.title}>'

class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('ChatMessage', backref='session', lazy='dynamic')
    
    def __repr__(self):
        return f'<ChatSession {self.id} for User {self.user_id}>'

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    is_user = db.Column(db.Boolean, default=True)  # True if from user, False if from AI
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ChatMessage {self.id} from {"User" if self.is_user else "AI"}>'

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    questions = db.relationship('QuizQuestion', backref='quiz', lazy='dynamic')
    
    def __repr__(self):
        return f'<Quiz {self.title}>'

class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), default='multiple_choice')
    options = db.relationship('QuizOption', backref='question', lazy='dynamic')
    
    def __repr__(self):
        return f'<QuizQuestion {self.id}>'

class QuizOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_question.id'), nullable=False)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<QuizOption {self.id}>'

class SearchIndex(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.Integer, db.ForeignKey('course_content.id'), nullable=False)
    indexed_text = db.Column(db.Text, nullable=False)
    
    def __repr__(self):
        return f'<SearchIndex {self.id}>'
