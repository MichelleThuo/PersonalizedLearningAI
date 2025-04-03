"""
Standalone FastAPI application for the Moodle Learning Assistant.
This runs just the FastAPI parts without the Flask dependencies.
"""
import os
import uvicorn
from fastapi_app.main import app as fastapi_app

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 5000))
    
    # Start with uvicorn
    uvicorn.run(
        "fastapi_app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )