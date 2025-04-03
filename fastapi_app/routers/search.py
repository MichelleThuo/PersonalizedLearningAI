"""Search API router with enhanced capabilities."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.search import SearchQuery, SearchResponse
from ..services.search import search_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search(
    query: SearchQuery,
    db: Session = Depends(get_db)
):
    """
    Search for content matching the query.
    
    Args:
        query: Search query parameters
        db: Database session
        
    Returns:
        Search results
    """
    try:
        results = search_service.search(
            db=db,
            query=query.query,
            course_id=query.course_id,
            limit=query.limit,
            use_vector_search=True  # Always try vector search first
        )
        return results
    except Exception as e:
        logger.error(f"Error in search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error performing search: {str(e)}"
        )


@router.post("/index/{content_id}")
async def index_content(
    content_id: int,
    db: Session = Depends(get_db)
):
    """
    Index a specific piece of content for searching.
    
    Args:
        content_id: ID of content to index
        db: Database session
        
    Returns:
        Indexing result
    """
    try:
        result = search_service.index_content(db, content_id)
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
    Batch index content for searching.
    
    Args:
        course_id: Optional course ID to filter content
        db: Database session
        
    Returns:
        Batch indexing result
    """
    try:
        result = search_service.batch_index(db, course_id)
        if not result.get("success", False) and "error" in result:
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


@router.get("/similar/{content_id}")
async def get_similar_content(
    content_id: int,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Get content similar to specified content.
    
    Args:
        content_id: Content ID to find similar content for
        limit: Maximum number of similar content items
        db: Database session
        
    Returns:
        List of similar content items
    """
    try:
        results = search_service.get_similar_content(db, content_id, limit)
        return {"content_id": content_id, "similar_content": results}
    except Exception as e:
        logger.error(f"Error getting similar content: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting similar content: {str(e)}"
        )