import asyncio
import sys
import os
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Union, Optional, Literal

from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low
from pydantic import UUID4
from dotenv import load_dotenv

load_dotenv()

# --- Agent Chat Protocol Models (Matching Agent) ---
class TextContent(Model):
    type: Literal['text'] = 'text'
    text: str

class Resource(Model):
    uri: str
    metadata: Optional[dict[str, str]] = None

class ResourceContent(Model):
    type: Literal['resource'] = 'resource'
    resource_id: UUID4
    resource: Union[Resource, List[Resource]]

class MetadataContent(Model):
    type: Literal['metadata'] = 'metadata'
    metadata: dict[str, str]

class StartSessionContent(Model):
    type: Literal['start-session'] = 'start-session'

class EndSessionContent(Model):
    type: Literal['end-session'] = 'end-session'

class StartStreamContent(Model):
    type: Literal['start-stream'] = 'start-stream'
    stream_id: UUID4

class EndStreamContent(Model):
    type: Literal['end-stream'] = 'end-stream'
    stream_id: UUID4

AgentContent = Union[
    TextContent,
    ResourceContent,
    MetadataContent,
    StartSessionContent,
    EndSessionContent,
    StartStreamContent,
    EndStreamContent
]

class ChatMessage(Model):
    timestamp: datetime
    msg_id: UUID4
    content: List[AgentContent]

class ChatAcknowledgement(Model):
    timestamp: datetime
    acknowledged_msg_id: UUID4
    metadata: Optional[dict[str, str]] = None
# ---------------------------------------------------

async def run_sender(recipient_address: str, query_text: str = "Do you have any summer clothing?"):
    sender = Agent(
        name="Sender",
        port=8007,
        seed="sender_seed_phrase_123",
        endpoint=["http://127.0.0.1:8007/submit"]
    )

    # Ensure sender has funds to communicate on network (fetch.ai testnet)
    fund_agent_if_low(sender.wallet.address())

    @sender.on_event("startup")
    async def say_hello(ctx: Context):
        ctx.logger.info(f"Sending message to {recipient_address}...")

        # 1. Send Start Session (Optional - kept commented as per user preference)
        # start_msg = ChatMessage(
        #     timestamp=datetime.now(timezone.utc),
        #     msg_id=uuid4(),
        #     content=[StartSessionContent()]
        # )
        # await ctx.send(recipient_address, start_msg)

        # 2. Send Query
        query_msg = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(text=query_text)]
        )
        await ctx.send(recipient_address, query_msg)

    # We need a handler to print the response
    @sender.on_message(ChatMessage)
    async def handle_response(ctx: Context, sender: str, msg: ChatMessage):
        for item in msg.content:
            if isinstance(item, TextContent):
                response_text = item.text
                ctx.logger.info(f"Received Response: {response_text}")

                # If it's just the greeting, don't exit yet; wait for the answer.
                if response_text.startswith("Hello! I am your Hybrid PIM Agent"):
                    continue

                # Exit after receiving the actual response
                os._exit(0)

    await sender.run_async()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/pim_agent_client.py <agent_address> [query_text]")
        sys.exit(1)

    recipient = sys.argv[1]
    user_query = sys.argv[2] if len(sys.argv) > 2 else "Do you have any summer clothing?"
    asyncio.run(run_sender(recipient, user_query))
