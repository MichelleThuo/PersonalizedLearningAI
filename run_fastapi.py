"""
Run the FastAPI application directly.
This script is used for testing the FastAPI components separately.
"""
import os
import uvicorn

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 5001))  # Use a different port to avoid conflict
    
    # Start with uvicorn
    uvicorn.run(
        "fastapi_app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )