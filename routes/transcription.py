"""
Video Transcription API Routes
Provides API endpoints for video transcription and processing
"""
import os
import logging
import tempfile
from pathlib import Path

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from services.transcription_service import TranscriptionService
from services.vector_db_service import VectorDBService
from models import CourseContent, Course
from app import db

logger = logging.getLogger(__name__)

transcription_bp = Blueprint('transcription', __name__)
transcription_service = TranscriptionService()
vector_db_service = VectorDBService()

@transcription_bp.route('/api/transcription/process/<int:content_id>', methods=['POST'])
def process_video_content(content_id):
    """
    Process video content for transcription
    
    Args:
        content_id (int): The ID of the video content to process
        
    Returns:
        JSON response with result
    """
    try:
        # Process the video content
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
        logger.error(f"Error in process_video_content endpoint: {str(e)}")
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500

@transcription_bp.route('/api/transcription/upload', methods=['POST'])
def upload_video():
    """
    Upload a video file and add it as course content
    
    Returns:
        JSON response with result
    """
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
        # Note: In a production system, this would be done asynchronously
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

@transcription_bp.route('/api/transcription/batch-process/<int:course_id>', methods=['POST'])
def batch_process_videos(course_id):
    """
    Batch process all videos in a course
    
    Args:
        course_id (int): The ID of the course
        
    Returns:
        JSON response with result
    """
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