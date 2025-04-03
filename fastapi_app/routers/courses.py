"""Courses API router."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from models import Course, CourseContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get("/courses")
async def get_courses(db: Session = Depends(get_db)):
    """
    Get all available courses.
    
    Args:
        db: Database session
        
    Returns:
        List of courses
    """
    try:
        courses = db.query(Course).all()
        return {
            "courses": [
                {
                    "id": course.id,
                    "moodle_course_id": course.moodle_course_id,
                    "title": course.title,
                    "description": course.description
                }
                for course in courses
            ]
        }
    except Exception as e:
        logger.error(f"Error getting courses: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting courses: {str(e)}"
        )


@router.get("/courses/{course_id}")
async def get_course(
    course_id: int,
    db: Session = Depends(get_db)
):
    """
    Get details of a specific course.
    
    Args:
        course_id: Course ID
        db: Database session
        
    Returns:
        Course details
    """
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=404,
                detail=f"Course with ID {course_id} not found"
            )
            
        return {
            "id": course.id,
            "moodle_course_id": course.moodle_course_id,
            "title": course.title,
            "description": course.description
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting course: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting course: {str(e)}"
        )


@router.get("/courses/{course_id}/content")
async def get_course_content(
    course_id: int,
    content_type: str = None,
    db: Session = Depends(get_db)
):
    """
    Get content for a specific course.
    
    Args:
        course_id: Course ID
        content_type: Optional filter by content type
        db: Database session
        
    Returns:
        Course content
    """
    try:
        # Check if course exists
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=404,
                detail=f"Course with ID {course_id} not found"
            )
            
        # Query content
        query = db.query(CourseContent).filter(CourseContent.course_id == course_id)
        if content_type:
            query = query.filter(CourseContent.content_type == content_type)
            
        content_items = query.all()
        
        return {
            "course_id": course_id,
            "course_title": course.title,
            "content_type_filter": content_type,
            "content_items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "content_type": item.content_type,
                    "summary": item.content_text[:200] + "..." if item.content_text and len(item.content_text) > 200 else item.content_text,
                    "url": item.url
                }
                for item in content_items
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting course content: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting course content: {str(e)}"
        )


@router.get("/content/{content_id}")
async def get_content_item(
    content_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific content item.
    
    Args:
        content_id: Content ID
        db: Database session
        
    Returns:
        Content item details
    """
    try:
        content = db.query(CourseContent).filter(CourseContent.id == content_id).first()
        if not content:
            raise HTTPException(
                status_code=404,
                detail=f"Content with ID {content_id} not found"
            )
            
        # Get course
        course = db.query(Course).filter(Course.id == content.course_id).first()
            
        return {
            "id": content.id,
            "title": content.title,
            "content_type": content.content_type,
            "content_text": content.content_text,
            "url": content.url,
            "course_id": content.course_id,
            "course_title": course.title if course else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting content item: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting content item: {str(e)}"
        )


@router.post("/courses/{course_id}/content")
async def add_course_content(
    course_id: int,
    title: str,
    content_type: str,
    content_text: str = None,
    url: str = None,
    db: Session = Depends(get_db)
):
    """
    Add content to a course.
    
    Args:
        course_id: Course ID
        title: Content title
        content_type: Content type (document, video, quiz, etc.)
        content_text: Optional content text
        url: Optional content URL
        db: Database session
        
    Returns:
        Added content details
    """
    try:
        # Check if course exists
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=404,
                detail=f"Course with ID {course_id} not found"
            )
            
        # Create content
        content = CourseContent(
            course_id=course_id,
            title=title,
            content_type=content_type,
            content_text=content_text,
            url=url
        )
        db.add(content)
        db.commit()
        
        return {
            "id": content.id,
            "course_id": content.course_id,
            "title": content.title,
            "content_type": content.content_type,
            "url": content.url,
            "message": f"Content '{title}' added to course '{course.title}'"
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding course content: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error adding course content: {str(e)}"
        )