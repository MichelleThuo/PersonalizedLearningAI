"""
Video Transcription API Routes
Provides API endpoints for video transcription and processing
"""
import os
import logging
import tempfile
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from services.transcription_service import TranscriptionService
from services.vector_db_service import VectorDBService
from models import CourseContent, Course
from app import db

transcription_bp = Blueprint('transcription', __name__)
transcription_service = TranscriptionService()
vector_db_service = VectorDBService()

@transcription_bp.route('/process/<int:content_id>', methods=['POST'])
def process_video_content(content_id):
    """
    Process video content for transcription
    
    Args:
        content_id (int): The ID of the video content to process
        
    Returns:
        JSON response with result
    """
    try:
        # Check if content exists
        content = CourseContent.query.get(content_id)
        if not content:
            return jsonify({
                "status": "error",
                "message": f"Content not found with ID: {content_id}"
            }), 404
            
        # Check if it's a video
        if content.content_type != 'video':
            return jsonify({
                "status": "error",
                "message": f"Content is not a video. Type: {content.content_type}"
            }), 400
            
        # Process the video content
        success = transcription_service.process_video_content(content_id)
        
        if success:
            # Index the content in vector database
            vector_db_service.index_content(content_id)
            
            return jsonify({
                "status": "success",
                "message": "Video processed and transcribed successfully",
                "content_id": content_id
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to process video content"
            }), 500
            
    except Exception as e:
        logging.error(f"Error in process_video_content: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@transcription_bp.route('/upload', methods=['POST'])
def upload_video():
    """
    Upload a video file and add it as course content
    
    Returns:
        JSON response with result
    """
    try:
        # Check if the post request has the file part
        if 'video_file' not in request.files:
            return jsonify({
                "status": "error",
                "message": "No video file part in the request"
            }), 400
            
        file = request.files['video_file']
        
        # Check if user did not select a file
        if file.filename == '':
            return jsonify({
                "status": "error",
                "message": "No video file selected"
            }), 400
            
        # Get form data
        course_id = request.form.get('course_id')
        title = request.form.get('title')
        
        # Validate course
        course = Course.query.get(course_id)
        if not course:
            return jsonify({
                "status": "error",
                "message": f"Course not found with ID: {course_id}"
            }), 404
            
        # Create directory if it doesn't exist
        upload_dir = os.path.join(current_app.static_folder, 'uploads', 'videos')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Create CourseContent record
        content = CourseContent(
            course_id=course_id,
            title=title or filename,
            content_type='video',
            url=file_path
        )
        
        db.session.add(content)
        db.session.commit()
        
        # Process the video in the background (would be better with a task queue)
        # For now, we'll process it synchronously
        success = transcription_service.process_video_content(content.id)
        
        if success:
            # Index the content in vector database
            vector_db_service.index_content(content.id)
            
            return jsonify({
                "status": "success",
                "message": "Video uploaded and processed successfully",
                "content": {
                    "id": content.id,
                    "title": content.title,
                    "course_id": content.course_id,
                    "content_type": content.content_type,
                    "url": content.url
                }
            })
        else:
            return jsonify({
                "status": "partial",
                "message": "Video uploaded but processing failed",
                "content": {
                    "id": content.id,
                    "title": content.title,
                    "course_id": content.course_id,
                    "content_type": content.content_type,
                    "url": content.url
                }
            }), 202
            
    except Exception as e:
        logging.error(f"Error in upload_video: {str(e)}")
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@transcription_bp.route('/batch-process/<int:course_id>', methods=['POST'])
def batch_process_videos(course_id):
    """
    Batch process all videos in a course
    
    Args:
        course_id (int): The ID of the course
        
    Returns:
        JSON response with result
    """
    try:
        # Check if course exists
        course = Course.query.get(course_id)
        if not course:
            return jsonify({
                "status": "error",
                "message": f"Course not found with ID: {course_id}"
            }), 404
            
        # Get all video content for the course
        videos = CourseContent.query.filter_by(
            course_id=course_id,
            content_type='video'
        ).all()
        
        if not videos:
            return jsonify({
                "status": "error",
                "message": f"No video content found for course ID: {course_id}"
            }), 404
            
        # Process each video
        results = {
            "total": len(videos),
            "processed": 0,
            "failed": 0,
            "failures": []
        }
        
        for video in videos:
            success = transcription_service.process_video_content(video.id)
            if success:
                # Index the content in vector database
                vector_db_service.index_content(video.id)
                results["processed"] += 1
            else:
                results["failed"] += 1
                results["failures"].append({
                    "id": video.id,
                    "title": video.title
                })
        
        return jsonify({
            "status": "success" if results["failed"] == 0 else "partial",
            "message": f"Processed {results['processed']} of {results['total']} videos",
            "results": results
        })
            
    except Exception as e:
        logging.error(f"Error in batch_process_videos: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500