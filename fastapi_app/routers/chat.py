"""Chat API router with LlamaIndex-enhanced context retrieval."""
import logging
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.chat import ChatRequest, ChatResponse
from ..services.search import search_service
from models import ChatSession, ChatMessage, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for HF_API_TOKEN
HF_API_TOKEN = os.environ.get("HF_API_TOKEN")
if not HF_API_TOKEN:
    logger.warning("HF_API_TOKEN not found in environment variables")

# Create router
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Process a chat message and return AI response.
    
    Args:
        request: Chat request with message and session info
        db: Database session
        
    Returns:
        AI response
    """
    try:
        # Check if API token is available
        if not HF_API_TOKEN:
            raise HTTPException(
                status_code=503,
                detail="Hugging Face API token not configured"
            )
            
        # Get or create chat session
        session = None
        if request.session_id:
            session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
            if not session:
                raise HTTPException(
                    status_code=404,
                    detail=f"Chat session with ID {request.session_id} not found"
                )
        else:
            # Default user ID for now - this should be obtained from authentication
            default_user_id = 1
            # Check if user exists
            user = db.query(User).filter(User.id == default_user_id).first()
            if not user:
                # Create a default user if none exists
                user = User(
                    id=default_user_id,
                    username="default_user",
                    email="default@example.com"
                )
                db.add(user)
                db.flush()
                
            # Create new session
            session = ChatSession(
                user_id=default_user_id,
                course_id=request.course_id,
                start_time=datetime.utcnow()
            )
            db.add(session)
            db.flush()  # Flush to get session ID
            
        # Store user message
        user_message = ChatMessage(
            session_id=session.id,
            is_user=True,
            message=request.message,
            timestamp=datetime.utcnow()
        )
        db.add(user_message)
        
        # Get relevant content for context
        context_used = False
        context = ""
        relevant_content = []
        
        try:
            context = search_service.get_relevant_content(
                db=db,
                query=request.message,
                course_id=request.course_id,
                limit=3
            )
            
            if context:
                context_used = True
                # For demonstration, extract content titles for response
                # In a real implementation, you'd use the context in the AI prompt
                lines = context.split("\n\n")
                for line in lines:
                    if line.startswith("Content:"):
                        title = line.split("\n")[0].replace("Content:", "").strip()
                        snippet = "\n".join(line.split("\n")[1:])
                        relevant_content.append({
                            "title": title,
                            "snippet": snippet
                        })
        except Exception as context_error:
            logger.error(f"Error getting context: {str(context_error)}")
            # Continue without context if there's an error
        
        # In a real implementation, call Hugging Face API here
        # For now, generate a simple response
        if context_used:
            ai_response = (
                f"I've found some relevant information that might help answer your question. "
                f"Based on our learning materials: {request.message}"
            )
        else:
            ai_response = f"I don't have specific information about that, but I'll do my best to help: {request.message}"
        
        # Store AI response
        ai_message = ChatMessage(
            session_id=session.id,
            is_user=False,
            message=ai_response,
            timestamp=datetime.utcnow()
        )
        db.add(ai_message)
        
        # Commit all changes
        db.commit()
        
        return ChatResponse(
            session_id=session.id,
            response=ai_response,
            context_used=context_used,
            relevant_content=relevant_content if relevant_content else None
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )


@router.get("/chat/history/{session_id}")
async def get_chat_history(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Get chat history for a session.
    
    Args:
        session_id: Chat session ID
        db: Database session
        
    Returns:
        Chat history with messages
    """
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Chat session with ID {session_id} not found"
            )
            
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(
            ChatMessage.timestamp
        ).all()
        
        return {
            "session_id": session.id,
            "user_id": session.user_id,
            "course_id": session.course_id,
            "start_time": session.start_time,
            "messages": [
                {
                    "id": msg.id,
                    "is_user": msg.is_user,
                    "message": msg.message,
                    "timestamp": msg.timestamp
                }
                for msg in messages
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting chat history: {str(e)}"
        )


@router.post("/chat/sessions")
async def create_chat_session(
    course_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Create a new chat session.
    
    Args:
        course_id: Optional course ID for context
        db: Database session
        
    Returns:
        New chat session details
    """
    try:
        # Default user ID for now - this should be obtained from authentication
        default_user_id = 1
        # Check if user exists
        user = db.query(User).filter(User.id == default_user_id).first()
        if not user:
            # Create a default user if none exists
            user = User(
                id=default_user_id,
                username="default_user",
                email="default@example.com"
            )
            db.add(user)
            db.flush()
            
        # Create new session
        session = ChatSession(
            user_id=default_user_id,
            course_id=course_id,
            start_time=datetime.utcnow()
        )
        db.add(session)
        db.commit()
        
        return {
            "session_id": session.id,
            "user_id": session.user_id,
            "course_id": session.course_id,
            "start_time": session.start_time
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating chat session: {str(e)}"
        )