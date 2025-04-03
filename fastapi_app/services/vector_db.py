"""Vector database service using LlamaIndex and Pinecone."""
import os
import logging
from typing import List, Dict, Any, Optional
import pinecone
from sqlalchemy.orm import Session
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
PINECONE_ENVIRONMENT = "gcp-starter"  # Update as needed
INDEX_NAME = "moodle-assistant"


class VectorDBService:
    """Service for managing vector database operations using LlamaIndex."""

    def __init__(self):
        """Initialize the vector database service."""
        self.initialized = False
        try:
            # Initialize Pinecone
            if not PINECONE_API_KEY:
                logger.warning("PINECONE_API_KEY not found in environment variables")
                return
                
            # Initialize Pinecone with pinecone-client v2.2.2
            pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
            
            # Check if index exists, if not create it
            index_list = pinecone.list_indexes()
            if INDEX_NAME not in index_list:
                logger.info(f"Creating Pinecone index: {INDEX_NAME}")
                pinecone.create_index(
                    name=INDEX_NAME,
                    dimension=384,  # Default for MPNET base, adjust for other models
                    metric="cosine"
                )
            
            # Set up LlamaIndex with HuggingFace embeddings
            embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-mpnet-base-v2")
            
            # Initialize settings
            Settings.embed_model = embed_model
            Settings.chunk_size = 1024
            Settings.chunk_overlap = 20
            
            # Connect to Pinecone index
            index = pinecone.Index(INDEX_NAME)
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

    def index_content(self, db: Session, content_id: int) -> Dict[str, Any]:
        """
        Index a specific piece of course content.
        
        Args:
            db: Database session
            content_id: ID of content to index
            
        Returns:
            Dict with indexing result
        """
        if not self.initialized:
            return {"success": False, "error": "Vector database not initialized"}
            
        try:
            # Get content from database
            content = db.query(CourseContent).filter(CourseContent.id == content_id).first()
            if not content:
                return {"success": False, "error": f"Content with ID {content_id} not found"}
                
            # Get course information
            course = db.query(Course).filter(Course.id == content.course_id).first()
            if not course:
                return {"success": False, "error": f"Course with ID {content.course_id} not found"}
                
            # Create metadata
            metadata = {
                "content_id": content.id,
                "course_id": content.course_id,
                "course_title": course.title,
                "title": content.title,
                "content_type": content.content_type
            }
            
            # Create document
            document = Document(
                text=content.content_text,
                metadata=metadata
            )
            
            # Parse nodes (chunking)
            nodes = self.node_parser.get_nodes_from_documents([document])
            
            # Index nodes
            self.index.insert_nodes(nodes)
            
            return {
                "success": True,
                "content_id": content.id,
                "title": content.title,
                "chunks": len(nodes),
                "message": f"Successfully indexed content: {content.title}"
            }
        except Exception as e:
            logger.error(f"Error indexing content {content_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    def batch_index(self, db: Session, course_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Batch index content, optionally filtered by course.
        
        Args:
            db: Database session
            course_id: Optional course ID to filter content
            
        Returns:
            Dict with indexing results
        """
        if not self.initialized:
            return {"success": False, "error": "Vector database not initialized"}
            
        try:
            # Query content
            query = db.query(CourseContent)
            
            if course_id:
                query = query.filter(CourseContent.course_id == course_id)
                
            contents = query.all()
            
            if not contents:
                message = f"No content found" if not course_id else f"No content found for course {course_id}"
                return {"success": False, "error": message}
                
            # Index each content
            results = []
            for content in contents:
                result = self.index_content(db, content.id)
                results.append(result)
                
            # Summarize results
            success_count = sum(1 for r in results if r["success"])
            
            return {
                "success": success_count > 0,
                "total": len(contents),
                "indexed": success_count,
                "failed": len(contents) - success_count,
                "results": results
            }
        except Exception as e:
            logger.error(f"Error in batch indexing: {str(e)}")
            return {"success": False, "error": str(e)}

    def search(
        self, 
        query: str, 
        course_id: Optional[int] = None, 
        limit: int = 10,
        use_hybrid_search: bool = True,
        semantic_weight: float = 0.7
    ) -> Dict[str, Any]:
        """
        Search for content using the vector database.
        
        Args:
            query: Search query
            course_id: Optional course ID to filter results
            limit: Maximum number of results
            use_hybrid_search: Whether to use hybrid search (vector + keyword)
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
                "error": "Vector database not initialized"
            }
            
        try:
            # Create query engine
            if use_hybrid_search:
                query_engine = self.index.as_query_engine(
                    similarity_top_k=limit * 2,  # Get more results than needed for filtering
                    filters={"course_id": course_id} if course_id else None,
                    alpha=semantic_weight  # Balance between semantic and keyword search
                )
            else:
                query_engine = self.index.as_query_engine(
                    similarity_top_k=limit * 2,
                    filters={"course_id": course_id} if course_id else None
                )
            
            # Execute query
            response = query_engine.query(query)
            
            # Process results
            results = []
            
            # Group nodes by content_id to avoid duplication
            grouped_nodes = {}
            for node in response.source_nodes:
                content_id = node.metadata.get("content_id")
                if content_id not in grouped_nodes:
                    grouped_nodes[content_id] = {
                        "node": node,
                        "score": node.score,
                        "text": node.text
                    }
                elif node.score > grouped_nodes[content_id]["score"]:
                    # Update if better score
                    grouped_nodes[content_id] = {
                        "node": node,
                        "score": node.score,
                        "text": node.text
                    }
            
            # Convert to result format
            for content_id, item in grouped_nodes.items():
                node = item["node"]
                results.append({
                    "id": int(node.metadata.get("content_id")),
                    "title": node.metadata.get("title"),
                    "content_type": node.metadata.get("content_type"),
                    "snippet": item["text"][:200] + "...",
                    "course_id": int(node.metadata.get("course_id")),
                    "course_title": node.metadata.get("course_title"),
                    "url": node.metadata.get("url"),
                    "relevance_score": float(item["score"])
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
        Get content similar to a specific piece of content.
        
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
            results = self.search(
                query=content.content_text[:1000],  # Use first 1000 chars to avoid token limits
                course_id=None,  # Don't limit to course to find cross-course connections
                limit=limit + 1  # Get extra to remove self
            )
            
            # Remove self from results
            filtered_results = [
                result for result in results.get("results", [])
                if result["id"] != content_id
            ][:limit]
            
            return filtered_results
        except Exception as e:
            logger.error(f"Error getting similar content: {str(e)}")
            return []

    def get_relevant_context(self, query: str, course_id: Optional[int] = None, limit: int = 3) -> str:
        """
        Get relevant context for a chat query to enhance AI responses.
        
        Args:
            query: User query
            course_id: Optional course ID to filter context
            limit: Maximum number of context items
            
        Returns:
            Consolidated context string from relevant documents
        """
        if not self.initialized:
            return ""
            
        try:
            # Search for relevant context
            search_results = self.search(
                query=query,
                course_id=course_id,
                limit=limit,
                use_hybrid_search=True,
                semantic_weight=0.8  # Higher semantic weight for context retrieval
            )
            
            # Extract content
            contexts = []
            for result in search_results.get("results", []):
                contexts.append(f"Content: {result['title']}\n{result['snippet']}")
                
            # Join contexts
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
            "index_name": INDEX_NAME
        }
        
        if self.initialized:
            try:
                # Get index stats from Pinecone using pinecone-client v2.2.2
                index = pinecone.Index(INDEX_NAME)
                stats = index.describe_index_stats()
                
                # Extract information based on pinecone-client v2.2.2 response format
                status["document_count"] = stats.get('total_vector_count', 0)
                status["dimensions"] = 384  # Default dimension
                namespace_stats = stats.get('namespaces', {})
                default_namespace = namespace_stats.get('', {})
                status["index_fullness"] = default_namespace.get('vector_count', 0)
            except Exception as e:
                status["error"] = str(e)
                
        return status


# Initialize service
vector_db_service = VectorDBService()