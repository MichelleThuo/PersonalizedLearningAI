"""
Vector Database Service
Provides functionality to index and search content using Pinecone vector database
"""
import os
import logging
import json
from typing import List, Dict, Any, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import pinecone
from flask import current_app
from models import CourseContent, SearchIndex
from app import db

logger = logging.getLogger(__name__)

class VectorDBService:
    """Service for vector database operations"""
    
    def __init__(self):
        """Initialize the vector database service"""
        self.initialized = False
        self.index_name = "learning-assistant"
        self.dimension = 512  # Default vector dimension
        self.api_key = os.environ.get("PINECONE_API_KEY")
        self.vectorizer = TfidfVectorizer(max_features=self.dimension)
        
        # Initialize lazily (only when needed)
        # self._initialize()
    
    def _initialize(self):
        """Initialize the Pinecone client and index"""
        if self.initialized:
            return True
        
        try:
            if not self.api_key:
                logger.error("PINECONE_API_KEY environment variable is not set")
                return False
            
            # Initialize Pinecone
            logger.info("Initializing Pinecone...")
            pinecone.init(api_key=self.api_key, environment="gcp-starter")
            
            # Check if our index exists, if not create it
            if self.index_name not in pinecone.list_indexes():
                logger.info(f"Creating Pinecone index '{self.index_name}'...")
                pinecone.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine"
                )
            
            # Connect to the index
            self.index = pinecone.Index(self.index_name)
            logger.info(f"Connected to Pinecone index '{self.index_name}'")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Error initializing Pinecone: {str(e)}")
            return False
    
    def _text_to_vector(self, text: str) -> List[float]:
        """
        Convert text to a vector representation using TF-IDF
        
        Args:
            text (str): The text to vectorize
            
        Returns:
            List[float]: Vector representation of the text
        """
        if not text:
            return [0.0] * self.dimension
        
        # Fit the vectorizer if not already fitted
        if not hasattr(self.vectorizer, 'vocabulary_'):
            # Fit on a corpus of one document (the current text)
            self.vectorizer.fit([text])
        
        # Transform the text to a vector
        vector = self.vectorizer.transform([text]).toarray()[0]
        
        # Normalize to unit length
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        # Return as a list with specified dimension
        result = vector.tolist()
        if len(result) < self.dimension:
            result.extend([0.0] * (self.dimension - len(result)))
        elif len(result) > self.dimension:
            result = result[:self.dimension]
            
        return result
    
    def index_content(self, content_id: int) -> bool:
        """
        Index a piece of course content in the vector database
        
        Args:
            content_id (int): The ID of the CourseContent to index
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the content from the database
            content = CourseContent.query.get(content_id)
            if not content:
                logger.error(f"Content with ID {content_id} not found")
                return False
            
            if not content.content_text:
                logger.warning(f"Content with ID {content_id} has no text to index")
                return False
            
            # Initialize the vector database if not already initialized
            if not self._initialize():
                return False
            
            # Convert the content text to a vector
            vector = self._text_to_vector(content.content_text)
            
            # Add metadata
            metadata = {
                'content_id': content.id,
                'content_type': content.content_type,
                'title': content.title,
                'course_id': content.course_id
            }
            
            # Upsert the vector into Pinecone
            self.index.upsert(
                vectors=[(str(content.id), vector, metadata)]
            )
            
            # Add/update the search index record in our database
            search_index = SearchIndex.query.filter_by(content_id=content.id).first()
            if not search_index:
                search_index = SearchIndex(content_id=content.id, indexed_text=content.content_text)
                db.session.add(search_index)
            else:
                search_index.indexed_text = content.content_text
            
            db.session.commit()
            
            logger.info(f"Successfully indexed content ID {content_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing content: {str(e)}")
            db.session.rollback()
            return False
    
    def search(self, query: str, course_id: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for content matching the given query
        
        Args:
            query (str): The search query
            course_id (int, optional): Filter results by course ID
            limit (int): Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of search results
        """
        try:
            if not query:
                return []
            
            # Initialize the vector database if not already initialized
            if not self._initialize():
                return []
            
            # Convert the query to a vector
            query_vector = self._text_to_vector(query)
            
            # Set up filter for course_id if provided
            filter_dict = None
            if course_id:
                filter_dict = {
                    "course_id": {"$eq": course_id}
                }
            
            # Query Pinecone
            results = self.index.query(
                vector=query_vector,
                top_k=limit,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Format results
            formatted_results = []
            for match in results.get("matches", []):
                content_id = match.get("metadata", {}).get("content_id")
                if content_id:
                    content = CourseContent.query.get(content_id)
                    if content:
                        formatted_results.append({
                            'id': content.id,
                            'title': content.title,
                            'content_type': content.content_type,
                            'course_id': content.course_id,
                            'course': content.course.title if content.course else None,
                            'url': content.url,
                            'snippet': (content.content_text[:200] + '...') if content.content_text and len(content.content_text) > 200 else content.content_text,
                            'score': match.get("score", 0)
                        })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vector database: {str(e)}")
            return []
    
    def batch_index(self, course_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Batch index all content or content for a specific course
        
        Args:
            course_id (int, optional): Index only content from this course
            
        Returns:
            Dict[str, Any]: Results with success/failure counts
        """
        try:
            # Initialize the vector database if not already initialized
            if not self._initialize():
                return {"status": "error", "message": "Failed to initialize vector database"}
            
            # Get content to index
            query = CourseContent.query
            if course_id:
                query = query.filter_by(course_id=course_id)
            
            # Only index content with text
            query = query.filter(CourseContent.content_text.isnot(None))
            content_items = query.all()
            
            if not content_items:
                return {"status": "warning", "message": "No content found to index"}
            
            # Index each content item
            success_count = 0
            failure_count = 0
            
            for content in content_items:
                if self.index_content(content.id):
                    success_count += 1
                else:
                    failure_count += 1
            
            total = success_count + failure_count
            
            if success_count == total:
                return {
                    "status": "success",
                    "message": f"Successfully indexed all {total} content items"
                }
            elif success_count > 0:
                return {
                    "status": "partial",
                    "message": f"Indexed {success_count} out of {total} content items",
                    "success_count": success_count,
                    "failure_count": failure_count
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to index any content"
                }
            
        except Exception as e:
            logger.error(f"Error in batch index: {str(e)}")
            return {"status": "error", "message": f"An error occurred: {str(e)}"}
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of the vector database
        
        Returns:
            Dict[str, Any]: Status information
        """
        try:
            if not self.api_key:
                return {
                    "status": "not_configured",
                    "message": "Pinecone API key not set"
                }
            
            # Try to initialize
            if not self._initialize():
                return {
                    "status": "error",
                    "message": "Failed to initialize Pinecone"
                }
            
            # Get index statistics
            stats = self.index.describe_index_stats()
            
            return {
                "status": "active",
                "index_name": self.index_name,
                "dimension": self.dimension,
                "vector_count": stats.get("total_vector_count", 0),
                "namespaces": stats.get("namespaces", {})
            }
            
        except Exception as e:
            logger.error(f"Error getting vector database status: {str(e)}")
            return {
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }