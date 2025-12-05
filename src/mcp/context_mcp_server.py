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

import asyncio
import os
import sys
import json

# Add src to path for imports
src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, src_path)

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

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

# Create MCP Server
server = Server("pim-context-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_product_context",
            description=(
                "Retrieves relevant product information from the running shoes catalog. "
                "Use this tool when users ask about running shoes, athletic footwear, "
                "specific brands (AeroStride, CloudTrail, FleetStep, etc.), or product features "
                "(cushioning, stability, trail, road, waterproof, etc.). "
                "Returns structured product data including brand, name, type, materials, "
                "price, ratings, and reviews."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant products (e.g., 'waterproof trail shoes', 'best marathon running shoes', 'shoes under $200')"
                    }
                },
                "required": ["query"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "get_product_context":
        query = arguments.get("query", "")
        
        if not query:
            return [TextContent(type="text", text="Error: No query provided")]
        
        try:
            context = retrieve_pim_context(query, rag, vector_store)
            
            if not context:
                return [TextContent(
                    type="text", 
                    text="No relevant products found for your query. Try a different search term."
                )]
            
            return [TextContent(type="text", text=context)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error retrieving context: {str(e)}")]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    print("PIM Context MCP Server ready", file=sys.stderr)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            initialization_options=None,
        )


if __name__ == "__main__":
    asyncio.run(main())

