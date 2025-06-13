# === knowledge_mcp_server.py (MCP server for RAG retrieval) ===

import os
import sys
import os

# Add the parent directory of 'utils' to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yaml
import logging
from fastapi import FastAPI
from fastmcp import FastMCP
import uvicorn
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from utils.constants import CONST
from utils.metadata_handler import MetadataHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load config
parent_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
config_path = os.path.join(parent_folder, "config.yaml")
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

config.update({
    "metadata_path": os.path.abspath(config["metadata"]),
})

app = FastAPI(title="Knowledge MCP Server")
mcp = FastMCP(app)

class KnowledgeRetriever:
    def __init__(self):
        self.vector_store = None
        self.metadata_handler = None
        self.initialized = False
        
    def initialize(self):
        """Initialize the vector store and metadata handler"""
        try:
            logging.info("Initializing Knowledge Retriever...")
            
            # Initialize embeddings
            embeddings = HuggingFaceEmbeddings(
                model_name=CONST.SELECTED_EMBEDDING_MODEL,
                cache_folder=CONST.CHROMA_DB_DIR
            )
            
            # Initialize vector store
            self.vector_store = Chroma(
                persist_directory=CONST.CHROMA_DB_DIR,
                embedding_function=embeddings
            )
            
            # Initialize metadata handler
            self.metadata_handler = MetadataHandler(config["metadata_path"])
            
            self.initialized = True
            logging.info("✅ Knowledge Retriever initialized successfully!")
            
        except Exception as e:
            logging.error(f"Failed to initialize Knowledge Retriever: {str(e)}")
            raise

# Initialize the retriever
retriever = KnowledgeRetriever()

@mcp.tool()
def get_knowledge(query: str, k: int = 2):
    """
    Retrieve relevant knowledge from the vector database based on the query.
    
    Args:
        query: The search query to find relevant documents
        k: Number of documents to retrieve (default: 2)
    
    Returns:
        Dictionary containing retrieved documents and metadata
    """
    if not retriever.initialized:
        return {
            "error": "Knowledge retriever not initialized",
            "status": "error"
        }
    
    try:
        logging.info("🔍 Retrieving knowledge for query: %s", query)
        
        # Retrieve documents from vector store
        retrieved_docs = retriever.vector_store.similarity_search(query, k=k)
        
        # Format retrieved content
        retrieved_content = []
        for i, doc in enumerate(retrieved_docs):
            retrieved_content.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_rank": i + 1
            })
        
        # Get latest metadata
        metadata = retriever.metadata_handler.load_latest_metadata()
        formatted_metadata = retriever.metadata_handler.format_metadata_for_prompt(metadata)
        
        result = {
            "status": "success",
            "query": query,
            "retrieved_documents": retrieved_content,
            "driving_metadata": formatted_metadata,
            "total_documents": len(retrieved_content)
        }
        
        logging.info("✅ Successfully retrieved %d documents", len(retrieved_content))
        return result
        
    except Exception as e:
        logging.error("❌ Error retrieving knowledge: %s", str(e))
        return {
            "error": f"Failed to retrieve knowledge: {str(e)}",
            "status": "error"
        }

@mcp.tool()
def get_driving_metadata():
    """
    Get the current driving metadata without performing document retrieval.
    Useful for motor control actions that only need current state information.
    
    Returns:
        Dictionary containing current driving metadata
    """
    if not retriever.initialized:
        return {
            "error": "Knowledge retriever not initialized",
            "status": "error"
        }
    
    try:
        logging.info("📊 Retrieving driving metadata")
        
        # Get latest metadata
        metadata = retriever.metadata_handler.load_latest_metadata()
        formatted_metadata = retriever.metadata_handler.format_metadata_for_prompt(metadata)
        
        result = {
            "status": "success",
            "driving_metadata": formatted_metadata,
            "raw_metadata": metadata
        }
        
        logging.info("✅ Successfully retrieved driving metadata")
        return result
        
    except Exception as e:
        logging.error("❌ Error retrieving metadata: %s", str(e))
        return {
            "error": f"Failed to retrieve metadata: {str(e)}",
            "status": "error"
        }

if __name__ == "__main__":
    # Initialize the retriever before starting the server
    retriever.initialize()
    
    # Start the server
    uvicorn.run("knowledge_mcp_server:app", host="0.0.0.0", port=5052, reload=True)