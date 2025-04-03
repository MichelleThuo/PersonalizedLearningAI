"""
Test script for Pinecone API version 2.2.2
"""
import os
import pinecone

def test_pinecone():
    """Test basic Pinecone operations with the 2.2.2 API"""
    # Get API key from environment
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        print("Error: PINECONE_API_KEY not found in environment")
        return False
    
    try:
        # Configuration
        api_key = api_key
        environment = "gcp-starter"
        
        # Create a config object
        print("Creating Pinecone configuration...")
        config = pinecone.config.Config(
            api_key=api_key, 
            host=f"https://controller.{environment}.pinecone.io"
        )
        
        # List indexes to verify connection
        print("Listing Pinecone indexes...")
        indexes = pinecone.list_indexes(config)
        print(f"Found {len(indexes)} indexes: {indexes}")
        
        return True
    except Exception as e:
        print(f"Error testing Pinecone: {e}")
        return False

if __name__ == "__main__":
    print("Testing Pinecone...")
    test_pinecone()