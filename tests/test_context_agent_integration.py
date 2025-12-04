from uagents import Bureau, Agent, Context, Model
import os
import sys

# Ensure src is in path for imports within context_agent to work if needed
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Add the parent directory to sys.path so we can import 'src' as a module if needed,
# OR we can just import directly if 'src' is in path.
# However, the import below `from src.context_agent ...` implies 'src' is a package or we are at root.
# If we appended `.../src` to path, we should import `context_agent` directly.
# Let's add the PROJECT ROOT to sys.path so `from src.context_agent` works.
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.context_agent import agent as context_agent, ContextRequest, ContextResponse

# Create a tester agent
tester = Agent(name="ContextTester", port=8009, seed="context_test_sender_seed_unique_bureau")

@tester.on_event("startup")
async def send_query(ctx: Context):
    query = "running shoes for men"
    ctx.logger.info(f"Sending query: '{query}' to {context_agent.address}")
    await ctx.send(context_agent.address, ContextRequest(query=query))

@tester.on_message(ContextResponse)
async def handle_response(ctx: Context, sender: str, msg: ContextResponse):
    ctx.logger.info("Received Context Response:")
    print(f"\n{'-'*20}\n{msg.context}\n{'-'*20}\n")
    ctx.logger.info("Test complete.")

    # Stop the agents/bureau?
    # uAgents Bureau doesn't have a clean 'stop' method triggered from agent context easily available in older versions.
    # We can just exit the process.
    os._exit(0)

# Initialize Bureau
# We pass endpoint for local communication if needed, but Bureau handles it internally usually.
bureau = Bureau(port=8010)
bureau.add(context_agent)
bureau.add(tester)

if __name__ == "__main__":
    print("Starting Bureau...")
    bureau.run()
