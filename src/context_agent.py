from datetime import datetime, timezone
from uuid import uuid4
import os
import sys
import json

# Add src to sys path to ensure imports work if run directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from uagents import Context, Model, Protocol, Agent
from typing import List, Union, Optional

from hyperon import MeTTa

from pim_rag import PIMRAG
from pim_knowledge import initialize_pim_knowledge_graph
from pim_utils import retrieve_pim_context
from vector_store import PIMVectorStore

load_dotenv()

# Configuration
AGENT_NAME = os.getenv("CONTEXT_AGENT_NAME", "Context Retrieval Agent")
AGENT_PORT = int(os.getenv("CONTEXT_AGENT_PORT", "8007"))
AGENT_SEED = os.getenv("CONTEXT_AGENT_SEED", "context_agent_seed_phrase")
AGENTVERSE_MAILBOX_KEY = os.getenv("AGENTVERSE_MAILBOX_KEY")

# Initialize Agent
agent_args = {
    "name": AGENT_NAME,
    "port": AGENT_PORT,
    "seed": AGENT_SEED,
}

if AGENTVERSE_MAILBOX_KEY:
    print("Configuring agent with Agentverse Mailbox...")
    # Note: If running multiple agents with same mailbox key, behavior might be unexpected.
    # ideally user provides a different key for this agent if using mailbox.
    # For now, we'll comment this out or assume the user knows what they are doing if they set it.
    # agent_args["mailbox"] = f"{AGENTVERSE_MAILBOX_KEY}@https://agentverse.ai"
    pass

agent = Agent(**agent_args)

# Initialize Components
metta = MeTTa()
DATA_PATH = os.path.join(os.getcwd(), 'data', 'Dummy_catalog_runningshoes.json')
if not os.path.exists(DATA_PATH):
    print(f"ERROR: Data file not found at {DATA_PATH}")

initialize_pim_knowledge_graph(metta, DATA_PATH)
rag = PIMRAG(metta)

# Initialize Vector Store & Ingest Data
print("Initializing Vector Store...")
vector_store = PIMVectorStore()

try:
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
        vector_store.ingest_pim_data(data)
except Exception as e:
    print(f"Error ingesting data into Vector Store: {e}")

# Protocol Models
class ContextRequest(Model):
    query: str

class ContextResponse(Model):
    context: str

# Protocol Definition
context_proto = Protocol(name="context_retrieval", version="1.0.0")

@context_proto.on_message(ContextRequest, replies=ContextResponse)
async def handle_context_request(ctx: Context, sender: str, msg: ContextRequest):
    """Handle incoming context requests."""
    ctx.logger.info(f"Received query from {sender}: {msg.query}")

    try:
        context_str = retrieve_pim_context(msg.query, rag, vector_store)

        if not context_str:
            context_str = "No relevant context found."

        # Log size of context found
        ctx.logger.info(f"Found context of length: {len(context_str)}")

        await ctx.send(sender, ContextResponse(context=context_str))

    except Exception as e:
        ctx.logger.error(f"Error processing context request: {e}")
        await ctx.send(sender, ContextResponse(context=f"Error: {str(e)}"))

agent.include(context_proto, publish_manifest=True)

if __name__ == "__main__":
    print(f"Starting Context Agent on port {AGENT_PORT}...")
    agent.run()

