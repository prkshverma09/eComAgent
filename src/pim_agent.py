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
from pim_utils import LLM, process_pim_query
from vector_store import PIMVectorStore

# Load .env from project root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
print(f"Loading .env from: {env_path}")
print(f".env exists: {os.path.exists(env_path)}")
load_dotenv(env_path)

# Configuration
AGENT_NAME = os.getenv("AGENT_NAME", "PIM Agent")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8006"))
AGENT_SEED = os.getenv("AGENT_SEED", "pim_agent_seed_phrase")
AGENTVERSE_MAILBOX_KEY = os.getenv("AGENTVERSE_MAILBOX_KEY")
ASI_ONE_API_KEY = os.getenv("ASI_ONE_API_KEY")

if not ASI_ONE_API_KEY:
    print("WARNING: ASI_ONE_API_KEY is not set. LLM features will fail.")

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
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'updated_running_shoes_full_catalog.json')
if not os.path.exists(DATA_PATH):
    print(f"ERROR: Data file not found at {DATA_PATH}")

initialize_pim_knowledge_graph(metta, DATA_PATH)
rag = PIMRAG(metta)

print("Initializing Vector Store...")
vector_store = PIMVectorStore()

try:
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
        vector_store.ingest_pim_data(data)
except Exception as e:
    print(f"Error ingesting data into Vector Store: {e}")

if ASI_ONE_API_KEY:
    llm = LLM(api_key=ASI_ONE_API_KEY)
else:
    print("WARNING: Running without LLM. Agent will fail to process intent.")
    llm = None

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
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
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
            # Note: Cannot send ChatMessage as reply per protocol spec, only ChatAcknowledgement is allowed
            # The greeting will be sent when user sends first text message

        elif isinstance(item, TextContent):
            user_query = item.text.strip()
            ctx.logger.info(f"Query from {sender}: {user_query}")

            try:
                # Pass vector_store to enable Hybrid RAG
                response_text = process_pim_query(user_query, rag, llm, vector_store=vector_store)
                # Send response back - the protocol spec allows this via a separate interaction
                await ctx.send(sender, create_text_chat(response_text))
            except Exception as e:
                ctx.logger.error(f"Error processing query: {e}")
                await ctx.send(sender, create_text_chat("I encountered an error processing your request."))

        elif isinstance(item, EndSessionContent):
            ctx.logger.info(f"Session ended with {sender}")


@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.debug(f"Received acknowledgement for {msg.acknowledged_msg_id}")


# Include the official chat protocol with manifest publishing
agent.include(chat_proto, publish_manifest=True)

# Print startup info
@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"PIM Agent started with address: {agent.address}")
    ctx.logger.info(f"Using official AgentChatProtocol v{chat_protocol_spec.version}")
    ctx.logger.info(f"Protocol digest: {chat_protocol_spec.digest}")


if __name__ == "__main__":
    print(f"Starting PIM Agent on port {AGENT_PORT}...")
    print(f"Using official AgentChatProtocol v{chat_protocol_spec.version}")
    agent.run()
