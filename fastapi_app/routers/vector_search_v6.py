"""Vector search API router for Pinecone v6.0.2."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.search import VectorSearchQuery, VectorSearchResponse
from ..services.vector_db_v6 import vector_db_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post("/vector-search", response_model=VectorSearchResponse)
async def vector_search(
    query: VectorSearchQuery,
    db: Session = Depends(get_db)
):
    """
    Perform vector-based semantic search on content.
    
    Args:
        query: Search query parameters
        db: Database session
        
    Returns:
        Search results
    """
    if not vector_db_service.initialized:
        raise HTTPException(
            status_code=503,
            detail="Vector search service is not initialized"
        )
        
    try:
        results = vector_db_service.search(
            query=query.query,
            course_id=query.course_id,
            limit=query.limit,
            use_hybrid_search=query.use_hybrid_search,
            semantic_weight=query.semantic_weight
        )
        return results
    except Exception as e:
        logger.error(f"Error in vector search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error performing vector search: {str(e)}"
        )


@router.post("/index-content/{content_id}")
async def index_content(
    content_id: int,
    db: Session = Depends(get_db)
):
    """
    Index a specific piece of content in the vector database.
    
    Args:
        content_id: ID of content to index
        db: Database session
        
    Returns:
        Indexing result
    """
    if not vector_db_service.initialized:
        raise HTTPException(
            status_code=503,
            detail="Vector search service is not initialized"
        )
        
    try:
        result = vector_db_service.index_content(db, content_id)
        if not result.get("success", False):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Unknown error indexing content")
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error indexing content {content_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error indexing content: {str(e)}"
        )


@router.post("/batch-index")
async def batch_index(
    course_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Batch index content in the vector database.
    
    Args:
        course_id: Optional course ID to filter content
        db: Database session
        
    Returns:
        Batch indexing result
    """
    if not vector_db_service.initialized:
        raise HTTPException(
            status_code=503,
            detail="Vector search service is not initialized"
        )
        
    try:
        result = vector_db_service.batch_index(db, course_id)
        if not result.get("success", False):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Unknown error in batch indexing")
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch indexing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in batch indexing: {str(e)}"
        )


@router.get("/similar-content/{content_id}")
async def get_similar_content(
    content_id: int,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Get content similar to specified content using vector similarity.
    
    Args:
        content_id: Content ID to find similar content for
        limit: Maximum number of similar content items
        db: Database session
        
    Returns:
        List of similar content items
    """
    if not vector_db_service.initialized:
        raise HTTPException(
            status_code=503,
            detail="Vector search service is not initialized"
        )
        
    try:
        results = vector_db_service.get_similar_content(content_id, db, limit)
        return {"content_id": content_id, "similar_content": results}
    except Exception as e:
        logger.error(f"Error getting similar content: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting similar content: {str(e)}"
        )


@router.get("/status")
async def get_status():
    """
    Get vector database status.
    
    Returns:
        Status information
    """
    try:
        status = vector_db_service.get_status()
        return status
    except Exception as e:
        logger.error(f"Error getting vector database status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting vector database status: {str(e)}"
        )