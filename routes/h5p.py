"""
H5P Content Generation API Routes
Provides API endpoints for generating H5P interactive content
"""

import os
import logging
from flask import Blueprint, request, jsonify, current_app, send_file
from models import db, Course, CourseContent
from services.h5p_service import H5PService

# Create blueprint
h5p_bp = Blueprint('h5p', __name__)
logger = logging.getLogger(__name__)

# Initialize services
h5p_service = H5PService()

@h5p_bp.route('/generate', methods=['POST'])
def generate_h5p_content():
    """Generate H5P content from regular course content"""
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        content_id = data.get('content_id')
        content_type = data.get('content_type', 'course_presentation')
        custom_text = data.get('custom_text')
        
        # Validate content type
        valid_types = ['course_presentation', 'question_set', 'interactive_video', 'fill_in_the_blanks']
        if content_type not in valid_types:
            return jsonify({
                'error': f'Invalid content type. Must be one of: {", ".join(valid_types)}'
            }), 400
            
        # If content_id is provided, get from database
        if content_id:
            content_item = CourseContent.query.get(content_id)
            
            if not content_item:
                return jsonify({'error': 'Content not found'}), 404
                
            content_text = content_item.content_text or content_item.title
        elif custom_text:
            content_text = custom_text
        else:
            return jsonify({'error': 'Either content_id or custom_text must be provided'}), 400
            
        # Generate H5P content
        result = h5p_service.generate_interactive_content(content_text, content_type)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
            
        # If successful, update the course content with H5P URL
        if content_id:
            content_item.url = result['url']
            db.session.commit()
            
        return jsonify({
            'success': True,
            'h5p_url': result['url'],
            'message': f'H5P {content_type} generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error generating H5P content: {str(e)}")
        return jsonify({'error': f'Failed to generate H5P content: {str(e)}'}), 500

@h5p_bp.route('/download/<filename>', methods=['GET'])
def download_h5p(filename):
    """Download a generated H5P file"""
    try:
        # Ensure filename only contains allowed characters
        if not all(c.isalnum() or c in '-_.' for c in filename):
            return jsonify({'error': 'Invalid filename'}), 400
        
        # Get file path
        file_path = os.path.join(h5p_service.h5p_temp_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        # Return file for download
        return send_file(
            file_path,
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error downloading H5P file: {str(e)}")
        return jsonify({'error': f'Failed to download H5P file: {str(e)}'}), 500

@h5p_bp.route('/for-course/<int:course_id>', methods=['GET'])
def get_h5p_for_course(course_id):
    """Get all H5P content for a specific course"""
    try:
        # Check if course exists
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
            
        # Get all course content with H5P URLs
        content_items = CourseContent.query.filter_by(course_id=course_id).all()
        h5p_items = []
        
        for item in content_items:
            # Check if URL is an H5P file
            if item.url and ('.h5p' in item.url or '/h5p_content/' in item.url):
                h5p_items.append({
                    'id': item.id,
                    'title': item.title,
                    'content_type': item.content_type,
                    'url': item.url
                })
                
        return jsonify(h5p_items)
        
    except Exception as e:
        logger.error(f"Error getting H5P content for course: {str(e)}")
        return jsonify({'error': f'Failed to get H5P content: {str(e)}'}), 500