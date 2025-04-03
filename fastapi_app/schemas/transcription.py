"""Schema definitions for video transcription API endpoints."""
from typing import Optional
from pydantic import BaseModel, Field


class VideoProcessRequest(BaseModel):
    """Schema for video processing request."""
    content_id: int = Field(..., description="Course content ID of the video to process")


class VideoUploadResponse(BaseModel):
    """Schema for video upload response."""
    content_id: int = Field(..., description="Created content ID for the video")
    title: str = Field(..., description="Video title")
    course_id: int = Field(..., description="Course ID")
    status: str = Field(..., description="Upload status")
    message: str = Field(..., description="Status message")


class BatchProcessRequest(BaseModel):
    """Schema for batch video processing request."""
    course_id: int = Field(..., description="Course ID to process all videos")
    force_reprocess: bool = Field(False, description="Whether to reprocess already processed videos")


class BatchProcessResponse(BaseModel):
    """Schema for batch video processing response."""
    course_id: int = Field(..., description="Course ID")
    videos_found: int = Field(..., description="Number of videos found")
    videos_processed: int = Field(..., description="Number of videos queued for processing")
    status: str = Field(..., description="Batch processing status")
    message: str = Field(..., description="Status message")


class TranscriptionResult(BaseModel):
    """Schema for transcription result."""
    content_id: int = Field(..., description="Course content ID")
    title: str = Field(..., description="Video title")
    transcript: str = Field(..., description="Full transcript text")
    status: str = Field(..., description="Transcription status")
    message: Optional[str] = Field(None, description="Status message")
    duration: Optional[float] = Field(None, description="Video duration in seconds")
    language: Optional[str] = Field(None, description="Detected language")