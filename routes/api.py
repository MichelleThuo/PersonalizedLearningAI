import json
import logging
from flask import Blueprint, request, jsonify, current_app
from models import ChatSession, ChatMessage, Course, CourseContent
from services.openai_service import OpenAIService
from services.search_service import SearchService
from services.quiz_service import QuizService
from app import db

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)
openai_service = OpenAIService()
search_service = SearchService()
quiz_service = QuizService()

@api_bp.route('/chat', methods=['POST'])
def chat():
    """API endpoint for chatbot interactions"""
    try:
        data = request.json
        message = data.get('message')
        session_id = data.get('session_id')
        user_id = data.get('user_id')  # For tracking the conversation
        course_id = data.get('course_id')  # Optional, to provide course context
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get or create chat session
        session = None
        if session_id:
            session = ChatSession.query.get(session_id)
        
        if not session and user_id:
            # Create a new session
            session = ChatSession(user_id=user_id, course_id=course_id)
            db.session.add(session)
            db.session.flush()
        
        if not session:
            return jsonify({'error': 'Could not create or find chat session'}), 400
        
        # Save user message
        user_message = ChatMessage(
            session_id=session.id,
            is_user=True,
            message=message
        )
        db.session.add(user_message)
        
        # Get conversation history (last 10 messages)
        history = ChatMessage.query.filter_by(session_id=session.id).order_by(
            ChatMessage.timestamp.desc()
        ).limit(10).all()
        
        history.reverse()  # Get in chronological order
        
        # Format messages for OpenAI
        formatted_messages = []
        for msg in history:
            role = "user" if msg.is_user else "assistant"
            formatted_messages.append({
                "role": role,
                "content": msg.message
            })
        
        # Add the current message if not in history
        if not history or history[-1].message != message:
            formatted_messages.append({
                "role": "user",
                "content": message
            })
        
        # Get course context if available
        context = None
        if course_id:
            # Get relevant course content for context
            course_context = search_service.get_relevant_content(message, course_id)
            if course_context:
                context = course_context
        
        # Get response from OpenAI
        ai_response = openai_service.get_chat_response(formatted_messages, context)
        
        # Save AI response
        ai_message = ChatMessage(
            session_id=session.id,
            is_user=False,
            message=ai_response
        )
        db.session.add(ai_message)
        db.session.commit()
        
        return jsonify({
            'response': ai_response,
            'session_id': session.id
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'An error occurred processing your request'}), 500

@api_bp.route('/search', methods=['GET'])
def search():
    """API endpoint for searching course content"""
    try:
        query = request.args.get('q')
        course_id = request.args.get('course_id')
        
        if not query:
            return jsonify({'error': 'No search query provided'}), 400
        
        # Convert course_id to int if provided
        if course_id:
            try:
                course_id = int(course_id)
            except ValueError:
                return jsonify({'error': 'Invalid course ID'}), 400
        
        # Search for relevant content
        results = search_service.search(query, course_id)
        
        # Format results
        formatted_results = []
        for content in results:
            formatted_results.append({
                'id': content.id,
                'title': content.title,
                'content_type': content.content_type,
                'course_id': content.course_id,
                'url': content.url,
                'snippet': (content.content_text[:200] + '...') if content.content_text and len(content.content_text) > 200 else content.content_text
            })
        
        return jsonify({
            'query': query,
            'results': formatted_results
        })
        
    except Exception as e:
        logger.error(f"Error in search endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred processing your search'}), 500

@api_bp.route('/quiz/generate', methods=['POST'])
def generate_quiz():
    """API endpoint for generating quizzes based on course content"""
    try:
        data = request.json
        course_id = data.get('course_id')
        title = data.get('title')
        description = data.get('description')
        content_ids = data.get('content_ids', [])
        
        if not course_id or not title:
            return jsonify({'error': 'Course ID and title are required'}), 400
        
        # Create the quiz
        quiz = quiz_service.create_quiz(course_id, title, description, content_ids)
        
        if not quiz:
            return jsonify({'error': 'Failed to create quiz'}), 500
        
        # Get the complete quiz data
        quiz_data = quiz_service.get_quiz(quiz.id)
        
        return jsonify({
            'quiz': quiz_data
        })
        
    except Exception as e:
        logger.error(f"Error in generate_quiz endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred generating the quiz'}), 500

@api_bp.route('/quiz/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    """API endpoint for getting quiz data"""
    try:
        quiz_data = quiz_service.get_quiz(quiz_id)
        
        if not quiz_data:
            return jsonify({'error': 'Quiz not found'}), 404
        
        return jsonify({
            'quiz': quiz_data
        })
        
    except Exception as e:
        logger.error(f"Error in get_quiz endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred retrieving the quiz'}), 500

@api_bp.route('/quiz/evaluate', methods=['POST'])
def evaluate_quiz():
    """API endpoint for evaluating quiz attempts"""
    try:
        data = request.json
        quiz_id = data.get('quiz_id')
        answers = data.get('answers', {})
        
        if not quiz_id or not answers:
            return jsonify({'error': 'Quiz ID and answers are required'}), 400
        
        # Evaluate the quiz attempt
        results = quiz_service.evaluate_quiz_attempt(quiz_id, answers)
        
        if not results:
            return jsonify({'error': 'Failed to evaluate quiz attempt'}), 500
        
        return jsonify({
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in evaluate_quiz endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred evaluating the quiz'}), 500

@api_bp.route('/courses', methods=['GET'])
def get_courses():
    """API endpoint for getting available courses"""
    try:
        courses = Course.query.all()
        
        course_list = []
        for course in courses:
            course_list.append({
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'moodle_course_id': course.moodle_course_id
            })
        
        return jsonify({
            'courses': course_list
        })
        
    except Exception as e:
        logger.error(f"Error in get_courses endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred retrieving courses'}), 500

@api_bp.route('/course/<int:course_id>/contents', methods=['GET'])
def get_course_contents(course_id):
    """API endpoint for getting course content"""
    try:
        contents = CourseContent.query.filter_by(course_id=course_id).all()
        
        content_list = []
        for content in contents:
            content_list.append({
                'id': content.id,
                'title': content.title,
                'content_type': content.content_type,
                'url': content.url
            })
        
        return jsonify({
            'course_id': course_id,
            'contents': content_list
        })
        
    except Exception as e:
        logger.error(f"Error in get_course_contents endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred retrieving course contents'}), 500
