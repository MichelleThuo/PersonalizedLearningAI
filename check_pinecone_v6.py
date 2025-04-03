"""
Check Pinecone connectivity and operations with v6.0.2 API
"""
import os
import sys
import logging

from pinecone import Pinecone, ServerlessSpec

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
INDEX_NAME = "moodle-assistant-test"
DIMENSION = 4

def check_pinecone_v6():
    """Test Pinecone operations with v6.0.2 API"""
    # Get Pinecone API key from environment
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        logger.error("PINECONE_API_KEY not found in environment variables")
        return False
        
    try:
        # Initialize Pinecone
        logger.info("Initializing Pinecone with v6.0.2 API...")
        pc = Pinecone(api_key=api_key)
        
        # List existing indexes
        index_list = pc.list_indexes()
        index_names = index_list.names()
        
        logger.info(f"Existing indexes: {index_names}")
        
        # Check if test index exists, delete if it does
        if INDEX_NAME in index_names:
            logger.info(f"Deleting existing test index '{INDEX_NAME}'...")
            pc.delete_index(INDEX_NAME)
            
        # Create a new test index
        logger.info(f"Creating test index '{INDEX_NAME}'...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-west-2"
            )
        )
        
        # Connect to the index
        logger.info(f"Connecting to index '{INDEX_NAME}'...")
        index = pc.Index(INDEX_NAME)
        
        # Create test vectors
        logger.info("Creating test vectors...")
        vectors = [
            (
                "vec1", 
                [0.1, 0.2, 0.3, 0.4], 
                {"metadata": "test vector 1"}
            ),
            (
                "vec2", 
                [0.2, 0.3, 0.4, 0.5], 
                {"metadata": "test vector 2"}
            ),
            (
                "vec3", 
                [0.3, 0.4, 0.5, 0.6], 
                {"metadata": "test vector 3"}
            )
        ]
        
        # Upsert vectors
        logger.info("Upserting vectors...")
        index.upsert(vectors=vectors)
        
        # Query the index
        logger.info("Querying index...")
        query_response = index.query(
            vector=[0.1, 0.2, 0.3, 0.4],
            top_k=2,
            include_metadata=True
        )
        
        # Print results
        logger.info("Query results:")
        for match in query_response.matches:
            logger.info(f"ID: {match.id}, Score: {match.score}, Metadata: {match.metadata}")
        
        # Clean up - delete the test index
        logger.info(f"Cleaning up - deleting test index '{INDEX_NAME}'...")
        pc.delete_index(INDEX_NAME)
        
        logger.info("Pinecone test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error testing Pinecone: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
if __name__ == "__main__":
    success = check_pinecone_v6()
    sys.exit(0 if success else 1)