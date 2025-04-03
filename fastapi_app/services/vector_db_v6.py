"""Vector database service using LlamaIndex and Pinecone (v6.0.2)."""
import os
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from pinecone import Pinecone, ServerlessSpec
from llama_index.core import Document, Settings, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core.indices.vector_store import VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from models import CourseContent, Course

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Pinecone API key from environment
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
INDEX_NAME = "moodle-assistant"
CLOUD = "aws"  # AWS cloud for serverless
REGION = "us-west-2"  # US West 2 region for serverless


class VectorDBService:
    """Service for managing vector database operations using LlamaIndex and Pinecone v6.0.2."""

    def __init__(self):
        """Initialize the vector database service."""
        self.initialized = False
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
                    dimension=384,  # Default for MPNET base, adjust for other models
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud=CLOUD,
                        region=REGION
                    )
                )
                logger.info(f"Index '{INDEX_NAME}' created successfully")
            else:
                logger.info(f"Index '{INDEX_NAME}' already exists")
            
            # Set up LlamaIndex with HuggingFace embeddings
            embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-mpnet-base-v2")
            
            # Initialize settings
            Settings.embed_model = embed_model
            Settings.chunk_size = 1024
            Settings.chunk_overlap = 20
            
            # Connect to Pinecone index
            index = self.pc.Index(INDEX_NAME)
            self.vector_store = PineconeVectorStore(
                pinecone_index=index
            )
            
            # Create storage context
            storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
            
            # Create vector index
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                storage_context=storage_context
            )
            
            # Create node parser for chunking
            self.node_parser = SentenceSplitter(
                chunk_size=1024,
                chunk_overlap=20
            )
            
            self.initialized = True
            logger.info("Vector database service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector database service: {str(e)}")
            import traceback
            traceback.print_exc()

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
                
            # Create document
            document = Document(
                text=content.content_text,
                metadata={
                    "content_id": content.id,
                    "title": content.title,
                    "content_type": content.content_type,
                    "course_id": content.course_id,
                    "course_title": course_title,
                    "url": content.url
                }
            )
                
            # Parse document into nodes
            nodes = self.node_parser.get_nodes_from_documents([document])
            
            # Index nodes in vector store
            self.index.insert_nodes(nodes)
                
            return {
                "success": True,
                "content_id": content_id,
                "title": content.title,
                "nodes_count": len(nodes)
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
            use_hybrid_search: Whether to use hybrid search
            semantic_weight: Weight for semantic search (0-1)
            
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
            # Create query engine
            query_engine = self.index.as_query_engine()
            if use_hybrid_search:
                # Hybrid search not implemented yet
                pass
                
            # Filter query to specific course if provided
            if course_id:
                metadata_filters = {"course_id": course_id}
                query_engine = self.index.as_query_engine(
                    metadata_filters=metadata_filters
                )
                
            # Execute search
            query_result = query_engine.query(query)
            
            # Process results
            results = []
            source_nodes = query_result.source_nodes if hasattr(query_result, "source_nodes") else []
            for node in source_nodes:
                relevance_score = node.score if hasattr(node, "score") else 0.0
                results.append({
                    "content_id": node.metadata.get("content_id"),
                    "title": node.metadata.get("title"),
                    "content_type": node.metadata.get("content_type"),
                    "course_id": node.metadata.get("course_id"),
                    "course_title": node.metadata.get("course_title"),
                    "url": node.metadata.get("url"),
                    "relevance_score": float(relevance_score)
                })
            
            # Sort by relevance
            results = sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:limit]
            
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
            "cloud": CLOUD,
            "region": REGION
        }
        
        if self.initialized:
            try:
                # Get index stats from Pinecone using v6.0.2 API
                index = self.pc.Index(INDEX_NAME)
                stats = index.describe_index_stats()
                
                # Extract information
                status["document_count"] = stats.total_vector_count
                status["dimensions"] = 384  # Default dimension
                status["namespaces"] = stats.namespaces
            except Exception as e:
                status["error"] = str(e)
                
        return status


# Initialize service
vector_db_service = VectorDBService()