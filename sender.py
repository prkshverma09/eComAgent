import asyncio
from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low
import os
from dotenv import load_dotenv

load_dotenv()

# Define the message model (must match the agent's expected format if strict,
# but we are using the standard ChatMessage structure which uAgents supports or we mimic it)
# Since the agent uses the `chat_protocol` from `uagents` (or our definition of it),
# we should construct a compatible message.
# However, for simplicity, uAgents `ctx.send` wraps models.
# The agent expects `ChatMessage`.

# We need to replicate the models defined in pim_agent.py to send the right structure
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Union

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

# Recipient Address (The address printed by src/pim_agent.py)
# We need to know this address.
# Since I cannot see the terminal output of the user's running agent,
# I will create a sender that prints its own address and instructions
# on how to pair, or I can try to run the agent in the background.
# Better strategy for this tool: Run the agent in background, capture its address, then run sender.

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

        # 1. Send Start Session
        # start_msg = ChatMessage(
        #     timestamp=datetime.now(timezone.utc),
        #     msg_id=str(uuid4()),
        #     content=[StartSessionContent()]
        # )
        # await ctx.send(recipient_address, start_msg)

        # 2. Send Query
        query_msg = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=str(uuid4()),
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

    # sender.run()
    # If using asyncio.run(), we should use run_async directly or setup properly.
    # uAgents Agent.run() starts its own loop if not provided, or uses existing.
    # But calling it inside an async function (run_sender) which is run by asyncio.run() causes conflict.

    # Correct pattern:
    await sender.run_async()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python sender.py <agent_address> [query_text]")
        sys.exit(1)

    recipient = sys.argv[1]
    user_query = sys.argv[2] if len(sys.argv) > 2 else "Do you have any summer clothing?"
    asyncio.run(run_sender(recipient, user_query))

