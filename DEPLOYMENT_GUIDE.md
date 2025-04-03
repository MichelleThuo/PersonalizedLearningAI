# Moodle AI Learning Assistant: Deployment Guide

This guide provides comprehensive instructions for deploying the Moodle AI Learning Assistant in various environments, from local development to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Local Development Deployment](#local-development-deployment)
4. [Production Server Deployment](#production-server-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Cloud Platform Deployment](#cloud-platform-deployment)
7. [Moodle Integration Setup](#moodle-integration-setup)
8. [Database Migration](#database-migration)
9. [Environment Variables Reference](#environment-variables-reference)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying the application, ensure you have the following:

### Required Accounts

- **Pinecone Account**: For vector database ([Sign up](https://www.pinecone.io/))
- **Hugging Face Account**: For AI model access ([Sign up](https://huggingface.co/))
- **PostgreSQL Database**: Either local or cloud-hosted

### System Requirements

- **Python 3.11+**: Required for application runtime
- **PostgreSQL 14+**: Database server
- **FFmpeg**: For video processing capabilities
- **50GB+ Storage**: Recommended for application, dependencies, and content

### Required API Keys

- **Pinecone API Key**: From your Pinecone dashboard
- **Hugging Face API Token**: With permission to access the required models

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/moodle-ai-assistant.git
cd moodle-ai-assistant
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit the `.env` file with your specific configuration values:

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

### 4. Initialize Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE moodle_assistant;

# Exit PostgreSQL
\q
```

## Local Development Deployment

### 1. Run Database Migrations

The application will automatically create the necessary tables when it first runs:

```bash
python main.py
```

### 2. Start the Development Server

```bash
# Run the Flask application with integrated FastAPI
python main.py

# Alternative: Run just the FastAPI component
python run_fastapi.py
```

### 3. Access the Application

- Main application: http://localhost:5000
- FastAPI documentation: http://localhost:5000/docs

### 4. Development Tools

During development, you may want to:

```bash
# Check Pinecone connectivity
python check_pinecone.py

# Test vector database operations
python test_simple_vector_db.py

# Test LlamaIndex integration
python test_llama_pinecone_v6.py
```

## Production Server Deployment

For production deployments, you should use a proper WSGI server and reverse proxy.

### 1. Set Up Gunicorn

```bash
# Install gunicorn if not already installed
pip install gunicorn

# Start the application with gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 --reload main:app
```

### 2. Set Up Nginx as Reverse Proxy

Install Nginx:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install nginx

# CentOS/RHEL
sudo yum install nginx
```

Create an Nginx configuration file at `/etc/nginx/sites-available/moodle-ai-assistant`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Increase upload size limit for video files
    client_max_body_size 500M;
}
```

Enable the site and restart Nginx:

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/moodle-ai-assistant /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### 3. Set Up Systemd Service

Create a service file at `/etc/systemd/system/moodle-ai-assistant.service`:

```ini
[Unit]
Description=Moodle AI Learning Assistant
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/moodle-ai-assistant
ExecStart=/path/to/moodle-ai-assistant/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
Restart=always
Environment="PATH=/path/to/moodle-ai-assistant/venv/bin"
EnvironmentFile=/path/to/moodle-ai-assistant/.env

[Install]
WantedBy=multi-user.target
```

Start and enable the service:

```bash
sudo systemctl start moodle-ai-assistant
sudo systemctl enable moodle-ai-assistant
```

### 4. SSL Configuration

For secure HTTPS connections, set up SSL with Let's Encrypt:

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain and configure SSL certificate
sudo certbot --nginx -d your-domain.com
```

## Docker Deployment

### 1. Create a Dockerfile

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "main:app"]
```

### 2. Create Docker Compose File

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=${PGPASSWORD}
      - POSTGRES_USER=${PGUSER}
      - POSTGRES_DB=${PGDATABASE}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${PGUSER}"]
      interval: 5s
      timeout: 5s
      retries: 5

  web:
    build: .
    ports:
      - "5000:5000"
    depends_on:
      db:
        condition: service_healthy
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - PGUSER=${PGUSER}
      - PGPASSWORD=${PGPASSWORD}
      - PGHOST=db
      - PGPORT=5432
      - PGDATABASE=${PGDATABASE}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - HF_API_TOKEN=${HF_API_TOKEN}
      - HF_MODEL_NAME=${HF_MODEL_NAME}
      - HF_MAX_LENGTH=${HF_MAX_LENGTH}
      - HF_TEMPERATURE=${HF_TEMPERATURE}
      - FLASK_SECRET_KEY=${FLASK_SECRET_KEY}
    volumes:
      - ./static:/app/static
      - ./uploads:/app/uploads

volumes:
  postgres_data:
```

### 3. Build and Run with Docker Compose

```bash
# Build and start the services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the services
docker-compose down
```

## Cloud Platform Deployment

### Heroku Deployment

#### 1. Prepare for Heroku

```bash
# Install Heroku CLI
npm install -g heroku

# Login to Heroku
heroku login

# Create a new Heroku app
heroku create moodle-ai-assistant

# Add PostgreSQL add-on
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set PINECONE_API_KEY=your_pinecone_api_key
heroku config:set HF_API_TOKEN=your_huggingface_token
heroku config:set HF_MODEL_NAME=HuggingFaceH4/zephyr-7b-beta
heroku config:set HF_MAX_LENGTH=2048
heroku config:set HF_TEMPERATURE=0.7
heroku config:set FLASK_SECRET_KEY=random_string_for_session_security
```

#### 2. Create Heroku Configuration Files

Create a `Procfile` in the project root:

```
web: gunicorn main:app
```

Ensure you have a `runtime.txt` file:

```
python-3.11.4
```

#### 3. Deploy to Heroku

```bash
# Push to Heroku
git push heroku main

# Open the application
heroku open
```

### AWS Elastic Beanstalk Deployment

#### 1. Prepare for AWS EB

```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init -p python-3.11 moodle-ai-assistant

# Create EB environment
eb create moodle-ai-assistant-env
```

#### 2. Create EB Configuration Files

Create a `.ebextensions/01_packages.config` file:

```yaml
packages:
  yum:
    postgresql-devel: []
    ffmpeg: []
```

Create a `.ebextensions/02_python.config` file:

```yaml
container_commands:
  01_upgrade_pip:
    command: "pip install --upgrade pip"
  02_install_requirements:
    command: "pip install -r requirements.txt"
```

#### 3. Configure Environment Variables

Create a `.ebextensions/03_environment.config` file:

```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    PINECONE_API_KEY: your_pinecone_api_key
    HF_API_TOKEN: your_huggingface_token
    HF_MODEL_NAME: HuggingFaceH4/zephyr-7b-beta
    HF_MAX_LENGTH: 2048
    HF_TEMPERATURE: 0.7
    FLASK_SECRET_KEY: random_string_for_session_security
```

#### 4. Deploy to AWS EB

```bash
# Deploy to Elastic Beanstalk
eb deploy

# Open the application
eb open
```

## Moodle Integration Setup

### 1. Enable Moodle Web Services

In your Moodle installation:

1. Go to Site Administration > Plugins > Web Services > Overview
2. Follow the steps to enable web services
3. Enable the REST protocol
4. Create a service with the necessary functions:
   - `core_course_get_courses`
   - `core_course_get_contents`
   - `core_user_get_users`
   - `core_course_get_user_enrolments`
   - `gradereport_user_get_grade_items`
5. Create a token for this service

### 2. Configure Moodle Integration in the Application

Update your `.env` file with Moodle settings:

```
MOODLE_URL=https://your-moodle-site.com
MOODLE_TOKEN=your_moodle_webservice_token
MOODLE_SERVICE_NAME=moodle_mobile_app
```

### 3. Test Moodle Integration

Visit the admin dashboard in your application and test the Moodle synchronization feature.

## Database Migration

### Initial Database Setup

The application automatically creates the database tables on first run. However, you can manually set up the database:

```bash
# Run the Python interpreter
python

# In the Python shell
from app import db
db.create_all()
exit()
```

### Database Schema Evolution

If you need to modify the database schema:

1. Backup your database:
   ```bash
   pg_dump -U postgres moodle_assistant > backup.sql
   ```

2. Update model definitions in `models.py`

3. Apply the changes:
   ```bash
   # Using the Python shell
   python
   from app import db
   # WARNING: This drops all tables and recreates them - data will be lost
   db.drop_all()
   db.create_all()
   exit()
   ```

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/dbname` |
| `PGUSER` | PostgreSQL username | `postgres` |
| `PGPASSWORD` | PostgreSQL password | `password` |
| `PGHOST` | PostgreSQL host | `localhost` |
| `PGPORT` | PostgreSQL port | `5432` |
| `PGDATABASE` | PostgreSQL database name | `moodle_assistant` |
| `PINECONE_API_KEY` | API key for Pinecone vector database | `abc123...` |
| `HF_API_TOKEN` | API token for Hugging Face | `hf_abc123...` |
| `HF_MODEL_NAME` | Hugging Face model identifier | `HuggingFaceH4/zephyr-7b-beta` |
| `HF_MAX_LENGTH` | Maximum token length for model output | `2048` |
| `HF_TEMPERATURE` | Temperature parameter for model sampling | `0.7` |
| `FLASK_SECRET_KEY` | Secret key for Flask sessions | `random_string` |
| `MOODLE_URL` | URL of Moodle instance | `https://moodle.example.com` |
| `MOODLE_TOKEN` | API token for Moodle web services | `abc123...` |
| `MOODLE_SERVICE_NAME` | Service name for Moodle API | `moodle_mobile_app` |
| `VECTOR_INDEX_NAME` | Name of Pinecone index | `moodle-assistant` |
| `VECTOR_DIMENSION` | Dimension of vector embeddings | `1536` |
| `VECTOR_METRIC` | Similarity metric for vector search | `cosine` |
| `WHISPER_MODEL` | OpenAI Whisper model size | `base` |
| `WHISPER_LANGUAGE` | Language code for Whisper | `en` |

## Troubleshooting

### Common Issues and Solutions

#### 1. Database Connection Issues

**Problem**: Unable to connect to the database
**Solution**:
- Verify PostgreSQL is running:
  ```bash
  systemctl status postgresql
  ```
- Check database connection parameters in `.env`
- Ensure database exists:
  ```bash
  psql -U postgres -c "SELECT 1 FROM pg_database WHERE datname='moodle_assistant'"
  ```
- Check network connectivity to database host

#### 2. Pinecone API Issues

**Problem**: Unable to connect to Pinecone
**Solution**:
- Verify API key is correctly set in `.env`
- Check Pinecone service status at [status.pinecone.io](https://status.pinecone.io)
- Run the diagnostic script:
  ```bash
  python check_pinecone.py
  ```
- Ensure your Pinecone plan supports the index configuration

#### 3. Hugging Face API Issues

**Problem**: Unable to access Hugging Face models
**Solution**:
- Verify API token is correctly set in `.env`
- Check token permissions on Hugging Face website
- Ensure the specified model exists and is accessible
- Check network connectivity to Hugging Face API

#### 4. Application Startup Errors

**Problem**: Application fails to start
**Solution**:
- Check application logs:
  ```bash
  # In development
  python main.py
  
  # For systemd service
  journalctl -u moodle-ai-assistant
  
  # For Docker
  docker-compose logs web
  ```
- Verify all required environment variables are set
- Check for Python package conflicts or missing dependencies

#### 5. Moodle Integration Issues

**Problem**: Unable to connect to Moodle API
**Solution**:
- Verify Moodle URL is accessible
- Check Moodle token has appropriate permissions
- Ensure Moodle web services are properly configured
- Check for CORS issues if integration is through browser