"""
Test script for LlamaIndex integration with Pinecone v6.0.2
"""
import os
import logging
from pinecone import Pinecone, ServerlessSpec
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core.indices.vector_store import VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Document, Settings, StorageContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Pinecone API key from environment
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
INDEX_NAME = "test-index"
CLOUD = "aws"  # AWS cloud for serverless
REGION = "us-west-2"  # US West 2 region for serverless


def test_llama_index_with_pinecone():
    """Test LlamaIndex integration with Pinecone v6.0.2"""
    if not PINECONE_API_KEY:
        logger.error("PINECONE_API_KEY not found in environment")
        return False
        
    try:
        logger.info("Initializing Pinecone...")
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # List existing indexes
        logger.info("Listing Pinecone indexes...")
        indexes = pc.list_indexes()
        index_names = indexes.names()
        logger.info(f"Found indexes: {index_names}")
        
        # Check if test index exists
        if INDEX_NAME not in index_names:
            logger.info(f"Creating index '{INDEX_NAME}'...")
            # Create serverless index
            pc.create_index(
                name=INDEX_NAME,
                dimension=384,  # Default for MPNET base
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=CLOUD,
                    region=REGION
                )
            )
            logger.info(f"Index '{INDEX_NAME}' created successfully")
        else:
            logger.info(f"Index '{INDEX_NAME}' already exists")
        
        # Set up LlamaIndex with HuggingFace embeddings
        logger.info("Setting up LlamaIndex with HuggingFace embeddings...")
        embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-mpnet-base-v2")
        
        # Initialize settings
        Settings.embed_model = embed_model
        Settings.chunk_size = 1024
        Settings.chunk_overlap = 20
        
        # Connect to Pinecone index
        logger.info("Connecting to Pinecone index...")
        index = pc.Index(INDEX_NAME)
        vector_store = PineconeVectorStore(
            pinecone_index=index
        )
        
        # Create storage context
        logger.info("Creating storage context...")
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Create vector index
        logger.info("Creating vector index...")
        vector_index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            storage_context=storage_context
        )
        
        # Create node parser for chunking
        logger.info("Creating node parser...")
        node_parser = SentenceSplitter(
            chunk_size=1024,
            chunk_overlap=20
        )
        
        # Create test documents
        logger.info("Creating test documents...")
        documents = [
            Document(
                text="LlamaIndex (GPT Index) is a data framework for your LLM applications.",
                metadata={"source": "example", "category": "framework"}
            ),
            Document(
                text="Pinecone is a vector database that makes it easy to build high-performance vector search applications.",
                metadata={"source": "example", "category": "database"}
            ),
            Document(
                text="Large Language Models (LLMs) are powerful for text generation but need help with retrieval.",
                metadata={"source": "example", "category": "model"}
            )
        ]
        
        # Parse documents into nodes
        logger.info("Parsing documents into nodes...")
        nodes = node_parser.get_nodes_from_documents(documents)
        
        # Insert nodes into index
        logger.info("Inserting nodes into index...")
        vector_index.insert_nodes(nodes)
        
        # Test query
        logger.info("Testing query...")
        query_engine = vector_index.as_query_engine()
        query_text = "What is LlamaIndex?"
        response = query_engine.query(query_text)
        
        logger.info(f"Query: {query_text}")
        logger.info(f"Response: {response}")
        
        # Get source nodes used for the response
        logger.info("Source nodes:")
        for node in response.source_nodes:
            logger.info(f"- Text: {node.node.text}")
            logger.info(f"  Score: {node.score}")
            logger.info(f"  Metadata: {node.node.metadata}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing LlamaIndex with Pinecone: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    logger.info("Testing LlamaIndex integration with Pinecone v6.0.2...")
    result = test_llama_index_with_pinecone()
    if result:
        logger.info("Test successful!")
    else:
        logger.error("Test failed!")