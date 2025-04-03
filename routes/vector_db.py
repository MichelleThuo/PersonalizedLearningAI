"""
Vector Database API Routes
Provides API endpoints for vector database operations
"""
import logging
from flask import Blueprint, request, jsonify

from services.vector_db_service import VectorDBService
from models import CourseContent, Course
from app import db

vector_db_bp = Blueprint('vector_db', __name__)
vector_db_service = VectorDBService()

@vector_db_bp.route('/index/<int:content_id>', methods=['POST'])
def index_content(content_id):
    """
    Index course content in vector database
    
    Args:
        content_id (int): The ID of the content to index
        
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
            
        # Index the content
        success = vector_db_service.index_content(content_id)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Content indexed successfully",
                "content_id": content_id
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to index content"
            }), 500
            
    except Exception as e:
        logging.error(f"Error in index_content: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@vector_db_bp.route('/batch-index', methods=['POST'])
def batch_index():
    """
    Batch index content in vector database
    
    Returns:
        JSON response with result
    """
    try:
        # Get course_id from query parameters
        course_id = request.args.get('course_id')
        
        # If course_id is provided, check if it exists
        if course_id:
            course = Course.query.get(course_id)
            if not course:
                return jsonify({
                    "status": "error",
                    "message": f"Course not found with ID: {course_id}"
                }), 404
        
        # Batch index content
        result = vector_db_service.batch_index_content(course_id)
        
        return jsonify(result)
            
    except Exception as e:
        logging.error(f"Error in batch_index: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@vector_db_bp.route('/search', methods=['GET'])
def search():
    """
    Search for content in vector database
    
    Returns:
        JSON response with search results
    """
    try:
        # Get query parameters
        query = request.args.get('q', '')
        course_id = request.args.get('course_id')
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return jsonify({
                "status": "error",
                "message": "Query parameter 'q' is required"
            }), 400
            
        # Search in vector database
        content_ids = vector_db_service.search(query, course_id, limit)
        
        # Get content details
        contents = []
        if content_ids:
            contents = CourseContent.query.filter(CourseContent.id.in_(content_ids)).all()
            
            # Convert to dictionary and reorder based on search results
            content_dict = {content.id: content for content in contents}
            contents = [content_dict.get(id) for id in content_ids if id in content_dict]
        
        # Format results
        results = []
        for content in contents:
            results.append({
                "id": content.id,
                "title": content.title,
                "content_type": content.content_type,
                "course_id": content.course_id,
                "course_title": content.course.title if content.course else None,
                "url": content.url,
                "preview": content.content_text[:200] + "..." if content.content_text else None
            })
        
        return jsonify({
            "status": "success",
            "query": query,
            "results_count": len(results),
            "results": results
        })
            
    except Exception as e:
        logging.error(f"Error in search: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@vector_db_bp.route('/status', methods=['GET'])
def status():
    """
    Get vector database status
    
    Returns:
        JSON response with status
    """
    try:
        # Initialize the service
        success = vector_db_service.initialize()
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Vector database is operational",
                "details": {
                    "index_name": vector_db_service.index_name,
                    "dimension": vector_db_service.dimension,
                    "environment": vector_db_service.pinecone_environment
                }
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Vector database is not operational"
            }), 500
            
    except Exception as e:
        logging.error(f"Error in status: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500