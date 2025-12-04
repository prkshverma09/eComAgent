from datetime import datetime, timezone
from uuid import uuid4
import os
import sys
import json

# Add src to sys path to ensure imports work if run directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from uagents import Context, Model, Protocol, Agent
from typing import List, Union
# Re-define message models since imports might be tricky without uagents_core installed in env
class TextContent(Model):
    type: str = "text"
    text: str

class StartSessionContent(Model):
    type: str = "start-session"

class EndSessionContent(Model):
    type: str = "end-session"

class ChatMessage(Model):
    timestamp: datetime
    msg_id: str
    content: List[Union[TextContent, StartSessionContent, EndSessionContent]]

class ChatAcknowledgement(Model):
    timestamp: datetime
    acknowledged_msg_id: str

from hyperon import MeTTa

from pim_rag import PIMRAG
from pim_knowledge import initialize_pim_knowledge_graph
from pim_utils import LLM, process_pim_query
from vector_store import PIMVectorStore

load_dotenv()

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

if AGENTVERSE_MAILBOX_KEY and not os.getenv("DISABLE_MAILBOX"):
    print("Configuring agent with Agentverse Mailbox...")
    # agent_args["mailbox"] = f"{AGENTVERSE_MAILBOX_KEY}@https://agentverse.ai"
    agent_args["mailbox"] = True
else:
    print("Configuring agent for local execution (Mailbox disabled)...")
    # Explicitly define local endpoint for Almanac registration when running locally
    # This allows other local agents (like sender.py) to find us via Almanac if they use the same network/config
    # Note: For strict local-only without Almanac, sender needs to know the endpoint URL directly,
    # or we rely on uagents broadcasting/discovery on localhost if supported.
    # But defining it here helps.
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
# Use a new persistence dir for the backfill to avoid conflict with old schema if desired,
# or assume the ingest logic handles upserts/replacements gracefully.
# Here we stick to 'chroma_db' but clean it might be better if schemas conflict significantly.
# For simplicity, we just use default.
vector_store = PIMVectorStore()

# Load JSON to ingest (simple check to avoid re-ingesting every restart if needed,
# but for now we ingest to ensure sync)
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

# Chat Protocol
chat_proto = Protocol(name="pim_chat_protocol", version="1.0.0")

def create_text_chat(text: str, end_session: bool = False) -> ChatMessage:
    """Create a text chat message."""
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=str(uuid4()),
        content=content,
    )

@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages."""
    ctx.storage.set(str(ctx.session), sender)
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id),
    )

    for item in msg.content:
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"Session started with {sender}")
            await ctx.send(sender, create_text_chat("Hello! I am your Hybrid PIM Agent. Ask me anything about our products!"))

        elif isinstance(item, TextContent):
            user_query = item.text.strip()
            ctx.logger.info(f"Query from {sender}: {user_query}")

            try:
                # Pass vector_store to enable Hybrid RAG
                response_text = process_pim_query(user_query, rag, llm, vector_store=vector_store)
                await ctx.send(sender, create_text_chat(response_text))
            except Exception as e:
                ctx.logger.error(f"Error processing query: {e}")
                await ctx.send(sender, create_text_chat("I encountered an error processing your request."))

        elif isinstance(item, EndSessionContent):
            ctx.logger.info(f"Session ended with {sender}")

@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass

agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    print(f"Starting PIM Agent on port {AGENT_PORT}...")
    agent.run()
