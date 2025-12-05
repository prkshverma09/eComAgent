from datetime import datetime, timezone
from uuid import uuid4
import os
import sys
import json

# Add src to sys path to ensure imports work if run directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from uagents import Context, Model, Protocol, Agent

from hyperon import MeTTa

# Import official chat protocol from uagents_core (requires Python 3.10+)
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    EndSessionContent,
    StartSessionContent,
    chat_protocol_spec,
)

from pim_rag import PIMRAG
from pim_knowledge import initialize_pim_knowledge_graph
from pim_utils import retrieve_pim_context
from vector_store import PIMVectorStore

# Load .env from project root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
print(f"Loading .env from: {env_path}")
print(f".env exists: {os.path.exists(env_path)}")
load_dotenv(env_path)

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

# Always try to use Mailbox if Key is present (Required for Agentverse UI)
if AGENTVERSE_MAILBOX_KEY:
    print("Configuring agent with Agentverse Mailbox...")
    agent_args["mailbox"] = True
else:
    print("WARNING: AGENTVERSE_MAILBOX_KEY not found in environment.")
    print("Configuring agent for local execution (Mailbox disabled). Agentverse UI will NOT work.")
    agent_args["endpoint"] = [f"http://127.0.0.1:{AGENT_PORT}/submit"]

agent = Agent(**agent_args)

# Initialize Components
metta = MeTTa()
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'Dummy_catalog_runningshoes.json')
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

# ========================================
# OFFICIAL Chat Protocol (AgentChatProtocol v0.3.0)
# Using the official spec from uagents_core
# ========================================
chat_proto = Protocol(spec=chat_protocol_spec)


def create_text_chat(text: str, end_session: bool = False) -> ChatMessage:
    """Create a text chat message using official protocol."""
    content: list = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=content,
    )


@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages from ASI:One Chat UI."""
    ctx.logger.info(f"Received ChatMessage from {sender}")
    ctx.storage.set(str(ctx.session), sender)

    # Send Acknowledgement
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id),
    )

    for item in msg.content:
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"Session started with {sender}")

        elif isinstance(item, TextContent):
            user_query = item.text.strip()
            ctx.logger.info(f"Query from {sender}: {user_query}")

            try:
                # Retrieve context using hybrid RAG
                context_str = retrieve_pim_context(user_query, rag, vector_store)
                
                if not context_str:
                    context_str = "No relevant context found for your query."
                
                # Format response for chat
                response_text = f"**Context Retrieved:**\n\n{context_str}"
                await ctx.send(sender, create_text_chat(response_text))
            except Exception as e:
                ctx.logger.error(f"Error processing query: {e}")
                await ctx.send(sender, create_text_chat("I encountered an error retrieving context."))

        elif isinstance(item, EndSessionContent):
            ctx.logger.info(f"Session ended with {sender}")


@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.debug(f"Received acknowledgement for {msg.acknowledged_msg_id}")


# ========================================
# Programmatic Context Retrieval Protocol
# For agent-to-agent communication
# ========================================
class ContextRequest(Model):
    query: str

class ContextResponse(Model):
    context: str

context_proto = Protocol(name="context_retrieval", version="1.0.0")

@context_proto.on_message(ContextRequest, replies=ContextResponse)
async def handle_context_request(ctx: Context, sender: str, msg: ContextRequest):
    """Handle incoming context requests from other agents."""
    ctx.logger.info(f"Received ContextRequest from {sender}: {msg.query}")

    try:
        context_str = retrieve_pim_context(msg.query, rag, vector_store)

        if not context_str:
            context_str = "No relevant context found."

        ctx.logger.info(f"Found context of length: {len(context_str)}")
        await ctx.send(sender, ContextResponse(context=context_str))

    except Exception as e:
        ctx.logger.error(f"Error processing context request: {e}")
        await ctx.send(sender, ContextResponse(context=f"Error: {str(e)}"))


# Include protocols with manifest publishing
agent.include(chat_proto, publish_manifest=True)
agent.include(context_proto, publish_manifest=True)

# Print startup info
@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Context Agent started with address: {agent.address}")
    ctx.logger.info(f"Using official AgentChatProtocol v{chat_protocol_spec.version}")
    ctx.logger.info(f"Protocol digest: {chat_protocol_spec.digest}")


if __name__ == "__main__":
    print(f"Starting Context Agent on port {AGENT_PORT}...")
    print(f"Using official AgentChatProtocol v{chat_protocol_spec.version}")
    agent.run()
