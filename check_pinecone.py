"""
Script to verify Pinecone API key and connection.
This checks if the Pinecone API key is valid and can connect to the service.
"""
import os
import sys
import pinecone

def check_pinecone_connection():
    """
    Check if the Pinecone API key is valid and can connect to the service.
    """
    # Get Pinecone API key from environment
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        print("Error: PINECONE_API_KEY not found in environment variables")
        return False
    
    try:
        # For pinecone-client v2.2.2, there is no Pinecone class, use the globals
        print(f"Connecting to Pinecone with provided API key...")
        
        # Check API key validity by attempting to list indexes
        print("Listing Pinecone indexes...")
        
        # Set up pinecone with environment
        environment = "gcp-starter"  # or the appropriate one
        pinecone.init(api_key=api_key, environment=environment)
        
        # List indexes
        indexes = pinecone.list_indexes()
        
        print(f"Connection successful! Found {len(indexes)} indexes:")
        for idx in indexes:
            print(f" - {idx}")
        
        # Try to create a test index
        index_name = "moodle-assistant-test"
        
        # Check if index exists
        if index_name in indexes:
            print(f"Index '{index_name}' already exists.")
        else:
            print(f"Creating test index '{index_name}'...")
            pinecone.create_index(
                name=index_name,
                dimension=384,  # Default for most embedding models
                metric="cosine"
            )
            print(f"Successfully created test index '{index_name}'")
        
        print("Pinecone connection verified successfully!")
        return True
    
    except Exception as e:
        print(f"Error connecting to Pinecone: {str(e)}")
        return False

if __name__ == "__main__":
    print("Checking Pinecone connection...")
    success = check_pinecone_connection()
    if not success:
        sys.exit(1)
    sys.exit(0)