"""Enhanced search service with vector and keyword search capabilities."""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models import CourseContent, Course, SearchIndex

from .vector_db import vector_db_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchService:
    """Service for search operations with vector and keyword search."""

    def __init__(self):
        """Initialize search service."""
        self.vector_db = vector_db_service
        logger.info("Search service initialized")

    def search(
        self, 
        db: Session, 
        query: str, 
        course_id: Optional[int] = None, 
        limit: int = 10,
        use_vector_search: bool = True,
        use_hybrid_search: bool = True,
        semantic_weight: float = 0.7
    ) -> Dict[str, Any]:
        """
        Search for content matching the query.
        
        Args:
            db: Database session
            query: Search query string
            course_id: Optional course ID to filter results
            limit: Maximum number of results
            use_vector_search: Whether to use vector search
            use_hybrid_search: Whether to use hybrid search (keyword + vector)
            semantic_weight: Weight for semantic search (0-1)
            
        Returns:
            Dict with search results
        """
        # Vector search if enabled and available
        if use_vector_search and self.vector_db.initialized:
            return self.vector_db.search(
                query=query,
                course_id=course_id,
                limit=limit,
                use_hybrid_search=use_hybrid_search,
                semantic_weight=semantic_weight
            )
        
        # Fallback to keyword search
        return self._keyword_search(
            db=db,
            query=query,
            course_id=course_id,
            limit=limit
        )

    def _keyword_search(
        self, 
        db: Session, 
        query: str, 
        course_id: Optional[int] = None, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Perform keyword-based search as fallback.
        
        Args:
            db: Database session
            query: Search query string
            course_id: Optional course ID to filter results
            limit: Maximum number of results
            
        Returns:
            Dict with search results
        """
        try:
            # Prepare search terms
            search_terms = [f"%{term}%" for term in query.split()]
            
            # Base query joining CourseContent with Course
            search_query = db.query(
                CourseContent, Course
            ).join(
                Course, CourseContent.course_id == Course.id
            )
            
            # Add course filter if specified
            if course_id:
                search_query = search_query.filter(CourseContent.course_id == course_id)
                
            # Add search conditions
            conditions = []
            for term in search_terms:
                conditions.append(or_(
                    CourseContent.title.ilike(term),
                    CourseContent.content_text.ilike(term)
                ))
                
            # Apply conditions and get results
            search_query = search_query.filter(or_(*conditions)).limit(limit)
            results = search_query.all()
            
            # Format results
            formatted_results = []
            for content, course in results:
                # Calculate basic relevance score
                # Count how many search terms match the content
                relevance_score = 0.0
                for term in search_terms:
                    clean_term = term.replace("%", "").lower()
                    if clean_term in content.title.lower():
                        relevance_score += 0.5  # Higher weight for title matches
                    if clean_term in content.content_text.lower():
                        relevance_score += 0.3  # Lower weight for content matches
                
                # Normalize score to 0-1 range
                relevance_score = min(1.0, relevance_score) 
                
                # Create snippet from content
                snippet = content.content_text[:200] + "..." if content.content_text else ""
                
                formatted_results.append({
                    "id": content.id,
                    "title": content.title,
                    "content_type": content.content_type,
                    "snippet": snippet,
                    "course_id": course.id,
                    "course_title": course.title,
                    "url": content.url,
                    "relevance_score": relevance_score
                })
            
            # Sort by relevance
            formatted_results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return {
                "query": query,
                "results": formatted_results,
                "total_count": len(formatted_results),
                "filtered_by_course": course_id,
                "vector_search_enabled": False
            }
        except Exception as e:
            logger.error(f"Error in keyword search: {str(e)}")
            return {
                "query": query,
                "results": [],
                "total_count": 0,
                "filtered_by_course": course_id,
                "error": str(e),
                "vector_search_enabled": False
            }

    def index_content(self, db: Session, content_id: int) -> Dict[str, Any]:
        """
        Index content for searching.
        
        Args:
            db: Database session
            content_id: ID of content to index
            
        Returns:
            Dict with indexing result
        """
        try:
            # Check if content exists
            content = db.query(CourseContent).filter(CourseContent.id == content_id).first()
            if not content:
                return {"success": False, "error": f"Content with ID {content_id} not found"}
                
            # Index in vector database if available
            vector_result = {"success": False, "message": "Vector database not initialized"}
            if self.vector_db.initialized:
                vector_result = self.vector_db.index_content(db, content_id)
                
            # Update or create search index record
            search_index = db.query(SearchIndex).filter(SearchIndex.content_id == content_id).first()
            if not search_index:
                search_index = SearchIndex(
                    content_id=content_id,
                    indexed_text=content.content_text
                )
                db.add(search_index)
            else:
                search_index.indexed_text = content.content_text
                
            db.commit()
            
            return {
                "success": True,
                "content_id": content.id,
                "title": content.title,
                "vector_result": vector_result,
                "message": f"Successfully indexed content: {content.title}"
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error indexing content {content_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    def batch_index(self, db: Session, course_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Batch index content.
        
        Args:
            db: Database session
            course_id: Optional course ID to filter content
            
        Returns:
            Dict with indexing results
        """
        try:
            # Get content to index
            query = db.query(CourseContent)
            if course_id:
                query = query.filter(CourseContent.course_id == course_id)
                
            contents = query.all()
            
            if not contents:
                message = "No content found" if not course_id else f"No content found for course {course_id}"
                return {"success": False, "error": message}
                
            # Index each content
            results = []
            for content in contents:
                result = self.index_content(db, content.id)
                results.append(result)
                
            # Get summary stats
            success_count = sum(1 for r in results if r["success"])
            
            return {
                "success": success_count > 0,
                "total": len(contents),
                "indexed": success_count,
                "failed": len(contents) - success_count,
                "vector_db_available": self.vector_db.initialized,
                "results": results
            }
        except Exception as e:
            logger.error(f"Error in batch indexing: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_relevant_content(
        self, 
        db: Session, 
        query: str, 
        course_id: Optional[int] = None, 
        limit: int = 3
    ) -> str:
        """
        Get relevant content for chat context.
        
        Args:
            db: Database session
            query: User query
            course_id: Optional course ID to filter results
            limit: Maximum number of context items
            
        Returns:
            Consolidated context string
        """
        # Use vector search if available
        if self.vector_db.initialized:
            return self.vector_db.get_relevant_context(query, course_id, limit)
            
        # Fallback to keyword search
        search_results = self._keyword_search(db, query, course_id, limit)
        
        # Extract content
        contexts = []
        for result in search_results.get("results", []):
            contexts.append(f"Content: {result['title']}\n{result['snippet']}")
            
        # Join contexts
        if contexts:
            return "\n\n".join(contexts)
        else:
            return ""

    def get_similar_content(
        self, 
        db: Session, 
        content_id: int, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get content similar to specified content.
        
        Args:
            db: Database session
            content_id: Content ID to find similar content for
            limit: Maximum number of similar content items
            
        Returns:
            List of similar content items
        """
        # Use vector search if available
        if self.vector_db.initialized:
            return self.vector_db.get_similar_content(content_id, db, limit)
            
        # Fallback to basic similarity (by course and content type)
        try:
            content = db.query(CourseContent).filter(CourseContent.id == content_id).first()
            if not content:
                return []
                
            # Find similar content in same course with same content type
            similar_query = db.query(
                CourseContent, Course
            ).join(
                Course, CourseContent.course_id == Course.id
            ).filter(
                CourseContent.id != content_id,  # Exclude current content
                CourseContent.course_id == content.course_id,  # Same course
                CourseContent.content_type == content.content_type  # Same type
            ).limit(limit)
            
            similar_content = similar_query.all()
            
            # Format results
            results = []
            for similar, course in similar_content:
                results.append({
                    "id": similar.id,
                    "title": similar.title,
                    "content_type": similar.content_type,
                    "snippet": similar.content_text[:200] + "..." if similar.content_text else "",
                    "course_id": course.id,
                    "course_title": course.title,
                    "url": similar.url,
                    "relevance_score": 0.5  # Default score for non-vector similarity
                })
                
            return results
        except Exception as e:
            logger.error(f"Error getting similar content: {str(e)}")
            return []


# Initialize service
search_service = SearchService()