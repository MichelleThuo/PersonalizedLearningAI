"""
Video Transcription Service
Provides functionality to transcribe video content using Whisper
"""
import os
import tempfile
import logging
from pathlib import Path
import whisper
import ffmpeg
from pydub import AudioSegment

from app import db
from models import CourseContent, SearchIndex

class TranscriptionService:
    """Service for transcribing video content"""
    
    def __init__(self):
        """Initialize the transcription service with Whisper model"""
        self.model = None
        # Default to a smaller model for faster processing
        self.model_size = "base"
        logging.info(f"Initializing TranscriptionService with model size: {self.model_size}")
    
    def _load_model(self):
        """Lazy-load the Whisper model when needed"""
        if self.model is None:
            logging.info(f"Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size)
        return self.model
    
    def transcribe_video(self, video_path):
        """
        Transcribe a video file using Whisper
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            str: Transcribed text or error message
        """
        try:
            logging.info(f"Starting transcription for video: {video_path}")
            
            # Check if file exists
            if not os.path.exists(video_path):
                logging.error(f"Video file not found: {video_path}")
                return "Error: Video file not found"
            
            # Extract audio from video
            audio_path = self._extract_audio(video_path)
            if audio_path.startswith("Error:"):
                return audio_path
            
            # Transcribe audio
            model = self._load_model()
            result = model.transcribe(audio_path)
            
            # Clean up temporary audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)
                
            logging.info(f"Transcription completed for video: {video_path}")
            return result["text"]
            
        except Exception as e:
            logging.error(f"Error transcribing video: {str(e)}")
            return f"Error: {str(e)}"
    
    def _extract_audio(self, video_path):
        """
        Extract audio from video file
        
        Args:
            video_path (str): Path to the video file
            
        Returns:
            str: Path to extracted audio file or error message
        """
        try:
            logging.info(f"Extracting audio from video: {video_path}")
            
            # Create temporary file for the audio
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_file.close()
            temp_audio_path = temp_file.name
            
            # Use FFmpeg to extract audio
            video = AudioSegment.from_file(video_path)
            video.export(temp_audio_path, format="wav")
            
            logging.info(f"Audio extracted to: {temp_audio_path}")
            return temp_audio_path
            
        except Exception as e:
            logging.error(f"Error extracting audio: {str(e)}")
            return f"Error: {str(e)}"
    
    def process_video_content(self, content_id):
        """
        Process video content from CourseContent
        
        Args:
            content_id (int): ID of the CourseContent
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logging.info(f"Processing video content with ID: {content_id}")
            
            # Get the content from database
            content = CourseContent.query.get(content_id)
            if not content:
                logging.error(f"Content not found with ID: {content_id}")
                return False
            
            # Skip if not a video
            if content.content_type != 'video':
                logging.info(f"Content is not a video. Type: {content.content_type}")
                return False
            
            # Get video path from URL
            video_path = content.url
            if not video_path or not video_path.strip():
                logging.error(f"No video URL specified for content ID: {content_id}")
                return False
            
            # Check if it's a local path or URL
            is_local_path = os.path.exists(video_path)
            
            if is_local_path:
                # Transcribe the video
                transcription = self.transcribe_video(video_path)
                if transcription.startswith("Error:"):
                    logging.error(transcription)
                    return False
                
                # Update content with transcription
                content.content_text = transcription
                
                # Update search index
                search_index = SearchIndex.query.filter_by(content_id=content_id).first()
                if search_index:
                    search_index.indexed_text = transcription
                else:
                    search_index = SearchIndex(content_id=content_id, indexed_text=transcription)
                    db.session.add(search_index)
                
                db.session.commit()
                logging.info(f"Transcription updated for content ID: {content_id}")
                return True
            else:
                logging.error(f"Video path is not a local file: {video_path}")
                return False
                
        except Exception as e:
            logging.error(f"Error processing video content: {str(e)}")
            db.session.rollback()
            return False