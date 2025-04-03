# Moodle AI Learning Assistant: Code Structure Documentation

This document provides a detailed explanation of the file structure and purpose of each component in the project.

## Table of Contents

1. [Root Directory Files](#root-directory-files)
2. [Main Application Structure](#main-application-structure)
3. [FastAPI Application](#fastapi-application)
4. [Routes](#routes)
5. [Services](#services)
6. [Models](#models)
7. [Templates](#templates)
8. [Static Files](#static-files)
9. [Utility and Testing Files](#utility-and-testing-files)
10. [Configuration Files](#configuration-files)
11. [Documentation Files](#documentation-files)

## Root Directory Files

| File | Purpose |
|------|---------|
| `main.py` | The main entry point for the application. It initializes and runs the Flask application with FastAPI integration. |
| `app.py` | Sets up the Flask application, database configuration, and initializes SQLAlchemy. |
| `models.py` | Defines all SQLAlchemy database models (tables) for the application. |
| `run_fastapi.py` | A separate entry point for running just the FastAPI components independently. |
| `fastapi_standalone.py` | A standalone version of the FastAPI application without Flask dependencies. |

## Main Application Structure

### Core Files

#### `app.py`
The central Flask application setup file that:
- Initializes the Flask application
- Configures SQLAlchemy for database operations
- Sets up the database connection
- Creates database tables if they don't exist

```python
# Key components:
db = SQLAlchemy(model_class=Base)  # SQLAlchemy instance
app = Flask(__name__)  # Flask application
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")  # Database config
db.init_app(app)  # Initialize SQLAlchemy with Flask
```

#### `main.py`
The application entry point that:
- Imports the Flask app from app.py
- Registers all blueprints/routes
- Integrates FastAPI with Flask
- Runs the combined application

```python
# Key components:
app.mount("/api", fastapi_app, name="fastapi")  # Mount FastAPI at /api endpoint
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # Run the application
```

#### `models.py`
Defines all database tables using SQLAlchemy models:

```python
# Key models:
class User(UserMixin, db.Model):  # User accounts
class Course(db.Model):  # Course information
class CourseContent(db.Model):  # Content within courses
class ChatSession(db.Model):  # User chat sessions
class ChatMessage(db.Model):  # Individual chat messages
class Quiz(db.Model):  # Generated quizzes
class QuizQuestion(db.Model):  # Questions within quizzes
class QuizOption(db.Model):  # Answer options for questions
class SearchIndex(db.Model):  # Indexed content for search
```

## FastAPI Application

The `fastapi_app` directory contains the FastAPI-specific implementation.

### Structure

```
fastapi_app/
├── __init__.py         # Package initialization
├── main.py             # FastAPI application setup
├── database.py         # Database connection for FastAPI
├── dependencies/       # Dependency injection components
│   ├── __init__.py
│   └── database.py     # Database session dependencies
├── routers/            # API route definitions
│   ├── __init__.py
│   ├── chat.py         # Chat endpoints
│   ├── courses.py      # Course management endpoints
│   ├── quiz.py         # Quiz generation endpoints
│   ├── search.py       # Search functionality endpoints
│   ├── simple_vector_search.py  # Basic vector search implementation
│   ├── transcription.py         # Video transcription endpoints
│   ├── vector_search.py         # Advanced vector search endpoints
│   └── vector_search_v6.py      # Vector search with Pinecone v6 API
├── schemas/            # Pydantic data models
│   ├── __init__.py
│   ├── chat.py         # Chat request/response schemas
│   ├── search.py       # Search request/response schemas
│   └── transcription.py  # Transcription request/response schemas
└── services/           # Business logic implementations
    ├── __init__.py
    ├── search.py       # Search functionality
    ├── simple_vector_db.py  # Simple vector database implementation
    ├── vector_db.py    # Vector database operations
    └── vector_db_v6.py # Vector database with Pinecone v6 API
```

### Key FastAPI Files

#### `fastapi_app/main.py`
Sets up the FastAPI application with:
- Route registration
- Middleware configuration
- Startup/shutdown events
- Dependency injection setup

```python
# Key components:
app = FastAPI(title="Moodle Learning Assistant API")  # Create FastAPI instance
app.include_router(search_router)  # Register routes
app.include_router(chat_router)

@app.on_event("startup")
async def startup_event():
    # Initialize services on startup
```

#### `fastapi_app/routers/chat.py`
Defines API endpoints for the chat functionality:

```python
# Example endpoint:
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    # Process chat request and return response
```

#### `fastapi_app/schemas/search.py`
Defines Pydantic models for request/response validation:

```python
# Example schema:
class SearchRequest(BaseModel):
    query: str
    course_id: Optional[int] = None
    limit: int = 10
```

#### `fastapi_app/services/vector_db.py`
Implements the business logic for vector database operations:

```python
# Example implementation:
class VectorDBService:
    def __init__(self):
        # Initialize Pinecone client
        
    def search(self, query_vector, filter_params=None, top_k=5):
        # Perform vector similarity search
```

## Routes

The `routes` directory contains Flask blueprint definitions for the web interface routes.

### Structure

```
routes/
├── api.py             # General API endpoints
├── h5p.py             # H5P content generation routes
├── moodle.py          # Moodle integration routes
├── transcription.py   # Video transcription routes
├── vector_db.py       # Vector database routes
└── views.py           # Web interface view routes
```

### Key Route Files

#### `routes/views.py`
Defines the web interface routes:

```python
# Example route:
@views_bp.route('/')
def index():
    """Main page with overview of features"""
    return render_template('index.html')

@views_bp.route('/chat')
def chat():
    """Chat interface page"""
    return render_template('chat.html')
```

#### `routes/api.py`
Defines traditional Flask API endpoints:

```python
# Example endpoint:
@api_bp.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint for chatbot interactions"""
    data = request.json
    response = chat_service.get_response(data['message'], data.get('context'))
    return jsonify({'response': response})
```

#### `routes/moodle.py`
Handles Moodle LMS integration:

```python
# Example function:
@moodle_bp.route('/api/moodle/sync-course', methods=['POST'])
def sync_course():
    """Synchronize a Moodle course to the local database"""
    course_id = request.json.get('course_id')
    result = moodle_service.sync_course(course_id)
    return jsonify(result)
```

## Services

The `services` directory contains business logic implementations.

### Structure

```
services/
├── h5p_service.py          # H5P content generation
├── openai_service.py       # AI model integration
├── quiz_service.py         # Quiz generation
├── recommendation_service.py  # Course recommendations
├── search_service.py       # Search functionality
├── transcription_service.py  # Video transcription
└── vector_db_service.py    # Vector database operations
```

### Key Service Files

#### `services/openai_service.py`
Handles integration with AI models (using Hugging Face instead of OpenAI):

```python
class OpenAIService:
    def __init__(self):
        self.hf_api_token = os.environ.get("HF_API_TOKEN")
        self.hf_model = os.environ.get("HF_MODEL_NAME", "HuggingFaceH4/zephyr-7b-beta")
        
    def get_chat_response(self, messages, course_context=None):
        # Create prompt with context and messages
        # Call Hugging Face API
        # Process and return response
```

#### `services/recommendation_service.py`
Implements personalized recommendation algorithms:

```python
class RecommendationService:
    def __init__(self, db_session):
        self.db = db_session
        
    def get_recommendations_for_user(self, user_id, limit=5):
        # Get user history and preferences
        # Apply recommendation algorithm
        # Return personalized course recommendations
```

#### `services/h5p_service.py`
Handles generation of H5P interactive content:

```python
class H5PService:
    def __init__(self):
        # Initialize service
        
    def generate_interactive_content(self, content_text, content_type="course_presentation"):
        # Analyze content
        # Generate appropriate H5P structure
        # Create and return H5P package
```

## Models

The database models in `models.py` define the application's data structure.

### Key Models

#### `User`
Represents user accounts:

```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    moodle_user_id = db.Column(db.Integer, unique=True)
    
    # Relationships
    chat_sessions = db.relationship('ChatSession', backref='user', lazy='dynamic')
```

#### `Course`
Represents a course, potentially linked to Moodle:

```python
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    moodle_course_id = db.Column(db.Integer, unique=True, nullable=False)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    content = db.relationship('CourseContent', backref='course', lazy='dynamic')
```

#### `ChatSession` and `ChatMessage`
Track conversations between users and the AI:

```python
class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('ChatMessage', backref='session', lazy='dynamic')

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    is_user = db.Column(db.Boolean, default=True)  # True if from user, False if from AI
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
```

## Templates

The `templates` directory contains Jinja2 templates for the web interface.

### Structure

```
templates/
├── admin_dashboard.html    # Admin interface
├── base.html               # Base template for all pages
├── chat.html               # Chat interface
├── h5p.html                # H5P content generator
├── index.html              # Homepage
├── quiz.html               # Quiz interface
├── search.html             # Search interface
├── user_interface.html     # Learner interface
├── vector_status.html      # Vector database status
└── video.html              # Video processing interface
```

### Key Template Files

#### `templates/base.html`
The base template that all other templates extend:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Moodle AI Learning Assistant{% endblock %}</title>
    <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/custom.css') }}">
    {% block styles %}{% endblock %}
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <!-- Navigation elements -->
    </nav>
    
    <main class="container mt-4">
        {% block content %}{% endblock %}
    </main>
    
    <footer class="footer mt-5">
        <!-- Footer content -->
    </footer>
    
    {% block scripts %}{% endblock %}
</body>
</html>
```

#### `templates/user_interface.html`
The main learner interface:

```html
{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-md-8">
        <!-- Chat Interface -->
        <div class="card mb-4">
            <div class="card-header">
                <h5>AI Learning Assistant</h5>
            </div>
            <div class="card-body">
                <div id="chat-messages" class="mb-3">
                    <!-- Chat messages appear here -->
                </div>
                <form id="chat-form">
                    <div class="input-group">
                        <input type="text" id="message-input" class="form-control" placeholder="Ask a question...">
                        <button type="submit" class="btn btn-primary">Send</button>
                    </div>
                </form>
            </div>
        </div>
        
        <!-- Content area -->
    </div>
    
    <div class="col-md-4">
        <!-- Recommendations -->
        <div class="card mb-4">
            <div class="card-header">
                <h5>Recommended for You</h5>
            </div>
            <div class="card-body">
                <ul class="list-group" id="recommendations-list">
                    <!-- Recommendations appear here -->
                </ul>
            </div>
        </div>
        
        <!-- Learning progress -->
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/chatbot.js') }}"></script>
{% endblock %}
```

## Static Files

The `static` directory contains CSS, JavaScript, and other static assets.

### Structure

```
static/
├── css/
│   └── custom.css         # Custom CSS styles
├── h5p_content/           # Generated H5P packages
└── js/
    ├── chatbot.js         # Chat interface functionality
    ├── moodle-integration.js  # Moodle integration scripts
    ├── quiz.js            # Quiz interface functionality
    └── search.js          # Search functionality
```

### Key Static Files

#### `static/js/chatbot.js`
Handles the chat interface functionality:

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessage(message, true);
        messageInput.value = '';
        
        // Send message to API
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            // Add AI response to chat
            addMessage(data.response, false);
        })
        .catch(error => {
            console.error('Error:', error);
            addMessage('Sorry, there was an error processing your request.', false);
        });
    });
    
    function addMessage(text, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'user-message' : 'ai-message';
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
```

## Utility and Testing Files

The project includes various utility and testing files.

### Pinecone Testing Files

| File | Purpose |
|------|---------|
| `check_pinecone.py` | Verifies Pinecone API key and connection |
| `check_pinecone_v6.py` | Tests Pinecone with v6.0.2 API |
| `pinecone_example.py` | Example script for Pinecone API v2.2.2 |
| `pinecone_working_example.py` | Working example for Pinecone v6.0.2 |
| `pinecone_working_v6.py` | Working example with Pinecone v6.0.2 new API |
| `test_pinecone.py` | Test script for Pinecone v2.2.2 |
| `test_llama_pinecone_v6.py` | Tests LlamaIndex integration with Pinecone v6.0.2 |
| `test_simple_vector_db.py` | Tests the SimpleVectorDBService implementation |

### Example Usage

#### `check_pinecone.py`
Verifies that the Pinecone API key is valid and can connect to the service:

```python
import os
import pinecone

def check_pinecone_connection():
    """Check if the Pinecone API key is valid and can connect to the service."""
    try:
        api_key = os.environ.get("PINECONE_API_KEY")
        if not api_key:
            return {"status": "error", "message": "PINECONE_API_KEY not found in environment variables"}
        
        # Initialize Pinecone
        pinecone.init(api_key=api_key)
        
        # List indexes to verify connection
        indexes = pinecone.list_indexes()
        
        return {
            "status": "success",
            "message": "Successfully connected to Pinecone",
            "indexes": indexes
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

## Configuration Files

| File | Purpose |
|------|---------|
| `.env.example` | Template for environment variables |
| `.replit` | Configuration for Replit IDE |
| `replit.nix` | Nix package configuration for Replit |
| `pyproject.toml` | Python project metadata and dependencies |
| `uv.lock` | Dependency lock file |

### `.env.example`
Template for required environment variables:

```
# Database Configuration
DATABASE_URL=postgresql://username:password@host:port/dbname
PGUSER=postgres_username
PGPASSWORD=postgres_password
PGHOST=localhost
PGPORT=5432
PGDATABASE=moodle_assistant

# API Keys
PINECONE_API_KEY=your_pinecone_api_key
HF_API_TOKEN=your_huggingface_token

# Hugging Face Model Settings
HF_MODEL_NAME=HuggingFaceH4/zephyr-7b-beta
HF_MAX_LENGTH=2048
HF_TEMPERATURE=0.7

# Application Settings
FLASK_SECRET_KEY=random_string_for_session_security

# Moodle Integration (Optional)
MOODLE_URL=https://your-moodle-site.com
MOODLE_TOKEN=your_moodle_webservice_token
MOODLE_SERVICE_NAME=moodle_mobile_app
```

## Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview and quick start guide |
| `DEPLOYMENT_GUIDE.md` | Detailed deployment instructions |
| `DEVELOPER_DOCUMENTATION.md` | Technical documentation for developers |
| `DESIGN_DECISIONS.md` | Explanation of design choices and rationale |
| `USER_GUIDE.md` | Non-technical guide for end users |
| `CODE_STRUCTURE.md` | This document - detailed file explanations |

## File Relationships and Dependencies

### Main Application Flow

1. `main.py` initializes the application
2. It imports `app.py` which sets up Flask and the database
3. `models.py` provides the database structure
4. Routes in the `routes/` directory handle HTTP requests
5. Templates in `templates/` render the HTML responses
6. Services in `services/` implement the business logic
7. FastAPI components in `fastapi_app/` provide the API endpoints

### FastAPI Flow

1. `fastapi_app/main.py` initializes the FastAPI application
2. Routers in `fastapi_app/routers/` define API endpoints
3. Schemas in `fastapi_app/schemas/` validate request/response data
4. Services in `fastapi_app/services/` implement the API functionality
5. Dependencies in `fastapi_app/dependencies/` provide common functions

### Database Interaction Flow

1. `models.py` defines the database structure
2. SQLAlchemy ORM maps Python objects to database tables
3. Database sessions are managed through dependency injection
4. Services use the database to store and retrieve data
5. Pinecone vector database is used for semantic search

---

This document provides a comprehensive overview of the file structure and purpose of each component in the Moodle AI Learning Assistant project. It should help developers understand how the different parts of the system interact and where to look for specific functionality.
