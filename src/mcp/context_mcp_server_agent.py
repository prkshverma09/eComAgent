"""
MCP Server for Product Context Retrieval (Agent Communication version)

This server exposes the PIM context retrieval functionality as an MCP tool.
It communicates with context_agent.py via the uAgents protocol to retrieve context.

REQUIRED: context_agent.py must be running for this MCP server to work!

Usage:
  1. Start context_agent.py first:
     cd src && python context_agent.py

  2. Add to Claude Desktop config (~/Library/Application Support/Claude/claude_desktop_config.json):

  {
    "mcpServers": {
      "pim-context-agent": {
        "command": "/path/to/venv311/bin/python",
        "args": ["/path/to/eComAgent/src/mcp/context_mcp_server_agent.py"]
      }
    }
  }
"""

import os
import sys
import asyncio
import concurrent.futures
import json
import base64
from datetime import datetime
from uuid import uuid4

# Add src to path for imports
src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, src_path)

# Suppress any stdout from imports - MCP uses stdout for JSON-RPC
import io
_real_stdout = sys.stdout
sys.stdout = io.StringIO()

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from uagents import Model
from uagents_core.identity import Identity
from uagents_core.envelope import Envelope
import httpx
import requests

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


# Context Agent configuration
CONTEXT_AGENT_URL = "http://127.0.0.1:8007"
CONTEXT_AGENT_SUBMIT = f"{CONTEXT_AGENT_URL}/submit"
CONTEXT_AGENT_ADDRESS = "agent1q05xsy54st3hpq09nqjznp2vs3dqhatdk0vknk0gxzm47gt94k5wklpj5h8"


# Define the same models as context_agent.py for communication
class ContextRequest(Model):
    query: str


class ContextResponse(Model):
    context: str


# Create a persistent identity for this MCP server
mcp_identity = Identity.generate()


log("=" * 60)
log("PIM Context MCP Server (Agent Communication) Starting...")
log("=" * 60)
log(f"MCP Server Identity: {mcp_identity.address}")
log(f"Target Context Agent: {CONTEXT_AGENT_ADDRESS}")
log(f"Context Agent URL: {CONTEXT_AGENT_URL}")
log("")

# Check if context_agent.py is running
agent_running = False
try:
    response = requests.get(f"{CONTEXT_AGENT_URL}/", timeout=2)
    agent_running = True
    log(f"✓ context_agent.py is RUNNING at {CONTEXT_AGENT_URL}")
except requests.exceptions.ConnectionError:
    log(f"✗ context_agent.py is NOT running at {CONTEXT_AGENT_URL}")
    log("  ERROR: This MCP server REQUIRES context_agent.py to be running!")
    log("  Start it with: cd src && python context_agent.py")
except Exception as e:
    log(f"! Error checking context_agent: {e}")

log("=" * 60)
if agent_running:
    log("PIM Context MCP Server READY")
else:
    log("WARNING: MCP Server started but context_agent.py is not running!")
log("=" * 60)

# Create MCP Server using FastMCP
mcp = FastMCP("PIM Context Server (Agent)")

# Thread pool for running sync code
executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)


def sync_query_context_agent(user_query: str) -> str:
    """
    Send a ContextRequest to context_agent.py via HTTP and decode the response.
    Uses the uAgents envelope protocol for proper agent-to-agent communication.
    """
    log(f"[Agent] Sending ContextRequest to context_agent.py...")
    log(f"[Agent] Query: '{user_query}'")

    async def do_query():
        # Create the request message
        message = ContextRequest(query=user_query)

        # Base64 encode the payload (required by uAgents protocol)
        payload_json = message.model_dump_json()
        payload_b64 = base64.b64encode(payload_json.encode()).decode()

        # Create the envelope
        envelope = Envelope(
            version=1,
            sender=mcp_identity.address,
            target=CONTEXT_AGENT_ADDRESS,
            session=uuid4(),
            schema_digest=Model.build_schema_digest(ContextRequest),
            protocol_digest='',
            payload=payload_b64,
        )

        # Sign the envelope
        envelope.sign(mcp_identity)

        log(f"[Agent] Envelope created, sending to {CONTEXT_AGENT_SUBMIT}")

        # Send via HTTP with sync header
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                CONTEXT_AGENT_SUBMIT,
                json=json.loads(envelope.model_dump_json()),
                headers={
                    'Content-Type': 'application/json',
                    'x-uagents-connection': 'sync'
                }
            )

            log(f"[Agent] HTTP Response Status: {response.status_code}")

            if response.status_code != 200:
                return f"Error: HTTP {response.status_code} from context_agent"

            if not response.text:
                return "Error: Empty response from context_agent"

            # Parse the response envelope
            try:
                resp_envelope = response.json()
                resp_payload_b64 = resp_envelope.get('payload', '')

                # Decode the payload
                resp_payload_json = base64.b64decode(resp_payload_b64).decode()
                resp_data = json.loads(resp_payload_json)

                if 'context' in resp_data:
                    context = resp_data['context']
                    log(f"[Agent] SUCCESS: Received context with {len(context)} characters")
                    return context
                else:
                    return f"Error: Response missing 'context' field: {resp_data}"

            except Exception as e:
                log(f"[Agent] Error parsing response: {e}")
                return f"Error parsing response: {str(e)}"

    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(do_query())
            return result
        finally:
            loop.close()

    except Exception as e:
        log(f"[Agent] ERROR: {e}")
        import traceback
        log(traceback.format_exc())
        return f"Error communicating with context_agent: {str(e)}"


@mcp.tool()
async def get_product_context(query: str) -> str:
    """
    Retrieves relevant product information from the running shoes catalog
    by querying the Context Agent.

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

    # Check if agent is running
    try:
        requests.get(f"{CONTEXT_AGENT_URL}/", timeout=1)
        log("context_agent.py status: RUNNING ✓")
    except:
        log("context_agent.py status: NOT RUNNING ✗")
        return "Error: context_agent.py is not running. Please start it with: cd src && python context_agent.py"

    log("=" * 60)

    if not query:
        log("ERROR: No query provided")
        return "Error: No query provided"

    try:
        # Run the agent query in a thread pool to avoid event loop conflicts
        log("Sending query to context_agent.py via uAgents protocol...")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, sync_query_context_agent, query)

        log("-" * 40)
        log("RESPONSE PREVIEW (first 500 chars):")
        preview = result[:500] + "..." if len(result) > 500 else result
        log(preview)
        log("-" * 40)
        log(">>> SENDING RESPONSE BACK TO CLAUDE DESKTOP <<<")

        return result

    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        log(traceback.format_exc())
        return f"Error: {str(e)}"


if __name__ == "__main__":
    log("Waiting for requests from Claude Desktop...")
    mcp.run()
