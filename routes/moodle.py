"""
Moodle Integration API Routes
Provides API endpoints for Moodle LMS integration
"""

import json
import logging
import requests
from flask import Blueprint, request, jsonify, current_app, abort
from models import db, User, Course, CourseContent, Quiz, QuizQuestion, QuizOption
from services.search_service import SearchService
from services.quiz_service import QuizService

# Create blueprint
moodle_bp = Blueprint('moodle', __name__)
logger = logging.getLogger(__name__)

# Initialize services
search_service = SearchService()
quiz_service = QuizService()

@moodle_bp.route('/config', methods=['GET'])
def get_moodle_config():
    """Return Moodle configuration for frontend integration"""
    try:
        # Get Moodle configuration from environment or app config
        moodle_config = {
            'baseUrl': current_app.config.get('MOODLE_BASE_URL', ''),
            'tokenAvailable': bool(current_app.config.get('MOODLE_API_TOKEN', ''))
        }
        
        return jsonify(moodle_config)
    except Exception as e:
        logger.error(f"Error getting Moodle config: {str(e)}")
        return jsonify({'error': 'Failed to get Moodle configuration'}), 500

@moodle_bp.route('/sync-course', methods=['POST'])
def sync_course():
    """Synchronize a Moodle course to the local database"""
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        course_id = data.get('course_id')
        content = data.get('content')
        
        if not course_id or not content:
            return jsonify({'error': 'Missing required parameters'}), 400
            
        # Check if course exists in our database
        course = Course.query.filter_by(moodle_course_id=course_id).first()
        
        if not course:
            # Get course details from Moodle
            course_details = get_course_details(course_id)
            
            if not course_details:
                return jsonify({'error': 'Failed to get course details from Moodle'}), 404
                
            # Create new course
            course = Course(
                moodle_course_id=course_id,
                title=course_details.get('fullname', f'Course {course_id}'),
                description=course_details.get('summary', '')
            )
            db.session.add(course)
            db.session.commit()
        
        # Process and store course content
        content_items_created = process_course_content(course.id, content)
        
        # Index content for search
        for content_item in CourseContent.query.filter_by(course_id=course.id).all():
            search_service.index_content(content_item.id)
            
        return jsonify({
            'success': True,
            'course_id': course.id,
            'moodle_course_id': course.moodle_course_id,
            'content_items_created': content_items_created
        })
            
    except Exception as e:
        logger.error(f"Error syncing course: {str(e)}")
        return jsonify({'error': f'Failed to sync course: {str(e)}'}), 500

@moodle_bp.route('/user-courses/<int:user_id>', methods=['GET'])
def get_user_courses(user_id):
    """Get courses for a specific user"""
    try:
        # Check if user exists
        user = User.query.filter_by(moodle_user_id=user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Call Moodle API to get user courses
        courses = call_moodle_api('core_enrol_get_users_courses', {'userid': user_id})
        
        if not courses:
            return jsonify([])
            
        return jsonify(courses)
        
    except Exception as e:
        logger.error(f"Error getting user courses: {str(e)}")
        return jsonify({'error': f'Failed to get user courses: {str(e)}'}), 500

@moodle_bp.route('/generate-quiz-from-course/<int:course_id>', methods=['POST'])
def generate_quiz_from_course(course_id):
    """Generate a quiz from Moodle course content"""
    try:
        data = request.json or {}
        num_questions = data.get('num_questions', 5)
        title = data.get('title', 'Generated Quiz')
        description = data.get('description', 'Automatically generated quiz')
        
        # Get course content
        course = Course.query.filter_by(id=course_id).first()
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
            
        # Get all course content text
        content_items = CourseContent.query.filter_by(course_id=course.id).all()
        combined_content = ' '.join([item.content_text for item in content_items if item.content_text])
        
        if not combined_content:
            return jsonify({'error': 'No content available for quiz generation'}), 400
            
        # Create quiz
        quiz = quiz_service.create_quiz(course_id, title, description)
        
        if not quiz:
            return jsonify({'error': 'Failed to create quiz'}), 500
            
        # Generate questions using OpenAI service - this requires content text directly
        questions = quiz_service.openai_service.generate_quiz(combined_content, num_questions)
        
        # Add questions to the quiz
        question_count = 0
        for q_data in questions:
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_text=q_data['question'],
                question_type='multiple_choice'
            )
            db.session.add(question)
            db.session.flush()
            
            # Add options
            for i, option_text in enumerate(q_data['options']):
                option = QuizOption(
                    question_id=question.id,
                    option_text=option_text,
                    is_correct=(i == q_data['correct_index'])
                )
                db.session.add(option)
            
            question_count += 1
        
        db.session.commit()
        result = {"questions": questions}
        
        return jsonify({
            'quiz_id': quiz.id,
            'title': quiz.title,
            'questions_created': len(result.get('questions', [])),
            'message': 'Quiz generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        return jsonify({'error': f'Failed to generate quiz: {str(e)}'}), 500

# Helper functions

def call_moodle_api(function, params=None):
    """Call Moodle API with the given function and parameters"""
    try:
        base_url = current_app.config.get('MOODLE_BASE_URL')
        token = current_app.config.get('MOODLE_API_TOKEN')
        
        if not base_url or not token:
            logger.error("Moodle API credentials not configured")
            return None
            
        api_url = f"{base_url}/webservice/rest/server.php"
        
        # Build request parameters
        request_params = {
            'wstoken': token,
            'wsfunction': function,
            'moodlewsrestformat': 'json'
        }
        
        # Add additional parameters
        if params:
            request_params.update(params)
            
        # Make request to Moodle API
        response = requests.get(api_url, params=request_params)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for Moodle exception
        if isinstance(data, dict) and data.get('exception'):
            logger.error(f"Moodle API error: {data.get('message')}")
            return None
            
        return data
        
    except Exception as e:
        logger.error(f"Error calling Moodle API: {str(e)}")
        return None

def get_course_details(course_id):
    """Get course details from Moodle"""
    try:
        courses = call_moodle_api('core_course_get_courses', {'options': {'ids': [course_id]}})
        
        if not courses or not isinstance(courses, list) or len(courses) == 0:
            return None
            
        return courses[0]
        
    except Exception as e:
        logger.error(f"Error getting course details: {str(e)}")
        return None

def process_course_content(course_id, content):
    """Process and store course content from Moodle"""
    try:
        items_created = 0
        
        # Iterate through sections
        for section in content:
            if not section.get('modules'):
                continue
                
            # Process modules in this section
            for module in section['modules']:
                module_name = module.get('name', '')
                module_type = module.get('modname', 'unknown')
                module_url = module.get('url', '')
                
                # Extract content text
                content_text = module_name
                
                if module.get('description'):
                    content_text += ' ' + module['description']
                    
                # Check if content already exists
                existing_content = CourseContent.query.filter_by(
                    course_id=course_id,
                    title=module_name,
                    content_type=module_type
                ).first()
                
                if existing_content:
                    # Update existing content
                    existing_content.content_text = content_text
                    existing_content.url = module_url
                else:
                    # Create new content item
                    content_item = CourseContent(
                        course_id=course_id,
                        title=module_name,
                        content_type=module_type,
                        content_text=content_text,
                        url=module_url
                    )
                    db.session.add(content_item)
                    items_created += 1
                    
        # Commit changes
        db.session.commit()
        return items_created
        
    except Exception as e:
        logger.error(f"Error processing course content: {str(e)}")
        db.session.rollback()
        raise e