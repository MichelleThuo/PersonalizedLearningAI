# Moodle AI Learning Assistant

![Moodle AI Learning Assistant](generated-icon.png)

## Project Overview

The Moodle AI Learning Assistant is an advanced AI-powered learning platform integrated with Moodle LMS, designed to provide intelligent, personalized, and engaging educational experiences through adaptive content generation and interactive support mechanisms.

This project enhances traditional Learning Management Systems by adding conversational AI capabilities, semantic search, personalized recommendations, dynamic quiz generation, automatic H5P content creation, and video content processing through AI-powered transcription.

## Key Features

### Conversational AI Assistant
- Natural language chat interface for answering questions about course content
- Context-aware responses that incorporate course materials and learning history
- Guided learning through conversational interactions

### Intelligent Search
- Semantic search across all course content
- Vector-based similarity matching for finding related materials
- Enhanced discovery of relevant learning resources

### Personalized Learning
- Course recommendations based on user behavior and performance
- Adaptive learning paths tailored to individual needs
- Progressive difficulty levels matched to learner capabilities

### Dynamic Content Generation
- Automatic quiz generation from course materials
- Interactive H5P content creation, including:
  - Course presentations
  - Question sets
  - Fill-in-the-blanks exercises
- Conversion of static content into interactive learning experiences

### Video Processing
- Automatic transcription of video content
- Searchable video content through transcription indexing
- Enhanced accessibility for video-based learning

### Dual Interface
- **User Interface**: Focused, learner-centric experience with chat, recommendations, and progress tracking
- **Admin Dashboard**: Comprehensive management tools, analytics, and system configuration

### Moodle Integration
- Seamless connection with existing Moodle installations
- Course and user synchronization
- Content indexing from Moodle courses

## Technology Stack

### Backend
- **Python 3.11+**: Core programming language
- **Flask**: Web framework for rendering templates and web routes
- **FastAPI**: Modern API framework for high-performance endpoints
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and settings management
- **Gunicorn/Uvicorn**: WSGI/ASGI servers

### Database
- **PostgreSQL**: Relational database for structured data
- **Pinecone**: Vector database for semantic search capabilities

### AI & Machine Learning
- **Hugging Face Transformers**: Primary AI model provider
- **LlamaIndex**: Framework for building LLM applications over data
- **OpenAI Whisper**: For transcribing video/audio content

### Frontend
- **Bootstrap 5**: CSS framework for responsive design
- **JavaScript**: For interactive elements
- **HTML/Jinja2**: Templates for rendering dynamic content

## Documentation

This repository includes comprehensive documentation to help you understand, deploy, and extend the project:

- [Deployment Guide](DEPLOYMENT_GUIDE.md): Instructions for deploying in various environments
- [Developer Documentation](DEVELOPER_DOCUMENTATION.md): Technical details and architecture explanation
- [Design Decisions](DESIGN_DECISIONS.md): Rationale behind key design choices

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Pinecone account
- Hugging Face account

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/moodle-ai-assistant.git
   cd moodle-ai-assistant
   ```

2. Set up the environment:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your specific configuration
   ```

4. Start the application:
   ```bash
   python main.py
   ```

5. Access the application at http://localhost:5000

## Use Cases

### For Learners

- Ask questions about course content and receive contextual answers
- Discover related learning materials through semantic search
- Practice knowledge with dynamically generated quizzes
- Follow personalized learning paths matched to their needs
- Engage with interactive H5P content
- Access transcribed video content for better comprehension

### For Administrators

- Monitor user engagement and learning progress
- Analyze performance data to identify knowledge gaps
- Manage course content and AI-powered features
- Configure system behavior and integration settings
- Track AI performance and conversation quality

## Contributing

We welcome contributions to the Moodle AI Learning Assistant! Please see our [Contribution Guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Hugging Face for providing access to advanced AI models
- Pinecone for vector search capabilities
- Moodle community for the open-source LMS platform
- All contributors who have helped shape this project
