import asyncio
import sys
import os
from datetime import datetime, timezone
from uuid import uuid4

from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
from dotenv import load_dotenv

# Import official chat protocol from uagents_core (requires Python 3.10+)
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
)

load_dotenv()


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

        # Send Query using official ChatMessage format
        query_msg = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=query_text)]
        )
        await ctx.send(recipient_address, query_msg)

    # Handle acknowledgement (optional)
    @sender.on_message(ChatAcknowledgement)
    async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
        ctx.logger.info(f"Message acknowledged: {msg.acknowledged_msg_id}")

    # Handle response
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
