#!/usr/bin/env python3
"""
MCP Server for Consumer Shopping Preferences

This server exposes user preference management as MCP tools for Claude Desktop.
Preferences are stored via Unibase Membase (decentralized on BNB Chain) with local fallback.

Environment Variables:
  - MEMBASE_ID: Your Membase identifier (required for blockchain storage)
  - MEMBASE_HUB: Membase hub URL (default: https://testnet.hub.membase.io)

Usage:
  Add to Claude Desktop config:

  {
    "mcpServers": {
      "consumer-preferences": {
        "command": "wsl",
        "args": ["-e", "bash", "-c", "cd /path/to/eComAgent && source venv/bin/activate && python src/mcp/consumer_mcp_server.py"],
        "env": {
          "MEMBASE_ID": "your_membase_id"
        }
      }
    }
  }

Tools:
  - save_preference: Save a user shopping preference
  - get_preferences: Get all preferences for a user
  - clear_preferences: Clear all preferences for a user
  - get_personalized_query: Enhance a product query with user preferences
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

# Add src to path for imports
src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, src_path)

# Suppress stdout during imports - MCP uses stdout for JSON-RPC
import io
_real_stdout = sys.stdout
sys.stdout = io.StringIO()

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Restore stdout
sys.stdout = _real_stdout


def log(message: str):
    """Log message to stderr with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", file=sys.stderr, flush=True)


# Load environment
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

log("=" * 60)
log("Consumer Preferences MCP Server Starting...")
log("=" * 60)


# ========================================
# Membase Blockchain Storage + Local Fallback
# ========================================
class PreferenceStore:
    """
    Storage for user preferences.
    Primary: Unibase Membase (decentralized on BNB Chain)
    Fallback: Local JSON file
    """

    def __init__(self):
        self.membase_id = os.getenv("MEMBASE_ID", "")
        self.membase_hub = os.getenv("MEMBASE_HUB", "https://testnet.hub.membase.io")
        self.membase_enabled = False
        self._memories = {}  # Dict of user_id -> MultiMemory

        # Try to initialize Membase
        if self.membase_id:
            try:
                from membase.memory.multi_memory import MultiMemory
                from membase.memory.message import Message
                self._MultiMemory = MultiMemory
                self._Message = Message
                self.membase_enabled = True
                log(f"Membase ENABLED - ID: {self.membase_id}")
                log(f"Membase Hub: {self.membase_hub}")
            except ImportError as e:
                log(f"Membase SDK import failed: {e}")
                log("Using local storage fallback")
            except Exception as e:
                log(f"Membase init failed: {e}")
                log("Using local storage fallback")
        else:
            log("MEMBASE_ID not set - using local storage only")
            log("Set MEMBASE_ID environment variable to enable blockchain storage")

        # Local fallback storage
        self._storage_file = os.path.join(src_path, 'mcp', 'consumer_preferences.json')
        self._storage = self._load_storage()
        log(f"Local fallback: {self._storage_file}")

    def _load_storage(self) -> dict:
        """Load preferences from local file"""
        if os.path.exists(self._storage_file):
            try:
                with open(self._storage_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_storage(self):
        """Save preferences to local file"""
        with open(self._storage_file, 'w') as f:
            json.dump(self._storage, f, indent=2)

    def _get_user_memory(self, user_id: str):
        """Get or create MultiMemory instance for a user"""
        if not self.membase_enabled:
            return None

        if user_id not in self._memories:
            # Create memory WITHOUT auto upload (we'll do it in background)
            self._memories[user_id] = self._MultiMemory(
                membase_account=user_id,
                auto_upload_to_hub=False,  # Don't block!
                default_conversation_id=f"preferences_{user_id}",
                preload_from_hub=False  # Don't block on load
            )
            log(f"Created Membase memory for user: {user_id}")

        return self._memories[user_id]

    def _sync_to_blockchain_background(self, user_id: str):
        """Sync user's preferences to blockchain in background thread"""
        import threading

        def sync():
            try:
                from membase.storage.hub import hub_client
                from membase.memory.serialize import serialize

                memory = self._memories.get(user_id)
                if memory:
                    messages = memory.get()
                    if messages:
                        # Upload all messages to hub (non-blocking)
                        hub_client.upload_hub(
                            owner=user_id,
                            filename=f"preferences_{user_id}",
                            msg=serialize(messages),
                            bucket=f"preferences_{user_id}",
                            wait=False  # Non-blocking!
                        )
                        log(f"Background sync queued: {user_id}")
            except Exception as e:
                log(f"Background sync error: {e}")

        thread = threading.Thread(target=sync, daemon=True)
        thread.start()

    def save_preference(self, user_id: str, key: str, value: any) -> dict:
        """Save a single preference (local first, blockchain in background)"""
        storage_type = "local"

        try:
            # Always save to local storage FIRST (fast, reliable)
            if user_id not in self._storage:
                self._storage[user_id] = {}

            self._storage[user_id][key] = {
                "value": value,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            self._save_storage()
            log(f"Saved to local: {user_id}/{key}")

            # Save to Membase memory (in-memory, non-blocking)
            if self.membase_enabled:
                try:
                    memory = self._get_user_memory(user_id)
                    if memory:
                        msg = self._Message(
                            name=f"pref_{key}",
                            content=json.dumps({
                                "key": key,
                                "value": value,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }),
                            role="user"
                        )
                        memory.add(msg)  # Just in-memory, fast!

                        # Trigger background blockchain sync
                        self._sync_to_blockchain_background(user_id)
                        storage_type = "local + blockchain (syncing)"
                        log(f"Saved to memory, background sync started: {user_id}/{key}")
                except Exception as e:
                    log(f"Membase save failed: {e}")
                    storage_type = "local only"

            return {
                "success": True,
                "message": f"Saved {key} for user {user_id}",
                "storage": storage_type
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_preferences(self, user_id: str) -> dict:
        """Get all preferences for a user (local primary, with memory merge)"""
        prefs = {}

        # Get from local storage (fast, reliable)
        user_data = self._storage.get(user_id, {})
        prefs = {k: v["value"] for k, v in user_data.items()}

        # Also check in-memory cache (includes recent saves)
        if self.membase_enabled:
            try:
                memory = self._get_user_memory(user_id)
                if memory:
                    messages = memory.get()
                    if messages:
                        for msg in messages:
                            if hasattr(msg, 'name') and msg.name.startswith('pref_'):
                                try:
                                    data = json.loads(msg.content)
                                    # Merge with local (memory takes precedence for recent saves)
                                    prefs[data['key']] = data['value']
                                except:
                                    pass
                        log(f"Merged {len(messages)} memory entries for {user_id}")
            except Exception as e:
                log(f"Memory retrieval note: {e}")

        return prefs

    def clear_preferences(self, user_id: str) -> dict:
        """Clear all preferences for a user"""
        # Clear local storage
        if user_id in self._storage:
            del self._storage[user_id]
            self._save_storage()

        # Clear Membase memory
        if self.membase_enabled and user_id in self._memories:
            try:
                del self._memories[user_id]
                log(f"Cleared Membase memory for {user_id}")
            except Exception as e:
                log(f"Error clearing Membase memory: {e}")

        return {"success": True, "message": f"Cleared preferences for {user_id}"}


# Initialize preference store
store = PreferenceStore()
log("Preference store initialized")


# ========================================
# Helper Functions
# ========================================
def format_preferences(prefs: dict) -> str:
    """Format preferences for display"""
    if not prefs:
        return "No preferences saved."

    lines = []
    labels = {
        "shoe_size": "Shoe Size",
        "preferred_colors": "Colors",
        "max_budget": "Max Budget",
        "min_budget": "Min Budget",
        "preferred_brands": "Brands",
        "preferred_type": "Shoe Type",
        "gender": "Gender",
        "features": "Features",
        "season": "Season"
    }

    for key, value in prefs.items():
        label = labels.get(key, key.replace("_", " ").title())
        if isinstance(value, list):
            value = ", ".join(value) if value else "Not set"
        elif key in ["max_budget", "min_budget"] and value:
            value = f"£{value}"
        lines.append(f"- {label}: {value}")

    return "\n".join(lines)


def preferences_to_query_enhancement(prefs: dict) -> str:
    """Convert preferences to search query enhancement"""
    enhancements = []

    if prefs.get("preferred_type"):
        enhancements.append(prefs["preferred_type"])

    if prefs.get("max_budget"):
        enhancements.append(f"under £{prefs['max_budget']}")

    if prefs.get("gender"):
        enhancements.append(f"for {prefs['gender']}")

    if prefs.get("season"):
        enhancements.append(prefs["season"])

    if prefs.get("preferred_colors"):
        colors = prefs["preferred_colors"]
        if isinstance(colors, list) and colors:
            enhancements.append(f"in {', '.join(colors[:2])}")  # Limit colors

    if prefs.get("preferred_brands"):
        brands = prefs["preferred_brands"]
        if isinstance(brands, list) and brands:
            enhancements.append(f"from {', '.join(brands[:2])}")  # Limit brands

    if prefs.get("features"):
        features = prefs["features"]
        if isinstance(features, list):
            enhancements.extend(features[:2])  # Limit features

    return " ".join(enhancements)


# ========================================
# MCP Server
# ========================================
log("Creating MCP server...")
mcp = FastMCP("Consumer Preferences")


@mcp.tool()
async def save_preference(user_id: str, preference_type: str, value: str) -> str:
    """
    Save a shopping preference for a user.

    Use this to remember user preferences like shoe size, budget, favorite colors, etc.
    Preferences are stored on BNB Chain via Unibase Membase for decentralized persistence.

    Args:
        user_id: Unique identifier for the user (use their name or a session ID)
        preference_type: Type of preference. Valid types:
            - shoe_size: Shoe size (e.g., "10", "10.5", "M10/W12")
            - max_budget: Maximum budget in GBP (e.g., "200")
            - min_budget: Minimum budget in GBP (e.g., "50")
            - preferred_colors: Comma-separated colors (e.g., "black,gray,navy")
            - preferred_brands: Comma-separated brands (e.g., "AeroStride,CloudTrail")
            - preferred_type: Shoe type (e.g., "trail", "road", "road fast")
            - gender: Target gender (e.g., "Men", "Women", "Men and Women")
            - features: Comma-separated features (e.g., "Wide fit,Arch Support")
            - season: Preferred season (e.g., "Summer", "Winter", "All-season")
        value: The preference value

    Returns:
        Confirmation of saved preference with storage type (blockchain or local)
    """
    log(f">>> save_preference: user={user_id}, type={preference_type}, value={value}")

    # Parse value for list types
    parsed_value = value
    if preference_type in ["preferred_colors", "preferred_brands", "features"]:
        parsed_value = [v.strip() for v in value.split(",") if v.strip()]
    elif preference_type in ["max_budget", "min_budget"]:
        try:
            # Remove currency symbols
            clean_value = value.replace("£", "").replace("$", "").strip()
            parsed_value = float(clean_value)
        except:
            return f"Error: Budget must be a number. Got: {value}"

    result = store.save_preference(user_id, preference_type, parsed_value)

    if result.get("success"):
        prefs = store.get_preferences(user_id)
        storage_type = result.get("storage", "local")

        # Add storage indicator
        if "blockchain" in storage_type:
            storage_icon = "⛓️"
            storage_note = "(syncing to BNB Chain in background)"
        else:
            storage_icon = "💾"
            storage_note = ""

        return f"""Preference saved! {storage_icon} {storage_note}

**{preference_type}**: {parsed_value}

**All preferences for {user_id}:**
{format_preferences(prefs)}"""
    else:
        return f"Error saving preference: {result.get('error', 'Unknown error')}"


@mcp.tool()
async def get_preferences(user_id: str) -> str:
    """
    Get all saved shopping preferences for a user.

    Use this to recall what a user has told you about their preferences
    before making product recommendations.

    Args:
        user_id: The user's identifier

    Returns:
        All saved preferences for the user
    """
    log(f">>> get_preferences: user={user_id}")

    prefs = store.get_preferences(user_id)

    if not prefs:
        return f"No preferences saved for {user_id}. Ask them about their shoe size, budget, preferred colors, etc."

    return f"""**Shopping Preferences for {user_id}:**

{format_preferences(prefs)}

Use these preferences to personalize product recommendations!"""


@mcp.tool()
async def clear_preferences(user_id: str) -> str:
    """
    Clear all saved preferences for a user.

    Use this when a user wants to start fresh or reset their preferences.

    Args:
        user_id: The user's identifier

    Returns:
        Confirmation that preferences were cleared
    """
    log(f">>> clear_preferences: user={user_id}")

    result = store.clear_preferences(user_id)
    return f"Preferences cleared for {user_id}. Ready to save new preferences!"


@mcp.tool()
async def get_personalized_query(user_id: str, base_query: str) -> str:
    """
    Enhance a product search query with user preferences.

    Use this BEFORE searching for products to create a personalized query.
    It combines the user's base query with their saved preferences.

    Example:
        base_query: "running shoes"
        With preferences (budget £200, trail, Men)
        Returns: "running shoes Trail under £200 for Men"

    Args:
        user_id: The user's identifier
        base_query: The original search query from the user

    Returns:
        Enhanced query string combining base query + preferences
    """
    log(f">>> get_personalized_query: user={user_id}, query={base_query}")

    prefs = store.get_preferences(user_id)

    if not prefs:
        return f"""No preferences found for {user_id}.

**Original query:** {base_query}

Consider asking the user about their preferences first (size, budget, colors, etc.) to provide personalized recommendations."""

    enhancement = preferences_to_query_enhancement(prefs)

    if enhancement:
        personalized_query = f"{base_query} {enhancement}".strip()
        return f"""**Personalized Query:**
{personalized_query}

**Applied preferences:**
{format_preferences(prefs)}

Use this enhanced query when searching for products to get personalized results!"""
    else:
        return f"""No applicable preferences to enhance this query.

**Original query:** {base_query}

**User preferences:**
{format_preferences(prefs)}"""


@mcp.tool()
async def save_multiple_preferences(user_id: str, preferences_json: str) -> str:
    """
    Save multiple preferences at once from a JSON string.

    Useful when a user provides several preferences in one message.

    Args:
        user_id: The user's identifier
        preferences_json: JSON string with preferences, e.g.:
            {"shoe_size": "10", "max_budget": 200, "preferred_colors": ["black", "gray"]}

    Returns:
        Confirmation of all saved preferences
    """
    log(f">>> save_multiple_preferences: user={user_id}")

    try:
        prefs_to_save = json.loads(preferences_json)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON. {str(e)}"

    saved = []
    errors = []

    for key, value in prefs_to_save.items():
        result = store.save_preference(user_id, key, value)
        if result.get("success"):
            saved.append(key)
        else:
            errors.append(f"{key}: {result.get('error', 'Unknown error')}")

    all_prefs = store.get_preferences(user_id)

    response = f"**Saved {len(saved)} preferences for {user_id}:**\n"
    response += f"{format_preferences(all_prefs)}"

    if errors:
        response += f"\n\n**Errors:**\n" + "\n".join(errors)

    return response


@mcp.tool()
async def check_blockchain_sync(user_id: str) -> str:
    """
    Check if preferences are synced to the blockchain.

    Use this to verify that a user's preferences have been stored on the
    BNB Chain via Membase. Shows both local and blockchain status.

    Args:
        user_id: The user's identifier

    Returns:
        Sync status showing local vs blockchain data
    """
    log(f">>> check_blockchain_sync: user={user_id}")

    import requests

    results = []

    # Check local storage
    local_prefs = store._storage.get(user_id, {})
    local_count = len(local_prefs)
    results.append(f"**Local Storage:** {local_count} preferences")
    if local_prefs:
        for key, data in local_prefs.items():
            results.append(f"  - {key}: {data.get('value', 'N/A')}")

    # Check Membase hub
    results.append("")
    results.append("**Blockchain (Membase Hub):**")

    if not store.membase_enabled:
        results.append("  - Membase not enabled (MEMBASE_ID not set)")
    else:
        try:
            hub_url = store.membase_hub
            response = requests.post(
                f"{hub_url}/api/conversation",
                data={"owner": user_id},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )

            if response.status_code == 200:
                conversations = response.json()
                if conversations and conversations != "null":
                    results.append(f"  - Found {len(conversations)} conversation(s) on chain")
                    for conv in conversations[:5]:  # Show first 5
                        results.append(f"    - {conv}")

                    # Try to get preference data
                    for conv in conversations[:3]:
                        try:
                            detail_resp = requests.post(
                                f"{hub_url}/api/conversation",
                                data={"owner": user_id, "id": conv},
                                headers={"Content-Type": "application/x-www-form-urlencoded"},
                                timeout=5
                            )
                            if detail_resp.status_code == 200:
                                detail = detail_resp.json()
                                if detail:
                                    results.append(f"  - Data synced: Yes")
                                    break
                        except:
                            pass
                else:
                    results.append("  - No data in conversations API")
                    results.append("  - Data may be in Memories (needle) - check link below")
            else:
                results.append(f"  - Hub returned status: {response.status_code}")

        except requests.Timeout:
            results.append("  - Hub timeout (server may be busy)")
        except Exception as e:
            results.append(f"  - Error checking hub: {str(e)[:50]}")

    # Add hub URL for manual verification
    results.append("")
    results.append(f"**Hub URL:** {store.membase_hub}")
    results.append(f"**Membase ID:** {store.membase_id}")

    # Add direct verification links
    results.append("")
    results.append("**Verify on Blockchain (Manual):**")
    results.append(f"  - Memories: {store.membase_hub}/needle.html?owner={user_id}")
    results.append(f"  - Look for: `preferences_{user_id}`")

    return "\n".join(results)


log("=" * 60)
log("Consumer Preferences MCP Server READY")
log("Tools: save_preference, get_preferences, clear_preferences,")
log("       get_personalized_query, save_multiple_preferences,")
log("       check_blockchain_sync")
log("=" * 60)


if __name__ == "__main__":
    log("Waiting for requests from Claude Desktop...")
    mcp.run()
