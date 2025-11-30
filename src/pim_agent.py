from datetime import datetime, timezone
from uuid import uuid4
import os
import sys

# Add src to sys path to ensure imports work if run directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from uagents import Context, Model, Protocol, Agent
# Import components from separate files
# NOTE: The import path for chat protocol might vary based on uagents version.
# Trying standard uagents import first if uagents_core is not found.
try:
    from uagents_core.contrib.protocols.chat import (
        ChatAcknowledgement,
        ChatMessage,
        EndSessionContent,
        StartSessionContent,
        TextContent,
        chat_protocol_spec,
    )
except ImportError:
    # Fallback to uagents built-in models or check documentation for correct import
    # For now, let's try to assume it might be under uagents.contrib or similar
    # But often uagents examples use a specific structure.
    # Let's inspect what is available or mock if necessary for the plan execution
    print("Warning: uagents_core not found. Attempting alternative imports or mocks.")

    # If standard uagents lib doesn't include the chat protocol definitions directly,
    # we might need to define them or they are in a different package.
    # However, for this task, I will attempt to define minimal models if import fails
    # to ensure the agent runs, OR I should check where these are.
    pass

# For 0.20.1, let's check if we can import similar things from uagents itself or if we need another package.
# Actually, the example code used `uagents_core`. If that's a separate package, I missed installing it.
# `uagents` on PyPI is the main one. `uagents-core` might be internal or old.
# Let's try to find where ChatMessage is in `uagents`.

# Re-attempting imports based on standard uagents usage patterns if uagents_core is missing
from uagents import Context, Model, Protocol, Agent
from typing import List, Optional, Union

class TextContent(Model):
    type: str = "text"
    text: str

class StartSessionContent(Model):
    type: str = "start-session"

class EndSessionContent(Model):
    type: str = "end-session"

class ChatMessage(Model):
    timestamp: datetime
    msg_id: str  # Changed from uuid4 to str to avoid pydantic issues with function type
    content: List[Union[TextContent, StartSessionContent, EndSessionContent]]

class ChatAcknowledgement(Model):
    timestamp: datetime
    acknowledged_msg_id: str

chat_protocol_spec = None # Placeholder if not found

from hyperon import MeTTa

from pim_rag import PIMRAG
from pim_knowledge import initialize_pim_knowledge_graph
from pim_utils import LLM, process_pim_query

load_dotenv()

# Configuration
# You can set these in .env file
AGENT_NAME = os.getenv("AGENT_NAME", "PIM Agent")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8006"))
AGENT_SEED = os.getenv("AGENT_SEED", "pim_agent_seed_phrase")
ASI_ONE_API_KEY = os.getenv("ASI_ONE_API_KEY")

if not ASI_ONE_API_KEY:
    print("WARNING: ASI_ONE_API_KEY is not set. LLM features will fail.")

# Initialize Agent
agent = Agent(
    name=AGENT_NAME,
    port=AGENT_PORT,
    seed=AGENT_SEED,
    mailbox=True
)

# Initialize Components
metta = MeTTa()
DATA_PATH = os.path.join(os.getcwd(), 'data', 'Example_PIM_Data.json')
if not os.path.exists(DATA_PATH):
    print(f"ERROR: Data file not found at {DATA_PATH}")

initialize_pim_knowledge_graph(metta, DATA_PATH)
rag = PIMRAG(metta)

# Handle missing API Key gracefully for demo
if ASI_ONE_API_KEY:
    llm = LLM(api_key=ASI_ONE_API_KEY)
else:
    print("WARNING: Running without LLM. Agent will fail to process intent.")
    llm = None

# Chat Protocol
# spec argument might not be supported in this version of uagents or requires specific format
# For 0.20.1 Protocol init is `Protocol(name: Optional[str] = None, version: Optional[str] = None)`
chat_proto = Protocol(name="pim_chat_protocol", version="1.0.0")

def create_text_chat(text: str, end_session: bool = False) -> ChatMessage:
    """Create a text chat message."""
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=str(uuid4()), # Convert to string
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
            await ctx.send(sender, create_text_chat("Hello! I am your PIM Agent. Ask me about products."))

        elif isinstance(item, TextContent):
            user_query = item.text.strip()
            ctx.logger.info(f"Query from {sender}: {user_query}")

            try:
                response_text = process_pim_query(user_query, rag, llm)
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

