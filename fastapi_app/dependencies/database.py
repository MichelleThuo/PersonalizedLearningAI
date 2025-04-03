"""Database dependencies for FastAPI."""
from fastapi_app.database import SessionLocal

def get_db():
    """
    Get database session.
    
    Returns:
        Database session
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()