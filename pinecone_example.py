"""
Example script for Pinecone API version 2.2.2
"""
import os
import pinecone
from pinecone.config import ConfigBuilder

def test_pinecone():
    """Test basic Pinecone operations with the 2.2.2 API"""
    # Get API key from environment
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        print("Error: PINECONE_API_KEY not found in environment")
        return False
    
    try:
        # Configuration using the ConfigBuilder
        print("Creating Pinecone configuration...")
        # The proper way to set configuration in Pinecone 2.2.2
        os.environ["PINECONE_API_KEY"] = api_key
        os.environ["PINECONE_ENVIRONMENT"] = "gcp-starter"
        
        # List indexes to verify connection
        print("Listing Pinecone indexes...")
        indexes = pinecone.list_indexes()
        print(f"Found {len(indexes)} indexes: {indexes}")
        
        # Create an index if none exists
        index_name = "test-index"
        dimension = 384 # Matches the embedding dimension
        
        # Check if our test index already exists
        if index_name not in indexes:
            print(f"Creating new index '{index_name}'...")
            pinecone.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine"
            )
            print(f"Index '{index_name}' created successfully")
        else:
            print(f"Index '{index_name}' already exists")
        
        # Connect to the index
        print(f"Connecting to index '{index_name}'...")
        index = pinecone.Index(index_name)
        
        # Check index stats
        print("Getting index statistics...")
        stats = index.describe_index_stats()
        print(f"Index stats: {stats}")
        
        return True
    except Exception as e:
        print(f"Error testing Pinecone: {e}")
        return False

if __name__ == "__main__":
    print("Testing Pinecone...")
    test_pinecone()