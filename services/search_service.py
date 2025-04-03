import re
import logging
from models import CourseContent, SearchIndex
from app import db

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self):
        pass
    
    def index_content(self, content_id):
        """
        Index a piece of course content for searching
        
        Args:
            content_id (int): The ID of the CourseContent to index
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            content = CourseContent.query.get(content_id)
            if not content:
                logger.error(f"Content with ID {content_id} not found")
                return False
            
            # Get text to index
            text_to_index = content.content_text or ""
            title = content.title or ""
            
            # Combine title and content for indexing
            indexed_text = f"{title} {text_to_index}"
            
            # Check if there's an existing index
            existing_index = SearchIndex.query.filter_by(content_id=content_id).first()
            
            if existing_index:
                # Update existing index
                existing_index.indexed_text = indexed_text
            else:
                # Create new index
                new_index = SearchIndex(content_id=content_id, indexed_text=indexed_text)
                db.session.add(new_index)
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error indexing content: {str(e)}")
            db.session.rollback()
            return False
    
    def search(self, query, course_id=None, limit=10):
        """
        Search for content matching the given query
        
        Args:
            query (str): The search query
            course_id (int, optional): Filter results by course ID
            limit (int): Maximum number of results to return
            
        Returns:
            list: List of CourseContent objects matching the query
        """
        try:
            # Normalize query
            query = query.lower().strip()
            query_terms = re.findall(r'\b\w+\b', query)
            
            # Get base query
            content_query = db.session.query(CourseContent).join(
                SearchIndex, CourseContent.id == SearchIndex.content_id
            )
            
            # Filter by course if provided
            if course_id:
                content_query = content_query.filter(CourseContent.course_id == course_id)
            
            # Filter by search terms
            for term in query_terms:
                content_query = content_query.filter(
                    SearchIndex.indexed_text.ilike(f'%{term}%')
                )
            
            # Get results
            results = content_query.limit(limit).all()
            return results
            
        except Exception as e:
            logger.error(f"Error searching content: {str(e)}")
            return []
    
    def get_relevant_content(self, query, course_id=None, limit=5):
        """
        Get content relevant to a user query, used for contextual chatbot responses
        
        Args:
            query (str): The user query
            course_id (int, optional): Filter results by course ID
            limit (int): Maximum number of results to return
            
        Returns:
            str: Concatenated relevant content as context
        """
        results = self.search(query, course_id, limit)
        
        if not results:
            return ""
        
        # Combine relevant content
        context = "Here is relevant content from the course materials:\n\n"
        
        for i, content in enumerate(results, 1):
            context += f"--- Document {i}: {content.title} ---\n"
            text = content.content_text or "No content available"
            
            # Limit the length of each content piece
            if len(text) > 1000:
                text = text[:1000] + "..."
                
            context += f"{text}\n\n"
        
        return context
