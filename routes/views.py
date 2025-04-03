from flask import Blueprint, render_template, request, redirect, url_for
from models import Course, CourseContent, Quiz

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    """Main page with overview of features"""
    courses = Course.query.all()
    return render_template('index.html', courses=courses)

@views_bp.route('/chat')
def chat():
    """Chat interface page"""
    course_id = request.args.get('course_id')
    user_id = request.args.get('user_id', 1)  # Default to user 1 for demonstration
    
    course = None
    if course_id:
        course = Course.query.get(course_id)
    
    courses = Course.query.all()
    
    return render_template('chat.html', 
                          course=course, 
                          courses=courses, 
                          user_id=user_id)

@views_bp.route('/search')
def search():
    """Search interface page"""
    query = request.args.get('q', '')
    course_id = request.args.get('course_id')
    
    courses = Course.query.all()
    course = None
    if course_id:
        course = Course.query.get(course_id)
    
    return render_template('search.html', 
                          query=query, 
                          course=course, 
                          courses=courses)

@views_bp.route('/quiz')
def quiz_list():
    """Quiz list page"""
    course_id = request.args.get('course_id')
    
    quizzes = []
    course = None
    
    if course_id:
        quizzes = Quiz.query.filter_by(course_id=course_id).all()
        course = Course.query.get(course_id)
    else:
        quizzes = Quiz.query.all()
    
    courses = Course.query.all()
    
    return render_template('quiz.html', 
                          quizzes=quizzes,
                          course=course,
                          courses=courses)

@views_bp.route('/quiz/<int:quiz_id>')
def quiz_detail(quiz_id):
    """Quiz detail page"""
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('quiz.html', 
                          quiz=quiz,
                          course=quiz.course,
                          quiz_view=True)

@views_bp.route('/h5p')
def h5p_generator():
    """H5P content generation page"""
    course_id = request.args.get('course_id')
    
    courses = Course.query.all()
    course = None
    if course_id:
        course = Course.query.get(course_id)
    
    return render_template('h5p.html',
                          course=course,
                          courses=courses)

@views_bp.route('/video')
def video_manager():
    """Video content manager page"""
    course_id = request.args.get('course_id')
    
    courses = Course.query.all()
    course = None
    
    # Get videos filtered by course if course_id is provided
    videos = []
    if course_id:
        course = Course.query.get(course_id)
        videos = CourseContent.query.filter_by(
            course_id=course_id,
            content_type='video'
        ).all()
    else:
        videos = CourseContent.query.filter_by(content_type='video').all()
    
    return render_template('video.html',
                          course=course,
                          courses=courses,
                          videos=videos)
