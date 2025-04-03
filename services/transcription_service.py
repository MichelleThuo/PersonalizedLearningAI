"""
Video Transcription Service
Provides functionality to transcribe video content using Whisper
"""
import os
import logging
import tempfile
from pathlib import Path

import whisper
import ffmpeg
from pydub import AudioSegment
from flask import current_app
from models import CourseContent
from app import db

logger = logging.getLogger(__name__)

class TranscriptionService:
    """Service for transcribing video content"""
    
    def __init__(self):
        """Initialize the transcription service"""
        self.model = None
        self.model_name = "base"  # Can be tiny, base, small, medium, large
    
    def _load_model(self):
        """Lazy-load the Whisper model when needed"""
        if self.model is None:
            try:
                logger.info(f"Loading Whisper model '{self.model_name}'...")
                self.model = whisper.load_model(self.model_name)
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading Whisper model: {str(e)}")
                return False
        return True
    
    def transcribe_video(self, video_path):
        """
        Transcribe a video file using Whisper
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            str: Transcribed text or error message
        """
        try:
            # Load model if not already loaded
            if not self._load_model():
                return None
            
            # Extract audio from video
            audio_path = self._extract_audio(video_path)
            if not audio_path:
                logger.error("Failed to extract audio from video")
                return None
            
            # Transcribe the audio
            logger.info(f"Transcribing audio: {audio_path}")
            result = self.model.transcribe(audio_path)
            
            # Clean up temporary audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            return result.get("text", "")
            
        except Exception as e:
            logger.error(f"Error transcribing video: {str(e)}")
            return None
    
    def _extract_audio(self, video_path):
        """
        Extract audio from video file
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            str: Path to extracted audio file or None if failed
        """
        try:
            # Create temporary file for the extracted audio
            temp_dir = tempfile.gettempdir()
            audio_path = os.path.join(temp_dir, f"audio_{os.path.basename(video_path)}.mp3")
            
            # Extract audio using ffmpeg
            logger.info(f"Extracting audio from {video_path} to {audio_path}")
            
            try:
                # First try with ffmpeg-python library
                (
                    ffmpeg
                    .input(video_path)
                    .output(audio_path, acodec='mp3', ab='128k', ac=1, ar='16k')
                    .run(quiet=True, overwrite_output=True)
                )
            except Exception as e:
                logger.warning(f"ffmpeg-python failed: {str(e)}, trying with pydub")
                
                # Fallback to pydub
                try:
                    video = AudioSegment.from_file(video_path)
                    video.export(audio_path, format="mp3")
                except Exception as e2:
                    logger.error(f"pydub also failed: {str(e2)}")
                    return None
            
            if os.path.exists(audio_path):
                return audio_path
            else:
                logger.error("Audio extraction completed but file doesn't exist")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            return None
    
    def process_video_content(self, content_id):
        """
        Process video content from CourseContent
        
        Args:
            content_id (int): ID of the CourseContent
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the content from the database
            content = CourseContent.query.get(content_id)
            if not content:
                logger.error(f"Content with ID {content_id} not found")
                return False
            
            if content.content_type != 'video':
                logger.error(f"Content with ID {content_id} is not a video")
                return False
            
            # Get the full path to the video file
            video_path = os.path.join(current_app.root_path, content.url)
            logger.info(f"Processing video: {video_path}")
            
            if not os.path.exists(video_path):
                logger.error(f"Video file not found: {video_path}")
                return False
            
            # Transcribe the video
            transcription = self.transcribe_video(video_path)
            if not transcription:
                logger.error("Transcription failed")
                return False
            
            # Save the transcription to the database
            content.content_text = transcription
            db.session.commit()
            
            logger.info(f"Successfully transcribed video ID {content_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing video content: {str(e)}")
            db.session.rollback()
            return False