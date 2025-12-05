"""
MCP Server for Product Context Retrieval

This server exposes the PIM context retrieval functionality as an MCP tool.
When added to Claude Desktop, it allows Claude to query the product knowledge base.

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

# Load environment
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

# Initialize components
print("Initializing PIM Context MCP Server...", file=sys.stderr)

metta = MeTTa()
DATA_PATH = os.path.join(project_root, 'data', 'updated_running_shoes_full_catalog.json')

if not os.path.exists(DATA_PATH):
    print(f"ERROR: Data file not found at {DATA_PATH}", file=sys.stderr)
    sys.exit(1)

initialize_pim_knowledge_graph(metta, DATA_PATH)
rag = PIMRAG(metta)

print("Initializing Vector Store...", file=sys.stderr)
vector_store = PIMVectorStore(db_path=os.path.join(project_root, "chroma_db_mcp"))

try:
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
        vector_store.ingest_pim_data(data)
    print(f"Loaded {len(data)} products into knowledge base", file=sys.stderr)
except Exception as e:
    print(f"Error ingesting data: {e}", file=sys.stderr)
    sys.exit(1)

print("PIM Context MCP Server ready", file=sys.stderr)

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
    if not query:
        return "Error: No query provided"
    
    try:
        print(f"Processing query: {query}", file=sys.stderr)
        context = retrieve_pim_context(query, rag, vector_store)
        
        if not context:
            return "No relevant products found for your query. Try a different search term."
        
        print(f"Found context with {len(context)} characters", file=sys.stderr)
        return context
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return f"Error retrieving context: {str(e)}"


if __name__ == "__main__":
    mcp.run()
