"""Main FastAPI application for the Moodle Learning Assistant."""
import os
import logging
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .database import engine, Base, get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title="Moodle Learning Assistant API",
    description="API for Moodle Learning Assistant with video transcription and semantic search",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates for server-side rendering if needed
templates = Jinja2Templates(directory="templates")

# Import models and create tables
from models import User, Course, CourseContent, ChatSession, ChatMessage, Quiz, QuizQuestion, QuizOption, SearchIndex  # noqa

# Import routers
from .routers import (
    chat, 
    search, 
    quiz, 
    courses, 
    transcription, 
    vector_search
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(quiz.router, prefix="/api", tags=["quiz"])
app.include_router(courses.router, prefix="/api", tags=["courses"])
app.include_router(transcription.router, prefix="/api", tags=["transcription"])
app.include_router(vector_search.router, prefix="/api", tags=["vector-search"])

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Initialize environment-dependent services
    logger.info("Starting application with environment: %s", os.environ.get("ENV", "development"))

@app.get("/", tags=["root"])
async def root(request: Request):
    """Render the homepage."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health", tags=["health"])
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Simple database connectivity check
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error("Health check failed: %s", str(e))
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}