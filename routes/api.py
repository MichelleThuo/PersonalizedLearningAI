import json
import logging
import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from models import ChatSession, ChatMessage, Course, CourseContent
from services.openai_service import OpenAIService
from services.search_service import SearchService
from services.quiz_service import QuizService
from services.recommendation_service import RecommendationService
from services.transcription_service import TranscriptionService
from services.vector_db_service import VectorDBService
from app import db

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)
openai_service = OpenAIService()
search_service = SearchService()
quiz_service = QuizService()
recommendation_service = RecommendationService()
transcription_service = TranscriptionService()
vector_db_service = VectorDBService()

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

@api_bp.route('/recommendations/<int:user_id>', methods=['GET'])
def get_recommendations(user_id):
    """API endpoint for getting personalized course recommendations"""
    try:
        limit = request.args.get('limit', 5, type=int)
        
        # Get recommendations for the user
        recommendations = recommendation_service.get_recommendations_for_user(user_id, limit)
        
        return jsonify({
            'user_id': user_id,
            'recommendations': recommendations
        })
        
    except Exception as e:
        logger.error(f"Error in get_recommendations endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred retrieving recommendations'}), 500

@api_bp.route('/learning-path', methods=['POST'])
def generate_learning_path():
    """API endpoint for generating a progressive learning path"""
    try:
        data = request.json
        user_id = data.get('user_id')
        topic = data.get('topic')
        difficulty = data.get('difficulty', 'beginner')
        
        if not user_id or not topic:
            return jsonify({'error': 'User ID and topic are required'}), 400
        
        # Generate learning path
        learning_path = recommendation_service.generate_learning_path(user_id, topic, difficulty)
        
        if 'error' in learning_path:
            return jsonify({'error': learning_path['error']}), 500
        
        return jsonify({
            'learning_path': learning_path
        })
        
    except Exception as e:
        logger.error(f"Error in generate_learning_path endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred generating the learning path'}), 500

@api_bp.route('/videos', methods=['GET'])
def get_videos():
    """API endpoint for getting video content"""
    try:
        course_id = request.args.get('course_id')
        
        # Filter videos by course if course_id is provided
        if course_id:
            try:
                course_id = int(course_id)
                videos = CourseContent.query.filter_by(
                    course_id=course_id,
                    content_type='video'
                ).all()
            except ValueError:
                return jsonify({'error': 'Invalid course ID'}), 400
        else:
            videos = CourseContent.query.filter_by(content_type='video').all()
        
        # Format video data for frontend
        video_list = []
        for video in videos:
            course = Course.query.get(video.course_id)
            video_list.append({
                'id': video.id,
                'title': video.title,
                'url': video.url,
                'course_id': video.course_id,
                'course_title': course.title if course else 'Unknown Course',
                'has_transcript': bool(video.content_text)
            })
        
        return jsonify({
            'videos': video_list
        })
        
    except Exception as e:
        logger.error(f"Error in get_videos endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred retrieving videos'}), 500

@api_bp.route('/content/<int:content_id>', methods=['GET'])
def get_content(content_id):
    """API endpoint for getting specific content details"""
    try:
        content = CourseContent.query.get(content_id)
        if not content:
            return jsonify({'error': 'Content not found'}), 404
        
        course = Course.query.get(content.course_id)
        
        content_data = {
            'id': content.id,
            'title': content.title,
            'content_type': content.content_type,
            'course_id': content.course_id,
            'course_title': course.title if course else 'Unknown Course',
            'url': content.url,
            'content_text': content.content_text
        }
        
        return jsonify({
            'status': 'success',
            'content': content_data
        })
        
    except Exception as e:
        logger.error(f"Error in get_content endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred retrieving content'}), 500

@api_bp.route('/transcription/upload', methods=['POST'])
def upload_video():
    """API endpoint for uploading and processing a video file"""
    try:
        if 'video_file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No video file provided'}), 400
        
        video_file = request.files['video_file']
        course_id = request.form.get('course_id')
        title = request.form.get('title')
        
        if not video_file.filename:
            return jsonify({'status': 'error', 'message': 'Empty file submitted'}), 400
        
        if not course_id or not title:
            return jsonify({'status': 'error', 'message': 'Course ID and title are required'}), 400
        
        # Validate course exists
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'status': 'error', 'message': 'Course not found'}), 404
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'videos')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Secure filename and save the file
        filename = secure_filename(video_file.filename)
        file_path = os.path.join(upload_dir, filename)
        video_file.save(file_path)
        
        # Create database entry for the video
        video_content = CourseContent(
            course_id=course_id,
            title=title,
            content_type='video',
            url=os.path.join('static', 'uploads', 'videos', filename)
        )
        db.session.add(video_content)
        db.session.commit()
        
        # Process the video (transcription) in the background
        # For now, we'll process immediately, but this could be moved to a background task
        success = transcription_service.process_video_content(video_content.id)
        
        if success:
            # Index the transcribed content in the vector database
            vector_db_service.index_content(video_content.id)
            return jsonify({
                'status': 'success',
                'message': 'Video uploaded and processed successfully',
                'content_id': video_content.id
            })
        else:
            return jsonify({
                'status': 'partial',
                'message': 'Video uploaded but transcription failed. You can retry processing later.',
                'content_id': video_content.id
            })
        
    except Exception as e:
        logger.error(f"Error in upload_video endpoint: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500

@api_bp.route('/transcription/process/<int:content_id>', methods=['POST'])
def process_video(content_id):
    """API endpoint for processing an existing video"""
    try:
        content = CourseContent.query.get(content_id)
        if not content:
            return jsonify({'status': 'error', 'message': 'Content not found'}), 404
        
        if content.content_type != 'video':
            return jsonify({'status': 'error', 'message': 'Content is not a video'}), 400
        
        # Process the video
        success = transcription_service.process_video_content(content_id)
        
        if success:
            # Index the transcribed content in the vector database
            vector_db_service.index_content(content_id)
            return jsonify({
                'status': 'success',
                'message': 'Video processed successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to process video'
            }), 500
        
    except Exception as e:
        logger.error(f"Error in process_video endpoint: {str(e)}")
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500

@api_bp.route('/transcription/batch-process/<int:course_id>', methods=['POST'])
def batch_process_videos(course_id):
    """API endpoint for batch processing all videos in a course"""
    try:
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'status': 'error', 'message': 'Course not found'}), 404
        
        # Get all videos for the course
        videos = CourseContent.query.filter_by(
            course_id=course_id,
            content_type='video'
        ).all()
        
        if not videos:
            return jsonify({'status': 'error', 'message': 'No videos found for this course'}), 404
        
        # Process each video
        processed = 0
        for video in videos:
            if transcription_service.process_video_content(video.id):
                vector_db_service.index_content(video.id)
                processed += 1
        
        if processed == len(videos):
            return jsonify({
                'status': 'success',
                'message': f'All {processed} videos processed successfully'
            })
        elif processed > 0:
            return jsonify({
                'status': 'partial',
                'message': f'Processed {processed} out of {len(videos)} videos'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to process any videos'
            }), 500
        
    except Exception as e:
        logger.error(f"Error in batch_process_videos endpoint: {str(e)}")
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500
