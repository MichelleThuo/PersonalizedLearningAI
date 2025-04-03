"""Schema definitions for chat-related API endpoints."""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    """Base schema for chat messages."""
    is_user: bool = Field(..., description="True if message is from user, False if from AI")
    message: str = Field(..., description="Message content")


class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    pass


class Message(MessageBase):
    """Schema for a message with ID and timestamp."""
    id: int
    session_id: int
    timestamp: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class ChatSessionBase(BaseModel):
    """Base schema for chat sessions."""
    course_id: Optional[int] = Field(None, description="Optional course ID for context")


class ChatSessionCreate(ChatSessionBase):
    """Schema for creating a new chat session."""
    pass


class ChatSession(ChatSessionBase):
    """Schema for a chat session with ID, user_id, and timestamps."""
    id: int
    user_id: int
    start_time: datetime
    messages: List[Message] = []

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class ChatRequest(BaseModel):
    """Schema for chat request payload."""
    session_id: Optional[int] = Field(None, description="Existing session ID or None for new session")
    message: str = Field(..., description="User message")
    course_id: Optional[int] = Field(None, description="Optional course ID for context")


class ChatResponse(BaseModel):
    """Schema for chat response payload."""
    session_id: int = Field(..., description="Chat session ID")
    response: str = Field(..., description="AI response message")
    context_used: Optional[bool] = Field(False, description="Whether context was used for response")
    relevant_content: Optional[List[dict]] = Field(None, description="Relevant content used for context")