"""Simple vector database service using Pinecone (v6.0.2) without LlamaIndex."""
import os
import logging
import json
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy.orm import Session
from pinecone import Pinecone, ServerlessSpec

from models import CourseContent, Course

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Pinecone API key from environment
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
INDEX_NAME = "moodle-assistant"
DIMENSION = 512  # Dimension for TF-IDF vectorizer
CLOUD = "aws"  # AWS cloud for serverless (free tier compatible)
REGION = "us-east-1"  # us-east-1 region for serverless (free tier compatible)


class SimpleVectorDBService:
    """Service for managing vector database operations using Pinecone v6.0.2 without LlamaIndex."""

    def __init__(self):
        """Initialize the vector database service."""
        self.initialized = False
        self.vectorizer = TfidfVectorizer(max_features=DIMENSION)
        
        try:
            # Check for Pinecone API key
            if not PINECONE_API_KEY:
                logger.warning("PINECONE_API_KEY not found in environment variables")
                return
                
            # Initialize Pinecone with v6.0.2 API
            logger.info("Initializing Pinecone with v6.0.2 API...")
            self.pc = Pinecone(api_key=PINECONE_API_KEY)
            
            # Check if index exists, if not create it
            index_list = self.pc.list_indexes()
            index_names = index_list.names()
            
            if INDEX_NAME not in index_names:
                logger.info(f"Creating Pinecone index: {INDEX_NAME}")
                # Create serverless index
                self.pc.create_index(
                    name=INDEX_NAME,
                    dimension=DIMENSION,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud=CLOUD,
                        region=REGION
                    )
                )
                logger.info(f"Index '{INDEX_NAME}' created successfully")
            
                # Fit vectorizer with an empty list to initialize
                self.vectorizer.fit_transform(["Sample text for initialization"])
            else:
                logger.info(f"Index '{INDEX_NAME}' already exists")
            
            # Connect to Pinecone index
            self.index = self.pc.Index(INDEX_NAME)
            self.initialized = True
            logger.info("Vector database service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector database service: {str(e)}")
            import traceback
            traceback.print_exc()

    def _vectorize_text(self, text: str) -> List[float]:
        """
        Convert text to vector using TF-IDF.
        
        Args:
            text: Text to vectorize
            
        Returns:
            Vector representation of text
        """
        # Check if vectorizer is fitted, if not fit it
        try:
            vector = self.vectorizer.transform([text])
        except ValueError:
            # Vectorizer not fitted, fit it with the text
            self.vectorizer.fit_transform([text])
            vector = self.vectorizer.transform([text])
            
        # Convert sparse vector to dense array and normalize
        dense_vector = vector.toarray()[0]
        
        # Normalize vector to have unit length
        norm = np.linalg.norm(dense_vector)
        if norm > 0:
            dense_vector = dense_vector / norm
            
        # Convert to list of float
        return dense_vector.tolist()

    def index_content(self, db: Session, content_id: int) -> Dict[str, Any]:
        """
        Index a single content item in the vector database.
        
        Args:
            db: Database session
            content_id: ID of the content to index
            
        Returns:
            Dict with indexing result
        """
        if not self.initialized:
            return {"success": False, "error": "Vector database service not initialized"}
            
        try:
            # Get content from database
            content = db.query(CourseContent).filter(CourseContent.id == content_id).first()
            if not content:
                return {"success": False, "error": f"Content with ID {content_id} not found"}
                
            # Get course information
            course = db.query(Course).filter(Course.id == content.course_id).first()
            course_title = course.title if course else "Unknown Course"
            
            # Convert content text to vector
            text = content.content_text
            vector = self._vectorize_text(text)
            
            # Create metadata
            metadata = {
                "content_id": content.id,
                "title": content.title,
                "content_type": content.content_type,
                "course_id": content.course_id,
                "course_title": course_title,
                "url": content.url
            }
            
            # Upsert vector to Pinecone
            vector_id = f"content-{content_id}"
            self.index.upsert(
                vectors=[(vector_id, vector, metadata)],
                namespace="content"
            )
            
            return {
                "success": True,
                "content_id": content_id,
                "title": content.title,
                "vector_id": vector_id
            }
        except Exception as e:
            logger.error(f"Error indexing content {content_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    def batch_index(self, db: Session, course_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Batch index content in vector database.
        
        Args:
            db: Database session
            course_id: Optional course ID to filter content
            
        Returns:
            Dict with indexing result
        """
        if not self.initialized:
            return {"success": False, "error": "Vector database service not initialized"}
            
        try:
            # Query content to index
            query = db.query(CourseContent)
            if course_id:
                query = query.filter(CourseContent.course_id == course_id)
                
            contents = query.all()
            if not contents:
                return {
                    "success": False, 
                    "error": f"No content found{' for course ' + str(course_id) if course_id else ''}"
                }
                
            # Process each content item
            processed = []
            for content in contents:
                result = self.index_content(db, content.id)
                if result.get("success"):
                    processed.append(result)
                    
            return {
                "success": True,
                "processed_count": len(processed),
                "processed": processed,
                "total_count": len(contents)
            }
        except Exception as e:
            logger.error(f"Error in batch indexing: {str(e)}")
            return {"success": False, "error": str(e)}

    def search(
        self, 
        query: str, 
        course_id: Optional[int] = None,
        limit: int = 10,
        use_hybrid_search: bool = False,
        semantic_weight: float = 0.8
    ) -> Dict[str, Any]:
        """
        Search for content in vector database.
        
        Args:
            query: Search query
            course_id: Optional course ID to filter results
            limit: Maximum number of results
            use_hybrid_search: Whether to use hybrid search (ignored in simple implementation)
            semantic_weight: Weight for semantic search (ignored in simple implementation)
            
        Returns:
            Dict with search results
        """
        if not self.initialized:
            return {
                "query": query,
                "results": [],
                "total_count": 0,
                "filtered_by_course": course_id,
                "vector_search_enabled": False
            }
            
        try:
            # Convert query to vector
            query_vector = self._vectorize_text(query)
            
            # Set up filter for course_id if provided
            filter_dict = {}
            if course_id:
                filter_dict = {"course_id": {"$eq": course_id}}
                
            # Query Pinecone
            query_response = self.index.query(
                vector=query_vector,
                top_k=limit,
                include_metadata=True,
                namespace="content",
                filter=filter_dict
            )
            
            # Process results
            results = []
            for match in query_response.matches:
                metadata = match.metadata
                results.append({
                    "content_id": metadata.get("content_id"),
                    "title": metadata.get("title"),
                    "content_type": metadata.get("content_type"),
                    "course_id": metadata.get("course_id"),
                    "course_title": metadata.get("course_title"),
                    "url": metadata.get("url"),
                    "relevance_score": float(match.score) if hasattr(match, "score") else 0.0
                })
            
            return {
                "query": query,
                "results": results,
                "total_count": len(results),
                "filtered_by_course": course_id,
                "vector_search_enabled": self.initialized
            }
        except Exception as e:
            logger.error(f"Error searching vector database: {str(e)}")
            return {
                "query": query,
                "results": [],
                "total_count": 0,
                "filtered_by_course": course_id,
                "error": str(e),
                "vector_search_enabled": self.initialized
            }

    def get_similar_content(self, content_id: int, db: Session, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get content similar to the specified content.
        
        Args:
            content_id: Content ID to find similar content for
            db: Database session
            limit: Maximum number of similar content items
            
        Returns:
            List of similar content items
        """
        if not self.initialized:
            return []
            
        try:
            # Get content from database
            content = db.query(CourseContent).filter(CourseContent.id == content_id).first()
            if not content:
                return []
                
            # Use content text as query
            query = content.content_text
            
            # Execute search, excluding the original content
            search_result = self.search(query, limit=limit+1)
            
            # Filter out the original content
            similar_items = [
                result for result in search_result.get("results", [])
                if result.get("content_id") != content_id
            ][:limit]
            
            return similar_items
        except Exception as e:
            logger.error(f"Error getting similar content: {str(e)}")
            return []
            
    def get_relevant_context(self, query: str, course_id: Optional[int] = None, limit: int = 3) -> str:
        """
        Get relevant context for chat based on query.
        
        Args:
            query: Search query
            course_id: Optional course ID to filter results
            limit: Maximum number of context items
            
        Returns:
            Consolidated context string
        """
        if not self.initialized:
            return ""
            
        try:
            # Search for relevant content
            search_result = self.search(query, course_id=course_id, limit=limit)
            
            # Extract and format context items
            contexts = []
            for result in search_result.get("results", []):
                title = result.get("title", "Untitled")
                content_id = result.get("content_id", "unknown")
                course_title = result.get("course_title", "Unknown Course")
                
                # Format context item
                context_item = f"Content ID: {content_id}\nTitle: {title}\nCourse: {course_title}\n"
                contexts.append(context_item)
                
            # Join all context items
            if contexts:
                return "\n\n".join(contexts)
            else:
                return ""
        except Exception as e:
            logger.error(f"Error getting relevant context: {str(e)}")
            return ""

    def get_status(self) -> Dict[str, Any]:
        """
        Get status of vector database.
        
        Returns:
            Dict with status information
        """
        status = {
            "initialized": self.initialized,
            "pinecone_api_key_available": bool(PINECONE_API_KEY),
            "index_name": INDEX_NAME,
            "dimension": DIMENSION,
            "cloud": CLOUD,
            "region": REGION
        }
        
        if self.initialized:
            try:
                # Get index stats from Pinecone using v6.0.2 API
                stats = self.index.describe_index_stats()
                
                # Extract information
                status["document_count"] = stats.total_vector_count
                status["namespaces"] = stats.namespaces
            except Exception as e:
                status["error"] = str(e)
                
        return status


# Initialize service
vector_db_service = SimpleVectorDBService()