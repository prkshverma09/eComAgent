"""
MCP Server for Product Context Retrieval

This server exposes the PIM context retrieval functionality as an MCP tool.
It directly uses the RAG system to retrieve product context.

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

# Suppress any stdout from imports - MCP uses stdout for JSON-RPC
import io
_real_stdout = sys.stdout
sys.stdout = io.StringIO()

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from hyperon import MeTTa

from pim_rag import PIMRAG
from pim_knowledge import initialize_pim_knowledge_graph
from pim_utils import retrieve_pim_context
from vector_store import PIMVectorStore

# Restore stdout
sys.stdout = _real_stdout


def log(message: str):
    """Log message to stderr with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", file=sys.stderr, flush=True)


# Load environment
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

log("=" * 60)
log("PIM Context MCP Server Starting...")
log("=" * 60)

# Initialize MeTTa and knowledge graph
log("Initializing MeTTa Knowledge Graph...")
metta = MeTTa()
data_path = os.path.join(project_root, "data", "Dummy_catalog_runningshoes.json")

if not os.path.exists(data_path):
    log(f"ERROR: Data file not found at {data_path}")
else:
    initialize_pim_knowledge_graph(metta, data_path)
    log("MeTTa knowledge graph initialized")

# Initialize RAG
rag = PIMRAG(metta)
log("RAG initialized")

# Initialize Vector Store with absolute path
log("Initializing Vector Store...")
db_path = os.path.join(project_root, "chroma_db_mcp")
vector_store = PIMVectorStore(db_path=db_path)

try:
    with open(data_path, 'r') as f:
        data = json.load(f)
        vector_store.ingest_pim_data(data)
    log(f"Vector store initialized with {len(data)} products")
except Exception as e:
    log(f"Error initializing vector store: {e}")
    vector_store = None

log("=" * 60)
log("PIM Context MCP Server READY")
log("=" * 60)

# Create MCP Server using FastMCP
mcp = FastMCP("PIM Context Server")


@mcp.tool()
async def get_product_context(query: str) -> str:
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
    log(">>> RECEIVED REQUEST FROM CLAUDE DESKTOP <<<")
    log(f"Query: '{query}'")
    log("=" * 60)

    if not query:
        log("ERROR: No query provided")
        return "Error: No query provided"

    if not vector_store:
        log("ERROR: Vector store not initialized")
        return "Error: Vector store not initialized"

    try:
        log("Retrieving product context...")
        context = retrieve_pim_context(query, rag, vector_store)

        if not context:
            log("No matching products found")
            return "No matching products found for your query."

        log("-" * 40)
        log(f"SUCCESS: Retrieved {len(context)} characters of context")
        log("RESPONSE PREVIEW (first 500 chars):")
        preview = context[:500] + "..." if len(context) > 500 else context
        log(preview)
        log("-" * 40)
        log(">>> SENDING RESPONSE BACK TO CLAUDE DESKTOP <<<")

        return context

    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        log(traceback.format_exc())
        return f"Error retrieving context: {str(e)}"


if __name__ == "__main__":
    log("Waiting for requests from Claude Desktop...")
    mcp.run()
