"""
Test script for the SimpleVectorDBService
"""
import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app import db
from models import CourseContent, Course
from fastapi_app.services.simple_vector_db import SimpleVectorDBService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_test_data(session: Session):
    """Add test data to the database"""
    # Create a test course
    course = Course(
        moodle_course_id=999,
        title="Test Course",
        description="A test course for testing the vector database"
    )
    session.add(course)
    session.flush()  # Get the ID assigned by the database
    
    # Create some test content
    contents = [
        CourseContent(
            course_id=course.id,
            title="Introduction to AI",
            content_type="document",
            content_text="Artificial intelligence (AI) is intelligence demonstrated by machines, " +
                      "as opposed to natural intelligence displayed by animals and humans. " +
                      "AI research has been defined as the field of study of intelligent agents, " +
                      "which refers to any system that perceives its environment and takes actions " +
                      "that maximize its chance of achieving its goals."
        ),
        CourseContent(
            course_id=course.id,
            title="Machine Learning Basics",
            content_type="document",
            content_text="Machine learning is a branch of artificial intelligence and computer science " +
                      "which focuses on the use of data and algorithms to imitate the way that humans " +
                      "learn, gradually improving its accuracy. The term 'machine learning' was coined " +
                      "in 1959 by Arthur Samuel, an American pioneer in the field of computer gaming " +
                      "and artificial intelligence."
        ),
        CourseContent(
            course_id=course.id,
            title="Deep Learning",
            content_type="document",
            content_text="Deep learning is part of a broader family of machine learning methods based " +
                      "on artificial neural networks with representation learning. Learning can be " +
                      "supervised, semi-supervised or unsupervised. Deep learning architectures such " +
                      "as deep neural networks, deep belief networks, convolutional neural networks, " +
                      "and transformation-based models have been applied to many fields."
        )
    ]
    
    for content in contents:
        session.add(content)
        
    session.commit()
    
    return course, contents

def test_simple_vector_db():
    """Test the SimpleVectorDBService implementation"""
    try:
        # Get database URL
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            logger.error("DATABASE_URL not found in environment variables")
            return False
            
        # Create a test database engine and session
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Add test data
        logger.info("Adding test data to database...")
        course, contents = add_test_data(session)
        
        # Initialize the vector database service
        logger.info("Initializing SimpleVectorDBService...")
        vector_db = SimpleVectorDBService()
        
        if not vector_db.initialized:
            logger.error("SimpleVectorDBService failed to initialize. Check Pinecone API key.")
            return False
            
        # Test indexing content
        logger.info("Testing content indexing...")
        for content in contents:
            logger.info(f"Indexing content: {content.title}")
            result = vector_db.index_content(session, content.id)
            logger.info(f"Result: {result}")
            
            if not result.get("success", False):
                logger.error(f"Failed to index content: {result.get('error', 'Unknown error')}")
                return False
                
        # Test search
        logger.info("Testing search...")
        search_query = "artificial intelligence"
        search_result = vector_db.search(search_query, course_id=course.id, limit=2)
        logger.info(f"Search results for '{search_query}': {search_result}")
        
        # Test get_similar_content
        logger.info("Testing similar content retrieval...")
        content_id = contents[0].id
        similar = vector_db.get_similar_content(content_id, session, limit=2)
        logger.info(f"Similar content to ID {content_id}: {similar}")
        
        # Test get_relevant_context
        logger.info("Testing relevant context retrieval...")
        context = vector_db.get_relevant_context("neural networks", course_id=course.id, limit=2)
        logger.info(f"Relevant context: {context}")
        
        # Clean up test data
        logger.info("Cleaning up test data...")
        for content in contents:
            session.delete(content)
        session.delete(course)
        session.commit()
        
        logger.info("Test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error testing SimpleVectorDBService: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'session' in locals():
            session.close()
            
if __name__ == "__main__":
    success = test_simple_vector_db()
    sys.exit(0 if success else 1)