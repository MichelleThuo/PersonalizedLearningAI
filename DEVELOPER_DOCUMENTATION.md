# Moodle AI Learning Assistant: Developer Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Core Components](#core-components)
5. [AI Integration](#ai-integration)
6. [Database Design](#database-design)
7. [API Structure](#api-structure)
8. [User Interface Design](#user-interface-design)
9. [Authentication & Authorization](#authentication--authorization)
10. [Moodle Integration](#moodle-integration)
11. [Development Workflow](#development-workflow)
12. [Testing Strategy](#testing-strategy)
13. [Appendix: System Requirements](#appendix-system-requirements)

## Project Overview

### Vision and Purpose

The Moodle AI Learning Assistant was developed to address the limitations of traditional LMS platforms by adding AI-powered capabilities that enhance learning experiences. The goal was to create a system that could:

1. Understand natural language questions about course content
2. Provide contextually relevant answers based on course materials
3. Intelligently search across diverse training resources
4. Generate customized quizzes to test knowledge
5. Offer personalized learning recommendations
6. Create interactive content automatically
7. Process and analyze video content

### Core Challenges

The development addressed several key challenges:

1. **Integration with Existing Systems**: How to seamlessly connect with Moodle without disrupting its core functionality
2. **Natural Language Understanding**: Using modern AI models to understand and respond to user questions
3. **Content Indexing**: Creating effective semantic search across different content types
4. **Personalization**: Building recommendation algorithms that adapt to user behavior and needs
5. **Scalability**: Designing a system that can handle increasing amounts of content and users

### Design Philosophy

The project followed these guiding principles:

1. **Modularity**: Components are decoupled to allow for independent development and testing
2. **Extensibility**: The system is designed to easily add new features or integrate with additional services
3. **Maintainability**: Code is structured to be readable and sustainable over time
4. **Performance**: Optimized database queries and caching for responsiveness
5. **User Experience**: Clean, intuitive interfaces for both learners and administrators

## Architecture

### High-Level System Architecture

The application follows a multi-tier architecture:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Presentation   │     │   Application   │     │     Data        │
│     Layer       │◄───►│     Layer       │◄───►│     Layer       │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Web Interface  │     │  Business Logic │     │   PostgreSQL    │
│   HTML/CSS/JS   │     │ Python Services │     │     Database    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │                       │
                                ▼                       ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  External APIs  │     │ Vector Database │
                        │ Hugging Face/   │     │    Pinecone     │
                        │     Moodle      │     │                 │
                        └─────────────────┘     └─────────────────┘
```

### Framework Choices

The application uses a dual-framework approach:

1. **Flask**: Handles the traditional web routes, templating, and session management
2. **FastAPI**: Powers the modern API endpoints, async operations, and provides OpenAPI documentation

This hybrid approach leverages the strengths of both frameworks:
- Flask's mature ecosystem and simplicity for web interfaces
- FastAPI's performance and modern features for API development

### Component Interaction

Components interact through:
1. Direct function calls within the application
2. REST API calls between the front-end and back-end
3. Database queries for persistent data
4. External API calls to AI services and Moodle

## Technology Stack

### Backend Technologies

- **Python 3.11+**: Core programming language
- **Flask 2.3.3**: Web framework for rendering templates and handling web routes
- **FastAPI 0.103.1**: Modern, high-performance API framework
- **SQLAlchemy 2.0.20**: ORM for database interactions
- **Pydantic 2.3.0**: Data validation and settings management
- **Gunicorn 23.0.0**: WSGI HTTP Server
- **Uvicorn 0.23.2**: ASGI server for FastAPI

### Database Technologies

- **PostgreSQL 14+**: Relational database for structured data
- **Pinecone**: Vector database for semantic search capabilities
- **SQLite**: Used for local development (via Flask-SQLAlchemy)

### AI and Machine Learning

- **Hugging Face Transformers**: Primary AI model provider (zephyr-7b-beta)
- **LlamaIndex 0.8.54**: Framework for building LLM applications over data
- **OpenAI Whisper**: For transcribing video/audio content
- **scikit-learn 1.3.0**: For feature extraction and similarity calculations

### Frontend Technologies

- **Bootstrap 5.3**: CSS framework for responsive design
- **JavaScript**: For interactive elements
- **HTML/Jinja2 Templates**: For rendering dynamic content
- **Font Awesome 6.0**: Icon library

### Development Tools

- **Git**: Version control
- **pytest**: Testing framework (implied in setup)
- **Python-dotenv**: Environment variable management
- **Replit**: Development and deployment platform

## Core Components

### Application Structure

The application is organized into these main components:

```
moodle_ai_assistant/
├── main.py               # Main entry point
├── app.py                # Flask application setup
├── models.py             # SQLAlchemy models
├── routes/               # Flask route blueprints
│   ├── views.py          # UI routes
│   ├── api.py            # General API routes
│   ├── moodle.py         # Moodle integration
│   ├── h5p.py            # H5P content generation
│   ├── transcription.py  # Video transcription
│   └── vector_db.py      # Vector database operations
├── services/             # Business logic services
│   ├── openai_service.py     # AI model integration
│   ├── search_service.py     # Search functionality
│   ├── recommendation_service.py # Recommendation engine
│   ├── h5p_service.py     # H5P generation
│   ├── transcription_service.py # Video processing
│   └── vector_db_service.py # Vector DB operations
├── fastapi_app/          # FastAPI application
│   ├── main.py           # FastAPI setup
│   ├── routers/          # API route modules
│   ├── schemas/          # Pydantic models
│   ├── services/         # FastAPI-specific services
│   └── dependencies/     # Dependency injection
├── templates/            # Jinja2 HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Homepage
│   ├── user_interface.html # Learner interface
│   ├── admin_dashboard.html # Admin interface
│   └── ...               # Other templates
└── static/               # Static assets
    ├── css/              # CSS files
    ├── js/               # JavaScript files
    └── h5p_content/      # Generated H5P content
```

### Key Service Modules

1. **OpenAI Service**: Integrates with Hugging Face API to handle AI interactions
2. **Search Service**: Manages content search functionality
3. **Recommendation Service**: Generates personalized recommendations
4. **H5P Service**: Handles generation of interactive H5P content
5. **Transcription Service**: Processes video files and extracts text
6. **Vector DB Service**: Manages vector embeddings and semantic search

### Design Patterns Used

1. **Repository Pattern**: Database access is abstracted through service classes
2. **Dependency Injection**: Used in FastAPI for services
3. **Blueprint/Router Pattern**: Flask blueprints and FastAPI routers organize routes
4. **Factory Pattern**: Flask app creation and initialization
5. **Service Layer Pattern**: Business logic is isolated in service modules

## AI Integration

### Model Selection Rationale

The project primarily uses the Hugging Face zephyr-7b-beta model for several reasons:

1. **Performance**: Provides good results for conversational tasks
2. **Cost-effectiveness**: Open-source alternative to OpenAI models
3. **Customizability**: Can be fine-tuned for specific educational domains
4. **Availability**: Accessible through Hugging Face's API

### AI Capabilities Implementation

1. **Conversational Interface**
   - Implemented in `openai_service.py`
   - Uses chat completion endpoint with contextual memory
   - Structured prompts with course content context

2. **Content Understanding**
   - Text processing for content analysis
   - Named entity recognition for topic extraction
   - Content summarization capabilities

3. **Quiz Generation**
   - Question types: multiple choice, true/false, short answer
   - Difficulty level adaptation
   - Domain-specific question formulation

4. **Content Embedding**
   - Text fragments are transformed into vector embeddings
   - Embeddings stored in Pinecone for semantic search
   - Similarity computation for finding related content

### AI Integration Workflow

```
1. User Input → 2. Preprocessing → 3. AI Processing → 4. Postprocessing → 5. Response
```

1. **User Input**: Question or request from user interface
2. **Preprocessing**: Context gathering, history retrieval, prompt construction
3. **AI Processing**: Sending to model API, receiving raw response
4. **Postprocessing**: Formatting, validation, enhancing with links/resources
5. **Response**: Delivering final response to user interface

## Database Design

### Entity Relationship Diagram

```
┌───────────┐       ┌───────────┐       ┌───────────┐
│   User    │       │   Course  │       │CourseContent│
├───────────┤       ├───────────┤       ├───────────┤
│ id        │       │ id        │       │ id        │
│ username  │       │ title     │       │ course_id │
│ email     │       │ description│◄─────┤ title     │
│ password  │       │ moodle_id │       │ content   │
└───────────┘       └───────────┘       │ type      │
      │                   ▲             └───────────┘
      │                   │                   ▲
      │                   │                   │
      ▼                   │                   │
┌───────────┐       ┌───────────┐       ┌───────────┐
│ChatSession│       │   Quiz    │       │SearchIndex│
├───────────┤       ├───────────┤       ├───────────┤
│ id        │       │ id        │       │ id        │
│ user_id   │       │ course_id │       │ content_id│
│ course_id │       │ title     │       │ indexed_text
│ start_time│       │ description│       │           │
└───────────┘       └───────────┘       └───────────┘
      │                   │
      │                   │
      ▼                   ▼
┌───────────┐       ┌───────────┐
│ChatMessage│       │QuizQuestion│
├───────────┤       ├───────────┤
│ id        │       │ id        │
│ session_id│       │ quiz_id   │
│ is_user   │       │ text      │
│ message   │       │ type      │
│ timestamp │       │           │
└───────────┘       └───────────┘
                          │
                          │
                          ▼
                    ┌───────────┐
                    │QuizOption │
                    ├───────────┤
                    │ id        │
                    │ question_id
                    │ text      │
                    │ is_correct│
                    └───────────┘
```

### Database Models

The primary models (defined in `models.py`) include:

1. **User**: Stores user authentication and profile information
2. **Course**: Represents a course, potentially linked to Moodle
3. **CourseContent**: Individual content items within courses
4. **ChatSession**: Tracks conversation sessions between users and AI
5. **ChatMessage**: Individual messages within chat sessions
6. **Quiz**: Generated quizzes for testing knowledge
7. **QuizQuestion**: Individual questions within quizzes
8. **QuizOption**: Answer options for multiple choice questions
9. **SearchIndex**: Preprocessed text for efficient search

### Vector Database Schema

The Pinecone vector database stores:

1. **Vectors**: 1536-dimensional embeddings of content fragments
2. **Metadata**:
   - Content ID reference to PostgreSQL database
   - Content type
   - Course ID
   - Creation timestamp
   - Source URL (if applicable)

## API Structure

### REST API Endpoints

The application exposes several REST API endpoints:

1. **Chat API**
   - `POST /api/chat`: Submit messages and receive AI responses
   - `GET /api/chat/sessions`: Get user's chat history

2. **Search API**
   - `GET /api/search`: Search across course content
   - `POST /api/search/vector`: Semantic search using vectors

3. **Quiz API**
   - `POST /api/quiz/generate`: Generate a quiz for specific content
   - `GET /api/quiz/{quiz_id}`: Get quiz details
   - `POST /api/quiz/evaluate`: Submit and evaluate quiz answers

4. **Recommendation API**
   - `GET /api/recommendations/{user_id}`: Get personalized recommendations
   - `POST /api/learning-path`: Generate custom learning path

5. **Content API**
   - `GET /api/courses`: List available courses
   - `GET /api/courses/{course_id}/content`: Get course content
   - `GET /api/content/{content_id}`: Get specific content

6. **H5P API**
   - `POST /api/h5p/generate`: Generate H5P content
   - `GET /api/h5p/download/{filename}`: Download H5P package

7. **Video API**
   - `POST /api/video/upload`: Upload a video file
   - `POST /api/video/process/{content_id}`: Process existing video

8. **Vector DB API**
   - `GET /api/vector-db/status`: Check vector database status
   - `POST /api/vector-db/index/{content_id}`: Index content

9. **Moodle Integration API**
   - `GET /api/moodle/config`: Get Moodle configuration
   - `POST /api/moodle/sync-course`: Sync a Moodle course

### API Documentation

FastAPI provides automatic OpenAPI documentation at `/docs` endpoint, which includes:
- Endpoint descriptions
- Request/response schemas
- Authentication requirements
- Example requests

## User Interface Design

### User Experience Considerations

The UI design focused on several key principles:

1. **Simplicity**: Clean layouts to reduce cognitive load
2. **Consistency**: Uniform styling and interaction patterns
3. **Feedback**: Clear system status indicators
4. **Accessibility**: Following web accessibility guidelines
5. **Responsiveness**: Adapting to different screen sizes

### Two Interface Approach

The application provides two distinct interfaces:

1. **Learner Interface**
   - **Purpose**: For staff who need to learn and access content
   - **Design Philosophy**: Engaging, focused on learning, personalized
   - **Key Components**:
     - Chat window for AI assistance
     - Personalized course recommendations
     - Learning path visualization
     - Progress tracking
     - Quick access to quizzes

2. **Admin Dashboard**
   - **Purpose**: For administrators to manage the system
   - **Design Philosophy**: Data-rich, comprehensive, analytical
   - **Key Components**:
     - User activity analytics
     - Content management tools
     - AI performance metrics
     - System configuration
     - Report generation

### UI Technology Stack

The user interfaces use:

1. **Bootstrap 5**: For responsive layouts and components
2. **Jinja2 Templates**: For server-side rendering
3. **CSS Custom Properties**: For theming
4. **JavaScript**: For dynamic interactions
5. **Font Awesome**: For iconography

### Responsive Design Approach

The UI is built with a mobile-first approach:
1. Base layouts designed for mobile
2. Media queries to adapt to larger screens
3. Flexible grid system for layout
4. Responsive typography
5. Touch-friendly interaction elements

## Authentication & Authorization

### Authentication Methods

The application supports these authentication mechanisms:

1. **Local Authentication**: Username/password with SQLAlchemy models
2. **Flask-Login**: Session management for web interface
3. **JWT Tokens**: For API authentication (implied in FastAPI routes)
4. **Moodle SSO Integration**: For seamless Moodle login (planned)

### Authorization Levels

The system defines several user roles:

1. **Learner**: Can access learning content, chat, take quizzes
2. **Instructor**: Can create content, generate quizzes, view limited analytics
3. **Administrator**: Full system access, including configuration
4. **API User**: Programmatic access to specific endpoints

### Security Considerations

1. **Password Handling**: Secure hashing with werkzeug.security
2. **CSRF Protection**: Built-in Flask protection
3. **Input Validation**: With Pydantic models
4. **SQL Injection Prevention**: Through SQLAlchemy ORM
5. **API Rate Limiting**: To prevent abuse (implied)

## Moodle Integration

### Integration Points

The application integrates with Moodle at several points:

1. **User Synchronization**: Maps Moodle users to local users
2. **Course Retrieval**: Pulls course structure and content
3. **Content Indexing**: Processes Moodle content for AI features
4. **Data Synchronization**: Keeps local and Moodle data in sync
5. **Authentication**: SSO with Moodle credentials (planned)

### Integration Methods

Three primary integration methods are supported:

1. **REST API Integration**:
   - Uses Moodle Web Services API
   - Requires API token from Moodle
   - Implemented in `routes/moodle.py`

2. **LTI Integration** (Learning Tools Interoperability):
   - Standard approach for embedding external tools
   - Requires LTI configuration in Moodle
   - Provides seamless user experience

3. **Plugin Integration**:
   - More tightly coupled integration as a Moodle plugin
   - Requires installation in Moodle's plugin directory
   - Most complex but provides deepest integration

### Moodle API Interactions

Key Moodle API endpoints used:

1. **core_course_get_courses**: Retrieve course information
2. **core_course_get_contents**: Get detailed course content
3. **core_user_get_users**: Retrieve user information
4. **core_course_get_user_enrolments**: Get user course enrollments
5. **gradereport_user_get_grade_items**: Retrieve grade information

## Development Workflow

### Development Environment Setup

The development environment includes:

1. **Python 3.11+**: Core language runtime
2. **PostgreSQL**: Local or remote database
3. **Pinecone Account**: For vector database
4. **Hugging Face Account**: For AI model access
5. **Environment Variables**: Configuration in `.env` file
6. **Virtual Environment**: For dependency isolation

### Code Organization Principles

The codebase follows these organizational principles:

1. **Separation of Concerns**: Different aspects of the system are isolated
2. **DRY (Don't Repeat Yourself)**: Common functionality is abstracted
3. **Explicit over Implicit**: Code behavior is clear and documented
4. **Configuration over Convention**: Behavior is configurable via environment variables
5. **Modularity**: Components can be developed and tested independently

### Deployment Workflow

The application can be deployed through:

1. **Traditional Server Deployment**:
   - Gunicorn as WSGI server
   - Nginx as reverse proxy
   - Systemd for process management

2. **Docker Deployment**:
   - Multi-container setup
   - Docker Compose for service orchestration
   - Volume mapping for persistent data

3. **Cloud Platform Deployment**:
   - Heroku compatible
   - AWS/GCP/Azure adaptable
   - Environment variable configuration

## Testing Strategy

### Testing Levels

The testing approach encompasses:

1. **Unit Testing**: Testing individual functions and methods
2. **Integration Testing**: Testing component interactions
3. **API Testing**: Verifying API endpoints
4. **UI Testing**: Ensuring UI components work correctly

### Test Implementation Details

1. **Unit Tests**: Using pytest with fixtures
2. **Mock Objects**: For external dependencies
3. **Test Database**: Separate from development/production
4. **Continuous Integration**: Automated test runs
5. **Code Coverage**: Measuring test coverage percentage

### Test Organization

Tests are organized by component:

1. **Model Tests**: Verify database model behavior
2. **Service Tests**: Test business logic
3. **API Tests**: Validate API responses
4. **Integration Tests**: Test component interactions

## Appendix: System Requirements

### Minimum Hardware Requirements

- **CPU**: 2+ cores
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB available space
- **Network**: Broadband internet connection

### Software Dependencies

- **Python 3.11+**
- **PostgreSQL 14+**
- **Node.js 18+** (optional, for frontend development)
- **FFmpeg** (for video processing)

### External Service Dependencies

- **Pinecone**: Vector database for semantic search
- **Hugging Face**: AI model provider
- **Moodle Instance**: For LMS integration

### Environment Variables

The application requires several environment variables:

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

# Application Settings
FLASK_SECRET_KEY=random_string_for_session_security

# Moodle Integration
MOODLE_URL=https://your-moodle-site.com
MOODLE_TOKEN=your_moodle_webservice_token
```