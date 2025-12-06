#!/usr/bin/env python3
"""
Consumer Preference Agent with Unibase Membase Integration

This agent stores and retrieves user shopping preferences using Unibase's
decentralized memory layer (Membase) on BNB Chain.

Features:
- Store user preferences (size, colors, budget, brands, etc.)
- Retrieve preferences for personalized product search
- Decentralized storage on BNB Chain via Membase
- Dual protocol support (chat + programmatic)

Usage:
    python consumer_preference_agent.py

Environment Variables:
    MEMBASE_ACCOUNT: Your Membase account address (0x...)
    MEMBASE_ID: Sub-account identifier
    CONSUMER_AGENT_SEED: Agent seed phrase
    CONSUMER_AGENT_PORT: Agent port (default: 8008)
"""

from datetime import datetime, timezone
from uuid import uuid4
import os
import sys
import json

# Add src to sys path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from uagents import Context, Model, Protocol, Agent

# Import official chat protocol
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    EndSessionContent,
    StartSessionContent,
    chat_protocol_spec,
)

# Load .env from project root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
print(f"Loading .env from: {env_path}")
load_dotenv(env_path)

# ========================================
# Configuration
# ========================================
AGENT_NAME = os.getenv("CONSUMER_AGENT_NAME", "Consumer Preference Agent")
AGENT_PORT = int(os.getenv("CONSUMER_AGENT_PORT", "8008"))
AGENT_SEED = os.getenv("CONSUMER_AGENT_SEED", "consumer_preference_agent_seed_phrase")
AGENTVERSE_MAILBOX_KEY = os.getenv("AGENTVERSE_MAILBOX_KEY")

# Membase Configuration
MEMBASE_ACCOUNT = os.getenv("MEMBASE_ACCOUNT", "")
MEMBASE_ID = os.getenv("MEMBASE_ID", "consumer_prefs")
MEMBASE_ENABLED = bool(MEMBASE_ACCOUNT)

# ========================================
# Membase Integration (Unibase)
# ========================================
class MembaseClient:
    """
    Client for Unibase Membase - Decentralized Memory Layer

    Membase stores data on BNB Chain for persistent, verifiable storage.
    """

    def __init__(self, account: str, membase_id: str):
        self.account = account
        self.membase_id = membase_id
        self.enabled = bool(account)
        self._client = None

        if self.enabled:
            try:
                # Import Membase SDK
                from membase import MembaseClient as MB
                self._client = MB(
                    account=account,
                    membase_id=membase_id
                )
                print(f"Membase initialized: account={account[:10]}...")
            except ImportError:
                print("WARNING: Membase SDK not installed. Using local fallback.")
                print("Install with: pip install git+https://github.com/unibaseio/membase.git")
                self.enabled = False
            except Exception as e:
                print(f"WARNING: Membase init failed: {e}. Using local fallback.")
                self.enabled = False

        # Local fallback storage
        self._local_storage = {}
        self._storage_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'consumer_preferences_local.json'
        )
        self._load_local_storage()

    def _load_local_storage(self):
        """Load local fallback storage from disk"""
        if os.path.exists(self._storage_file):
            try:
                with open(self._storage_file, 'r') as f:
                    self._local_storage = json.load(f)
            except:
                self._local_storage = {}

    def _save_local_storage(self):
        """Save local fallback storage to disk"""
        with open(self._storage_file, 'w') as f:
            json.dump(self._local_storage, f, indent=2)

    async def save_preference(self, user_id: str, key: str, value: any) -> bool:
        """
        Save a user preference.

        Args:
            user_id: Unique user identifier
            key: Preference key (e.g., 'size', 'budget', 'colors')
            value: Preference value

        Returns:
            True if saved successfully
        """
        try:
            if self.enabled and self._client:
                # Save to Membase (on-chain)
                message = json.dumps({
                    "type": "preference",
                    "user_id": user_id,
                    "key": key,
                    "value": value,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                await self._client.save_message(message)
                print(f"Saved to Membase: {user_id}/{key}")

            # Always save to local storage as backup
            if user_id not in self._local_storage:
                self._local_storage[user_id] = {}
            self._local_storage[user_id][key] = {
                "value": value,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            self._save_local_storage()
            return True

        except Exception as e:
            print(f"Error saving preference: {e}")
            return False

    async def get_preferences(self, user_id: str) -> dict:
        """
        Get all preferences for a user.

        Args:
            user_id: Unique user identifier

        Returns:
            Dictionary of preferences
        """
        try:
            # Try Membase first if enabled
            if self.enabled and self._client:
                try:
                    messages = await self._client.get_messages(limit=100)
                    prefs = {}
                    for msg in messages:
                        try:
                            data = json.loads(msg)
                            if data.get("type") == "preference" and data.get("user_id") == user_id:
                                prefs[data["key"]] = data["value"]
                        except:
                            continue
                    if prefs:
                        return prefs
                except Exception as e:
                    print(f"Membase read failed, using local: {e}")

            # Fallback to local storage
            user_prefs = self._local_storage.get(user_id, {})
            return {k: v["value"] for k, v in user_prefs.items()}

        except Exception as e:
            print(f"Error getting preferences: {e}")
            return {}

    async def clear_preferences(self, user_id: str) -> bool:
        """Clear all preferences for a user."""
        try:
            if user_id in self._local_storage:
                del self._local_storage[user_id]
                self._save_local_storage()
            return True
        except Exception as e:
            print(f"Error clearing preferences: {e}")
            return False


# ========================================
# Preference Data Models
# ========================================
class UserPreferences(Model):
    """Standard user preference structure for shopping"""
    user_id: str
    shoe_size: str = ""           # e.g., "10", "10.5", "M10/W12"
    preferred_colors: list = []    # e.g., ["black", "gray", "navy"]
    max_budget: float = 0.0       # e.g., 200.0
    min_budget: float = 0.0       # e.g., 50.0
    preferred_brands: list = []    # e.g., ["AeroStride", "CloudTrail"]
    preferred_type: str = ""       # e.g., "trail", "road", "road fast"
    gender: str = ""              # e.g., "Men", "Women", "Men and Women"
    features: list = []           # e.g., ["Wide fit", "Arch Support"]
    season: str = ""              # e.g., "Summer", "Winter", "All-season"


class PreferenceRequest(Model):
    """Request to get/set preferences"""
    action: str  # "get", "set", "clear"
    user_id: str
    key: str = ""
    value: str = ""


class PreferenceResponse(Model):
    """Response with preferences"""
    user_id: str
    preferences: str  # JSON string of preferences
    success: bool
    message: str = ""


# ========================================
# Initialize Agent
# ========================================
agent_args = {
    "name": AGENT_NAME,
    "port": AGENT_PORT,
    "seed": AGENT_SEED,
}

if AGENTVERSE_MAILBOX_KEY:
    print("Configuring agent with Agentverse Mailbox...")
    agent_args["mailbox"] = True
else:
    print("Configuring agent for local execution...")
    agent_args["endpoint"] = [f"http://127.0.0.1:{AGENT_PORT}/submit"]

agent = Agent(**agent_args)

# Initialize Membase client
membase = MembaseClient(MEMBASE_ACCOUNT, MEMBASE_ID)


# ========================================
# Helper Functions
# ========================================
def parse_preference_command(text: str) -> tuple:
    """
    Parse natural language preference commands.

    Examples:
        "my size is 10" -> ("shoe_size", "10")
        "budget is £200" -> ("max_budget", 200.0)
        "I like black and gray shoes" -> ("preferred_colors", ["black", "gray"])
        "I prefer trail shoes" -> ("preferred_type", "trail")
    """
    text_lower = text.lower()

    # Size patterns
    if "size" in text_lower:
        import re
        match = re.search(r'size\s*(?:is\s*)?(\d+(?:\.\d+)?)', text_lower)
        if match:
            return ("shoe_size", match.group(1))

    # Budget patterns
    if "budget" in text_lower or "spend" in text_lower or "under" in text_lower:
        import re
        match = re.search(r'[£$]?\s*(\d+(?:\.\d+)?)', text)
        if match:
            return ("max_budget", float(match.group(1)))

    # Color patterns
    colors = ["black", "white", "gray", "grey", "navy", "blue", "red", "green", "multi", "limited"]
    found_colors = [c for c in colors if c in text_lower]
    if found_colors:
        return ("preferred_colors", found_colors)

    # Type patterns
    types = {"trail": "Trail", "road": "Road", "race": "Road race", "racing": "Road fast"}
    for keyword, type_val in types.items():
        if keyword in text_lower:
            return ("preferred_type", type_val)

    # Brand patterns
    brands = ["AeroStride", "CloudTrail", "FleetStep", "NimbusPath", "NovaStride",
              "PulseTrack", "RoadRift", "TerraSprint", "UrbanTempo", "VelociRun"]
    found_brands = [b for b in brands if b.lower() in text_lower]
    if found_brands:
        return ("preferred_brands", found_brands)

    # Gender patterns
    if "women" in text_lower or "female" in text_lower:
        return ("gender", "Women")
    elif "men" in text_lower or "male" in text_lower:
        return ("gender", "Men")

    # Season patterns
    if "summer" in text_lower:
        return ("season", "Summer")
    elif "winter" in text_lower:
        return ("season", "Winter")
    elif "all-season" in text_lower or "year-round" in text_lower:
        return ("season", "All-season")

    return (None, None)


def format_preferences_for_display(prefs: dict) -> str:
    """Format preferences for human-readable display"""
    if not prefs:
        return "No preferences saved yet."

    lines = ["**Your Shopping Preferences:**\n"]

    labels = {
        "shoe_size": "Shoe Size",
        "preferred_colors": "Preferred Colors",
        "max_budget": "Max Budget",
        "min_budget": "Min Budget",
        "preferred_brands": "Preferred Brands",
        "preferred_type": "Shoe Type",
        "gender": "Gender",
        "features": "Features",
        "season": "Season"
    }

    for key, value in prefs.items():
        label = labels.get(key, key.replace("_", " ").title())
        if isinstance(value, list):
            value = ", ".join(value) if value else "Not set"
        elif key == "max_budget" and value:
            value = f"£{value}"
        elif not value:
            continue
        lines.append(f"- **{label}**: {value}")

    return "\n".join(lines)


def preferences_to_filter_string(prefs: dict) -> str:
    """Convert preferences to a search filter string for product queries"""
    filters = []

    if prefs.get("preferred_type"):
        filters.append(prefs["preferred_type"])

    if prefs.get("max_budget"):
        filters.append(f"under £{prefs['max_budget']}")

    if prefs.get("preferred_colors"):
        colors = prefs["preferred_colors"]
        if isinstance(colors, list):
            filters.append(f"in {', '.join(colors)}")

    if prefs.get("gender"):
        filters.append(f"for {prefs['gender']}")

    if prefs.get("season"):
        filters.append(prefs["season"])

    if prefs.get("features"):
        features = prefs["features"]
        if isinstance(features, list):
            filters.extend(features)

    return " ".join(filters)


# ========================================
# Chat Protocol Handler
# ========================================
chat_proto = Protocol(spec=chat_protocol_spec)


def create_text_chat(text: str, end_session: bool = False) -> ChatMessage:
    """Create a text chat message."""
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=content,
    )


@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages for preference management."""
    ctx.logger.info(f"Received ChatMessage from {sender}")
    ctx.storage.set(str(ctx.session), sender)

    # Send acknowledgement
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id),
    )

    for item in msg.content:
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"Session started with {sender}")
            # Use sender as user_id for simplicity
            prefs = await membase.get_preferences(sender)
            if prefs:
                response = f"Welcome back! I remember your preferences.\n\n{format_preferences_for_display(prefs)}\n\nYou can update them anytime by telling me your size, budget, preferred colors, etc."
            else:
                response = "Hello! I'm your shopping preference assistant. Tell me about your preferences:\n\n- Your shoe size (e.g., 'my size is 10')\n- Your budget (e.g., 'budget is £200')\n- Preferred colors (e.g., 'I like black and gray')\n- Shoe type (e.g., 'I prefer trail shoes')\n\nYour preferences are stored securely on the blockchain!"
            await ctx.send(sender, create_text_chat(response))

        elif isinstance(item, TextContent):
            user_query = item.text.strip()
            ctx.logger.info(f"Query from {sender}: {user_query}")

            try:
                query_lower = user_query.lower()

                # Check for preference display request
                if any(kw in query_lower for kw in ["show", "what", "my preferences", "display", "current"]):
                    prefs = await membase.get_preferences(sender)
                    response = format_preferences_for_display(prefs)
                    await ctx.send(sender, create_text_chat(response))
                    continue

                # Check for clear request
                if any(kw in query_lower for kw in ["clear", "reset", "delete", "remove all"]):
                    await membase.clear_preferences(sender)
                    response = "Your preferences have been cleared. Start fresh by telling me your new preferences!"
                    await ctx.send(sender, create_text_chat(response))
                    continue

                # Try to parse preference command
                key, value = parse_preference_command(user_query)

                if key and value:
                    # Save the preference
                    await membase.save_preference(sender, key, value)

                    # Confirm and show updated preferences
                    prefs = await membase.get_preferences(sender)

                    # Format nice confirmation
                    if key == "shoe_size":
                        confirm = f"Got it! I've saved your shoe size as **{value}**."
                    elif key == "max_budget":
                        confirm = f"Got it! I've set your maximum budget to **£{value}**."
                    elif key == "preferred_colors":
                        confirm = f"Got it! I've noted your color preferences: **{', '.join(value)}**."
                    elif key == "preferred_type":
                        confirm = f"Got it! You prefer **{value}** shoes."
                    elif key == "preferred_brands":
                        confirm = f"Got it! I've noted your brand preferences: **{', '.join(value)}**."
                    else:
                        confirm = f"Got it! I've saved your {key.replace('_', ' ')}: **{value}**."

                    storage_note = " (stored on blockchain)" if membase.enabled else " (stored locally)"
                    response = f"{confirm}{storage_note}\n\n{format_preferences_for_display(prefs)}"
                    await ctx.send(sender, create_text_chat(response))
                else:
                    # Couldn't parse, provide help
                    response = """I couldn't understand that preference. Try:

- **Size**: "my size is 10" or "size 10.5"
- **Budget**: "budget is £200" or "under £150"
- **Colors**: "I like black and gray shoes"
- **Type**: "I prefer trail shoes" or "road running"
- **Brands**: "I like AeroStride and CloudTrail"
- **Season**: "summer shoes" or "winter running"

Say "show my preferences" to see what I have saved."""
                    await ctx.send(sender, create_text_chat(response))

            except Exception as e:
                ctx.logger.error(f"Error processing query: {e}")
                await ctx.send(sender, create_text_chat(f"Sorry, I encountered an error: {str(e)}"))

        elif isinstance(item, EndSessionContent):
            ctx.logger.info(f"Session ended with {sender}")


@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.debug(f"Received acknowledgement for {msg.acknowledged_msg_id}")


# ========================================
# Programmatic Protocol
# ========================================
preference_proto = Protocol(name="consumer_preferences", version="1.0.0")


@preference_proto.on_message(PreferenceRequest, replies=PreferenceResponse)
async def handle_preference_request(ctx: Context, sender: str, msg: PreferenceRequest):
    """Handle programmatic preference requests from other agents."""
    ctx.logger.info(f"Received PreferenceRequest from {sender}: {msg.action}")

    try:
        if msg.action == "get":
            prefs = await membase.get_preferences(msg.user_id)
            await ctx.send(sender, PreferenceResponse(
                user_id=msg.user_id,
                preferences=json.dumps(prefs),
                success=True,
                message="Preferences retrieved"
            ))

        elif msg.action == "set":
            # Parse value (could be JSON string for lists)
            try:
                value = json.loads(msg.value)
            except:
                value = msg.value

            success = await membase.save_preference(msg.user_id, msg.key, value)
            prefs = await membase.get_preferences(msg.user_id)
            await ctx.send(sender, PreferenceResponse(
                user_id=msg.user_id,
                preferences=json.dumps(prefs),
                success=success,
                message=f"Preference '{msg.key}' saved" if success else "Failed to save"
            ))

        elif msg.action == "clear":
            success = await membase.clear_preferences(msg.user_id)
            await ctx.send(sender, PreferenceResponse(
                user_id=msg.user_id,
                preferences="{}",
                success=success,
                message="Preferences cleared" if success else "Failed to clear"
            ))

        elif msg.action == "filter_string":
            # Get preferences and convert to filter string for product search
            prefs = await membase.get_preferences(msg.user_id)
            filter_str = preferences_to_filter_string(prefs)
            await ctx.send(sender, PreferenceResponse(
                user_id=msg.user_id,
                preferences=json.dumps({"filter_string": filter_str, "raw": prefs}),
                success=True,
                message="Filter string generated"
            ))

        else:
            await ctx.send(sender, PreferenceResponse(
                user_id=msg.user_id,
                preferences="{}",
                success=False,
                message=f"Unknown action: {msg.action}"
            ))

    except Exception as e:
        ctx.logger.error(f"Error handling preference request: {e}")
        await ctx.send(sender, PreferenceResponse(
            user_id=msg.user_id,
            preferences="{}",
            success=False,
            message=str(e)
        ))


# Include protocols
agent.include(chat_proto, publish_manifest=True)
agent.include(preference_proto, publish_manifest=True)


# ========================================
# Startup
# ========================================
@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Consumer Preference Agent started with address: {agent.address}")
    ctx.logger.info(f"Membase enabled: {membase.enabled}")
    if membase.enabled:
        ctx.logger.info(f"Membase account: {MEMBASE_ACCOUNT[:10]}...")
    else:
        ctx.logger.info("Using local storage fallback")
    ctx.logger.info(f"Protocol: consumer_preferences v1.0.0")


if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("CONSUMER PREFERENCE AGENT")
    print(f"{'='*60}")
    print(f"Port: {AGENT_PORT}")
    print(f"Membase: {'Enabled' if membase.enabled else 'Disabled (using local storage)'}")
    print(f"{'='*60}\n")
    agent.run()
