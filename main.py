"""Main entry point for the Moodle Learning Assistant application."""
import os
import logging
import uvicorn
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the Flask app and FastAPI app
from app import app as flask_app
from fastapi_app.main import app as fastapi_app

# Create a unified FastAPI app that includes both the original Flask app
# and the new FastAPI functionality
combined_app = FastAPI(
    title="Moodle Learning Assistant",
    description="Combined Flask and FastAPI application with enhanced semantic search capabilities",
    version="1.0.0"
)

# Mount the Flask app for backward compatibility and gradual migration
combined_app.mount("/flask", WSGIMiddleware(flask_app), name="flask_app")

# Redirect root to FastAPI by default
@combined_app.get("/")
async def root(request: Request):
    """Redirect root to FastAPI app."""
    return RedirectResponse(url="/api/docs")

# Include all FastAPI routes
combined_app.include_router(fastapi_app.router)

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 5000))
    
    # Start with uvicorn
    uvicorn.run(
        "main:combined_app",
        host="0.0.0.0",
        port=port,
        reload=True
    )