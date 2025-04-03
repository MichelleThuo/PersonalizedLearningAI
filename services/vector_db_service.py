"""
Vector Database Service
Provides functionality to store and query vector embeddings using Pinecone
"""
import os
import logging
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import pinecone

from app import db
from models import CourseContent, SearchIndex

class VectorDBService:
    """Service for vector database operations"""
    
    def __init__(self):
        """Initialize the vector database service with Pinecone"""
        self.api_key = os.environ.get("PINECONE_API_KEY")
        self.pinecone_environment = "us-west1-gcp"  # Update with your environment
        self.index_name = "moodle-content"
        self.dimension = 768  # Dimension for the vector embeddings
        self.vectorizer = TfidfVectorizer(max_features=self.dimension)
        self.initialized = False
        
        logging.info("Initializing VectorDBService")
        
    def initialize(self):
        """Initialize Pinecone connection and index"""
        if self.initialized:
            return True
            
        try:
            if not self.api_key:
                logging.error("Pinecone API key not found in environment variables")
                return False
                
            # Initialize Pinecone
            pinecone.init(api_key=self.api_key, environment=self.pinecone_environment)
            
            # Check if index exists, create if not
            if self.index_name not in pinecone.list_indexes():
                logging.info(f"Creating Pinecone index: {self.index_name}")
                pinecone.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine"
                )
            
            # Connect to the index
            self.index = pinecone.Index(self.index_name)
            self.initialized = True
            logging.info("Pinecone initialization successful")
            return True
            
        except Exception as e:
            logging.error(f"Error initializing Pinecone: {str(e)}")
            return False
    
    def generate_embedding(self, text):
        """
        Generate a vector embedding for text
        
        Args:
            text (str): Text to embed
            
        Returns:
            numpy.array: Vector embedding
        """
        try:
            if not text:
                return None
                
            # Fit and transform on the text to get tfidf vectors
            X = self.vectorizer.fit_transform([text])
            
            # Convert to dense array and normalize
            vector = X.toarray()[0]
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
                
            return vector.tolist()
            
        except Exception as e:
            logging.error(f"Error generating embedding: {str(e)}")
            return None
    
    def index_content(self, content_id):
        """
        Index course content in Pinecone
        
        Args:
            content_id (int): ID of the CourseContent to index
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Initialize if not done already
            if not self.initialize():
                return False
                
            # Get the content from database
            content = CourseContent.query.get(content_id)
            if not content:
                logging.error(f"Content not found with ID: {content_id}")
                return False
            
            # Get text to index
            text_to_index = content.content_text
            if not text_to_index:
                logging.error(f"No text content for ID: {content_id}")
                return False
            
            # Generate embedding
            embedding = self.generate_embedding(text_to_index)
            if not embedding:
                logging.error(f"Failed to generate embedding for content ID: {content_id}")
                return False
            
            # Create metadata
            metadata = {
                "content_id": content_id,
                "course_id": content.course_id,
                "title": content.title,
                "content_type": content.content_type,
                "url": content.url if content.url else ""
            }
            
            # Upsert to Pinecone
            self.index.upsert(
                vectors=[(str(content_id), embedding, metadata)]
            )
            
            logging.info(f"Content indexed in Pinecone for ID: {content_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error indexing content in Pinecone: {str(e)}")
            return False
    
    def search(self, query, course_id=None, limit=10):
        """
        Search for content matching the given query
        
        Args:
            query (str): The search query
            course_id (int, optional): Filter results by course ID
            limit (int): Maximum number of results to return
            
        Returns:
            list: List of content IDs matching the query
        """
        try:
            # Initialize if not done already
            if not self.initialize():
                return []
                
            # Generate embedding for the query
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                logging.error("Failed to generate embedding for query")
                return []
            
            # Filter by course if specified
            filter_query = {}
            if course_id:
                filter_query = {"course_id": int(course_id)}
            
            # Query Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=limit,
                include_metadata=True,
                filter=filter_query
            )
            
            # Process results
            content_ids = []
            for match in results.matches:
                content_ids.append(int(match.id))
            
            logging.info(f"Pinecone search for '{query}' returned {len(content_ids)} results")
            return content_ids
            
        except Exception as e:
            logging.error(f"Error searching in Pinecone: {str(e)}")
            return []
    
    def batch_index_content(self, course_id=None):
        """
        Batch index all course content or content from a specific course
        
        Args:
            course_id (int, optional): Index only content from this course
            
        Returns:
            dict: Summary of indexing results
        """
        try:
            # Initialize if not done already
            if not self.initialize():
                return {"status": "error", "message": "Failed to initialize Pinecone"}
                
            # Query content to index
            query = CourseContent.query
            if course_id:
                query = query.filter_by(course_id=course_id)
            
            contents = query.all()
            
            # Track results
            results = {
                "total": len(contents),
                "indexed": 0,
                "failed": 0,
                "errors": []
            }
            
            # Index each content
            for content in contents:
                success = self.index_content(content.id)
                if success:
                    results["indexed"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Failed to index content ID: {content.id}")
            
            logging.info(f"Batch indexing complete: {results['indexed']}/{results['total']} successful")
            return {
                "status": "success" if results["failed"] == 0 else "partial",
                "results": results
            }
            
        except Exception as e:
            logging.error(f"Error in batch indexing: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def delete_content(self, content_id):
        """
        Delete content from the index
        
        Args:
            content_id (int): ID of the content to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Initialize if not done already
            if not self.initialize():
                return False
                
            # Delete from Pinecone
            self.index.delete(ids=[str(content_id)])
            
            logging.info(f"Content deleted from Pinecone for ID: {content_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error deleting content from Pinecone: {str(e)}")
            return False