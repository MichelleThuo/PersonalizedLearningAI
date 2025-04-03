"""
Updated example script for Pinecone API version 2.2.2
"""
import os
from typing import List
import pinecone
from pinecone import Index

def test_pinecone_v2():
    """Test basic Pinecone operations with the 2.2.2 API"""
    # Get API key from environment
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        print("Error: PINECONE_API_KEY not found in environment")
        return False
    
    try:
        print("Testing Pinecone with API key...")
        api_key = api_key
        environment = "gcp-starter"  # Default environment for v2.2.2 starter tier
        
        # Setting environment variables
        os.environ["PINECONE_API_KEY"] = api_key
        os.environ["PINECONE_ENVIRONMENT"] = environment
        
        # List existing indexes
        print("Listing Pinecone indexes...")
        indexes = pinecone.list_indexes()
        print(f"Found {len(indexes)} indexes: {indexes}")
        
        # Check if our test index exists
        index_name = "test-index"
        
        # Create the index if it doesn't exist
        if index_name not in indexes:
            print(f"Creating index '{index_name}'...")
            pinecone.create_index(
                name=index_name,
                dimension=384,  # Embedding dimension
                metric="cosine"
            )
            print(f"Index '{index_name}' created successfully!")
        else:
            print(f"Index '{index_name}' already exists")
        
        # Connect to the index
        print(f"Connecting to index '{index_name}'...")
        index = Index(index_name)
        
        # Get index stats
        print("Getting index statistics...")
        stats = index.describe_index_stats()
        print(f"Index statistics: {stats}")
        
        # Test vector operations
        test_vector_id = "test-vector-1"
        test_vector = [0.1] * 384  # Create a test vector of dimension 384
        test_metadata = {"category": "test", "source": "example"}
        
        # Upsert a vector
        print(f"Upserting test vector '{test_vector_id}'...")
        upsert_response = index.upsert(
            vectors=[(test_vector_id, test_vector, test_metadata)],
            namespace="test-namespace"
        )
        print(f"Upsert response: {upsert_response}")
        
        # Query the vector
        print(f"Querying for similar vectors to '{test_vector_id}'...")
        query_response = index.query(
            vector=test_vector,
            top_k=5,
            include_metadata=True,
            namespace="test-namespace"
        )
        print(f"Query response: {query_response}")
        
        return True
    except Exception as e:
        print(f"Error testing Pinecone: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Pinecone v2...")
    test_pinecone_v2()