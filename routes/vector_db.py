"""
Vector Database API Routes
Provides API endpoints for vector database operations
"""
import logging
from flask import Blueprint, request, jsonify
from services.vector_db_service import VectorDBService
from models import CourseContent
from app import db

logger = logging.getLogger(__name__)

vector_db_bp = Blueprint('vector_db', __name__)
vector_db_service = VectorDBService()

@vector_db_bp.route('/api/vector/index/<int:content_id>', methods=['POST'])
def index_content(content_id):
    """
    Index course content in vector database
    
    Args:
        content_id (int): The ID of the content to index
        
    Returns:
        JSON response with result
    """
    try:
        # Verify content exists
        content = CourseContent.query.get(content_id)
        if not content:
            return jsonify({'status': 'error', 'message': 'Content not found'}), 404
        
        # Index the content
        success = vector_db_service.index_content(content_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Content {content_id} indexed successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to index content'
            }), 500
        
    except Exception as e:
        logger.error(f"Error in index_content endpoint: {str(e)}")
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500

@vector_db_bp.route('/api/vector/batch-index', methods=['POST'])
def batch_index():
    """
    Batch index content in vector database
    
    Returns:
        JSON response with result
    """
    try:
        course_id = request.json.get('course_id') if request.json else None
        
        # Batch index content
        result = vector_db_service.batch_index(course_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in batch_index endpoint: {str(e)}")
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500

@vector_db_bp.route('/api/vector/search', methods=['GET'])
def search():
    """
    Search for content in vector database
    
    Returns:
        JSON response with search results
    """
    try:
        query = request.args.get('q')
        course_id = request.args.get('course_id')
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return jsonify({'status': 'error', 'message': 'No search query provided'}), 400
        
        # Convert course_id to int if provided
        if course_id:
            try:
                course_id = int(course_id)
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Invalid course ID'}), 400
        
        # Perform vector search
        results = vector_db_service.search(query, course_id, limit)
        
        return jsonify({
            'status': 'success',
            'query': query,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in search endpoint: {str(e)}")
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500

@vector_db_bp.route('/api/vector/status', methods=['GET'])
def status():
    """
    Get vector database status
    
    Returns:
        JSON response with status
    """
    try:
        status_info = vector_db_service.get_status()
        return jsonify(status_info)
        
    except Exception as e:
        logger.error(f"Error in status endpoint: {str(e)}")
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500