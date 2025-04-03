"""Video transcription API router."""
import logging
import os
import tempfile
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.transcription import (
    VideoProcessRequest, 
    BatchProcessRequest, 
    BatchProcessResponse,
    VideoUploadResponse,
    TranscriptionResult
)
from models import CourseContent, Course

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post("/video/process", response_model=TranscriptionResult)
async def process_video(
    request: VideoProcessRequest,
    db: Session = Depends(get_db)
):
    """
    Process a video for transcription.
    
    Args:
        request: Video processing request
        db: Database session
        
    Returns:
        Transcription result
    """
    try:
        # Get content
        content = db.query(CourseContent).filter(
            CourseContent.id == request.content_id,
            CourseContent.content_type == "video"
        ).first()
        
        if not content:
            raise HTTPException(
                status_code=404,
                detail=f"Video content with ID {request.content_id} not found"
            )
            
        # Check if URL exists
        if not content.url:
            return TranscriptionResult(
                content_id=content.id,
                title=content.title,
                transcript="",
                status="error",
                message="No video URL provided"
            )
            
        # In a real implementation, call Whisper API or local model to transcribe
        # For now, create a placeholder transcript
        transcript = f"This is a placeholder transcript for {content.title}."
        
        # Update content with transcript
        content.content_text = transcript
        db.commit()
        
        return TranscriptionResult(
            content_id=content.id,
            title=content.title,
            transcript=transcript,
            status="completed",
            duration=120.0,  # Placeholder duration
            language="en"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing video: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing video: {str(e)}"
        )


@router.post("/video/upload", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    course_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a video file and add it as course content.
    
    Args:
        file: Video file
        course_id: Course ID
        title: Video title
        description: Video description
        db: Database session
        
    Returns:
        Upload result
    """
    try:
        # Check if course exists
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=404,
                detail=f"Course with ID {course_id} not found"
            )
            
        # Create uploads directory if it doesn't exist
        uploads_dir = Path("static/uploads")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a unique filename
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"video_{course_id}_{title.replace(' ', '_')}{file_extension}"
        file_path = uploads_dir / filename
        
        # Save the file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        # Create content record
        video_content = CourseContent(
            course_id=course_id,
            title=title,
            content_type="video",
            content_text=description,
            url=f"/static/uploads/{filename}"
        )
        db.add(video_content)
        db.commit()
        
        return VideoUploadResponse(
            content_id=video_content.id,
            title=title,
            course_id=course_id,
            status="uploaded",
            message=f"Video uploaded successfully: {title}"
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading video: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading video: {str(e)}"
        )


@router.post("/video/batch-process", response_model=BatchProcessResponse)
async def batch_process_videos(
    request: BatchProcessRequest,
    db: Session = Depends(get_db)
):
    """
    Batch process all videos in a course.
    
    Args:
        request: Batch processing request
        db: Database session
        
    Returns:
        Batch processing result
    """
    try:
        # Check if course exists
        course = db.query(Course).filter(Course.id == request.course_id).first()
        if not course:
            raise HTTPException(
                status_code=404,
                detail=f"Course with ID {request.course_id} not found"
            )
            
        # Get all video content for the course
        videos = db.query(CourseContent).filter(
            CourseContent.course_id == request.course_id,
            CourseContent.content_type == "video"
        )
        
        if not request.force_reprocess:
            # Skip already processed videos (has content_text)
            videos = videos.filter(
                (CourseContent.content_text == None) | 
                (CourseContent.content_text == "")
            )
            
        videos = videos.all()
        
        if not videos:
            return BatchProcessResponse(
                course_id=request.course_id,
                videos_found=0,
                videos_processed=0,
                status="completed",
                message="No videos found to process"
            )
            
        # Process each video
        processed_count = 0
        for video in videos:
            try:
                # In a real implementation, call Whisper API or local model
                # For now, create a placeholder transcript
                if video.url:
                    transcript = f"This is a placeholder transcript for {video.title}."
                    video.content_text = transcript
                    processed_count += 1
            except Exception as video_error:
                # Log error but continue with other videos
                logger.error(f"Error processing video {video.id}: {str(video_error)}")
                
        db.commit()
        
        return BatchProcessResponse(
            course_id=request.course_id,
            videos_found=len(videos),
            videos_processed=processed_count,
            status="completed",
            message=f"Processed {processed_count} of {len(videos)} videos"
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in batch processing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in batch processing: {str(e)}"
        )


@router.get("/videos")
async def get_videos(
    course_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Get all video content, optionally filtered by course.
    
    Args:
        course_id: Optional course ID filter
        db: Database session
        
    Returns:
        List of videos
    """
    try:
        # Base query
        query = db.query(CourseContent, Course).join(
            Course, CourseContent.course_id == Course.id
        ).filter(
            CourseContent.content_type == "video"
        )
        
        if course_id:
            query = query.filter(CourseContent.course_id == course_id)
            
        videos = query.all()
        
        # Format response
        results = []
        for content, course in videos:
            results.append({
                "id": content.id,
                "title": content.title,
                "url": content.url,
                "course_id": course.id,
                "course_title": course.title,
                "has_transcript": bool(content.content_text),
                "transcript_length": len(content.content_text) if content.content_text else 0
            })
            
        return {
            "videos": results,
            "total": len(results),
            "course_id": course_id
        }
    except Exception as e:
        logger.error(f"Error getting videos: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting videos: {str(e)}"
        )