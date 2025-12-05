"""
MCP Server for Product Context Retrieval

This server exposes the PIM context retrieval functionality as an MCP tool.
When added to Claude Desktop, it allows Claude to query the product knowledge base.

NOTE: This server does NOT depend on context_agent.py running. It directly uses
the underlying retrieval functions (PIMRAG, VectorStore, retrieve_pim_context).

Usage:
  Add to Claude Desktop config (~/Library/Application Support/Claude/claude_desktop_config.json):
  
  {
    "mcpServers": {
      "pim-context": {
        "command": "/path/to/venv311/bin/python",
        "args": ["/path/to/eComAgent/src/mcp/context_mcp_server.py"]
      }
    }
  }
"""

import os
import sys
import json
from datetime import datetime

# Add src to path for imports
src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, src_path)

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from hyperon import MeTTa

from pim_rag import PIMRAG
from pim_knowledge import initialize_pim_knowledge_graph
from pim_utils import retrieve_pim_context
from vector_store import PIMVectorStore


def log(message: str):
    """Log message to stderr with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", file=sys.stderr)


# Load environment
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

log("=" * 60)
log("PIM Context MCP Server Starting...")
log("=" * 60)
log(f"Project root: {project_root}")
log(f"Env path: {env_path}")

# Initialize components
metta = MeTTa()
DATA_PATH = os.path.join(project_root, 'data', 'updated_running_shoes_full_catalog.json')

if not os.path.exists(DATA_PATH):
    log(f"ERROR: Data file not found at {DATA_PATH}")
    sys.exit(1)

log(f"Loading data from: {DATA_PATH}")
initialize_pim_knowledge_graph(metta, DATA_PATH)
rag = PIMRAG(metta)

log("Initializing Vector Store...")
vector_store = PIMVectorStore(db_path=os.path.join(project_root, "chroma_db_mcp"))

try:
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
        vector_store.ingest_pim_data(data)
    log(f"SUCCESS: Loaded {len(data)} products into knowledge base")
except Exception as e:
    log(f"ERROR ingesting data: {e}")
    sys.exit(1)

log("=" * 60)
log("PIM Context MCP Server READY")
log("Waiting for requests from Claude Desktop...")
log("=" * 60)

# Create MCP Server using FastMCP
mcp = FastMCP("PIM Context Server")


@mcp.tool()
def get_product_context(query: str) -> str:
    """
    Retrieves relevant product information from the running shoes catalog.
    
    Use this tool when users ask about running shoes, athletic footwear,
    specific brands (AeroStride, CloudTrail, FleetStep, NimbusPath, NovaStride, 
    PulseTrack, RoadRift, TerraSprint, UrbanTempo, VelociRun), or product features 
    (cushioning, stability, trail, road, waterproof, marathon, race, etc.).
    
    Returns structured product data including brand, name, type, materials,
    price, ratings, and reviews.
    
    Args:
        query: The search query to find relevant products 
               (e.g., 'waterproof trail shoes', 'best marathon running shoes', 'shoes under $200')
    
    Returns:
        Structured product context with details about matching products.
    """
    log("=" * 60)
    log("RECEIVED REQUEST FROM CLAUDE DESKTOP")
    log(f"Query: '{query}'")
    log("=" * 60)
    
    if not query:
        log("ERROR: No query provided")
        return "Error: No query provided"
    
    try:
        log("Processing query with Hybrid RAG (Vector Store + MeTTa)...")
        context = retrieve_pim_context(query, rag, vector_store)
        
        if not context:
            log("No relevant products found")
            return "No relevant products found for your query. Try a different search term."
        
        log(f"SUCCESS: Found context with {len(context)} characters")
        log("-" * 40)
        log("RESPONSE PREVIEW (first 500 chars):")
        log(context[:500] + "..." if len(context) > 500 else context)
        log("-" * 40)
        log("Sending response back to Claude Desktop...")
        
        return context
        
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        log(traceback.format_exc())
        return f"Error retrieving context: {str(e)}"


if __name__ == "__main__":
    mcp.run()
