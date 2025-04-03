import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///moodle_assistant.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# API configuration for language models
app.config["HF_API_TOKEN"] = os.environ.get("HF_API_TOKEN")  # For Hugging Face models
app.config["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY")  # Kept for compatibility

# Moodle LMS integration configuration
app.config["MOODLE_BASE_URL"] = os.environ.get("MOODLE_BASE_URL", "")
app.config["MOODLE_API_TOKEN"] = os.environ.get("MOODLE_API_TOKEN", "")

# Initialize the app with the database extension
db.init_app(app)

# Register blueprints
with app.app_context():
    # Import models and create tables
    import models  # noqa: F401
    
    # Import and register route blueprints
    from routes.views import views_bp
    from routes.api import api_bp
    from routes.moodle import moodle_bp
    from routes.h5p import h5p_bp
    from routes.transcription import transcription_bp
    from routes.vector_db import vector_db_bp
    
    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(moodle_bp, url_prefix="/api/moodle")
    app.register_blueprint(h5p_bp, url_prefix="/api/h5p")
    app.register_blueprint(transcription_bp)
    app.register_blueprint(vector_db_bp)
    
    # Create all database tables
    db.create_all()
