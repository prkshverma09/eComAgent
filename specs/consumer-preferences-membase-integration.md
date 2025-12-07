# Consumer Preferences with Membase Blockchain Integration

## Hackathon Bounty Alignment

**Challenge:** Build an On-Chain Immortal AI Agent with Decentralized Memory and Cross-Platform Interoperability on BNB Chain.

| Requirement | Implementation Status |
|-------------|----------------------|
| Use Unibase Membase (decentralized AI memory layer) | ✅ Implemented |
| Sovereign memory | ✅ User-owned preferences on-chain |
| Cross-platform interoperability | ✅ MCP protocol for Claude Desktop |
| Autonomously manage data | ✅ Auto-sync to blockchain |
| Evolve based on interactions | ✅ Preferences improve recommendations |
| Working demo | ✅ Claude Desktop integration |
| Source code on GitHub | ✅ eComAgent repository |
| Documentation | ✅ This document |

---

## Overview

This feature enables AI agents to remember user shopping preferences (shoe size, budget, colors, brands, etc.) and store them persistently on the **BNB Chain blockchain** via **Unibase Membase**.

### Key Features

- **Decentralized Storage**: Preferences stored on BNB Chain via Membase hub
- **Sovereign Memory**: Users own their data on-chain
- **Local Fallback**: Automatic fallback to local JSON if blockchain unavailable
- **MCP Integration**: Exposed as Claude Desktop tools via Model Context Protocol
- **Personalized Search**: Enhance product queries with saved preferences
- **Non-Blocking Sync**: Fast response with background blockchain uploads

### Architecture Diagram

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  Claude Desktop │────▶│  Consumer MCP Server │────▶│  Membase SDK        │
│  (User Chat)    │     │  (consumer_mcp_      │     │  (MultiMemory)      │
└─────────────────┘     │   server.py)         │     └──────────┬──────────┘
                        └──────────────────────┘                │
                                   │                            │
                                   ▼                            ▼
                        ┌──────────────────┐         ┌─────────────────────┐
                        │  Local Fallback  │         │  Membase Hub        │
                        │  (JSON file)     │         │  (BNB Chain)        │
                        └──────────────────┘         └─────────────────────┘
                                                              │
                                                              ▼
                                                     ┌─────────────────────┐
                                                     │  BNB Chain Testnet  │
                                                     │  (On-Chain Storage) │
                                                     └─────────────────────┘
```

---

## How It Works

### 1. Storage Layer

The system uses a dual-storage approach:

**Primary: Membase Blockchain (BNB Chain)**
- Uses `membase.memory.multi_memory.MultiMemory` class
- Each user gets a separate memory instance
- Background uploads to Membase hub (non-blocking)
- Data persists on BNB Chain - survives agent restarts

**Fallback: Local JSON**
- Stored in `src/mcp/consumer_preferences.json`
- Automatic fallback if blockchain unavailable
- Always saved as backup for reliability

### 2. Data Flow

```
User says "I wear size 10"
        │
        ▼
Claude Desktop calls save_preference("user_id", "shoe_size", "10")
        │
        ▼
PreferenceStore.save_preference()
        │
        ├──▶ Save to local JSON (immediate, ~8ms)
        │
        └──▶ Return to user (fast response)
                │
                └──▶ Background thread uploads to Membase Hub
                            │
                            ▼
                     BNB Chain (on-chain storage)
```

### 3. Preference Types Supported

| Type | Description | Example Value |
|------|-------------|---------------|
| `shoe_size` | Shoe size | "10", "10.5", "M10/W12" |
| `max_budget` | Maximum budget (GBP) | "200", "150.50" |
| `min_budget` | Minimum budget (GBP) | "50" |
| `preferred_colors` | Comma-separated colors | "black,gray,navy" |
| `preferred_brands` | Comma-separated brands | "AeroStride,CloudTrail" |
| `preferred_type` | Shoe type | "trail", "road", "road fast" |
| `gender` | Target gender | "Men", "Women" |
| `features` | Comma-separated features | "Wide fit,Arch Support" |
| `season` | Preferred season | "Summer", "Winter" |

---

## Setup Instructions

### Prerequisites

- Python 3.9+
- Virtual environment with project dependencies
- Claude Desktop installed
- (Optional) BNB Chain wallet for full on-chain features

### Step 1: Install Membase SDK

```bash
cd /mnt/e/Hackathon/UK\ AI\ Agent\ Hackathon\ Ep3/eComAgent
source venv/bin/activate

# Install from PyPI
pip install membase

# Or from GitHub (latest)
pip install git+https://github.com/unibaseio/membase.git
```

The SDK installs with dependencies:
- `web3` - Ethereum/BNB Chain interaction
- `eth-account` - Wallet and signing
- `chromadb` - Local vector storage
- `aiohttp` - Async HTTP client

### Step 2: Configure Environment Variables

Add to your `.env` file:

```bash
# Unibase Membase Configuration (Decentralized Memory on BNB Chain)
# Required for blockchain storage:
MEMBASE_ID=ecomagent_consumer_prefs

# Optional - defaults to testnet:
MEMBASE_HUB=https://testnet.hub.membase.io

# Optional - for signed on-chain transactions:
# MEMBASE_ACCOUNT=0x_your_wallet_address
# MEMBASE_SECRET_KEY=your_private_key
```

**Environment Variables Explained:**

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `MEMBASE_ID` | Yes | Your unique identifier on Membase | (none - disables blockchain) |
| `MEMBASE_HUB` | No | Membase hub URL | `https://testnet.hub.membase.io` |
| `MEMBASE_ACCOUNT` | No | Wallet address for signing | (uses hub default) |
| `MEMBASE_SECRET_KEY` | No | Private key for transactions | (uses hub default) |

### Step 3: Configure Claude Desktop

The MCP server configuration at:
`C:\Users\<username>\AppData\Roaming\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "consumer-preferences": {
      "command": "wsl",
      "args": [
        "-e", "bash", "-c",
        "cd /mnt/e/Hackathon/UK\\ AI\\ Agent\\ Hackathon\\ Ep3/eComAgent && source venv/bin/activate && python src/mcp/consumer_mcp_server.py"
      ]
    }
  }
}
```

### Step 4: Restart Claude Desktop

1. Close Claude Desktop completely
2. Reopen Claude Desktop
3. The consumer-preferences MCP server will start automatically

### Step 5: Verify Setup

Check the MCP server logs at:
`C:\Users\<username>\AppData\Roaming\Claude\logs\mcp-server-consumer-preferences.log`

You should see:
```
[timestamp] Consumer Preferences MCP Server Starting...
[timestamp] Membase ENABLED - ID: ecomagent_consumer_prefs
[timestamp] Membase Hub: https://testnet.hub.membase.io
[timestamp] Consumer Preferences MCP Server READY
[timestamp] Tools: save_preference, get_preferences, clear_preferences,
[timestamp]        get_personalized_query, save_multiple_preferences,
[timestamp]        check_blockchain_sync
```

---

## Usage Guide

### Using in Claude Desktop

Once set up, you can use natural language with Claude to manage preferences:

**Saving Preferences:**
```
User: "I wear size 10 shoes and my budget is under £200"
Claude: (calls save_preference tool automatically)
Response: "Preference saved! ⛓️ (syncing to BNB Chain in background)"
```

**Retrieving Preferences:**
```
User: "What are my saved preferences?"
Claude: (calls get_preferences tool)
Response: "Your preferences: Shoe Size: 10, Max Budget: £200..."
```

**Checking Blockchain Sync:**
```
User: "Check if my preferences are on the blockchain"
Claude: (calls check_blockchain_sync tool)
Response: "Local Storage: 2 preferences... Blockchain: Found 1 conversation on chain"
```

**Personalized Search:**
```
User: "Find me running shoes"
Claude: (calls get_personalized_query, then product search)
Enhanced query: "running shoes under £200 size 10"
```

### MCP Tools Reference

#### 1. `save_preference`

Save a single preference to blockchain storage.

**Parameters:**
- `user_id` (string): Unique user identifier
- `preference_type` (string): Type of preference (see table above)
- `value` (string): The preference value

**Example:**
```json
{
  "user_id": "aswin",
  "preference_type": "shoe_size",
  "value": "10"
}
```

**Response:**
```
Preference saved! ⛓️ (syncing to BNB Chain in background)

**shoe_size**: 10

**All preferences for aswin:**
- Shoe Size: 10
```

#### 2. `get_preferences`

Retrieve all saved preferences for a user.

**Parameters:**
- `user_id` (string): User identifier

**Response:**
```
**Shopping Preferences for aswin:**

- Shoe Size: 10
- Max Budget: £200
- Colors: black, gray
- Brands: AeroStride, CloudTrail
```

#### 3. `clear_preferences`

Clear all preferences for a user.

**Parameters:**
- `user_id` (string): User identifier

**Response:**
```
Preferences cleared for aswin. Ready to save new preferences!
```

#### 4. `get_personalized_query`

Enhance a search query with user preferences.

**Parameters:**
- `user_id` (string): User identifier
- `base_query` (string): Original search query

**Example:**
```json
{
  "user_id": "aswin",
  "base_query": "running shoes"
}
```

**Response:**
```
**Personalized Query:**
running shoes trail under £200 for Men in black, gray from AeroStride

**Applied preferences:**
- Shoe Type: trail
- Max Budget: £200
- Gender: Men
- Colors: black, gray
- Brands: AeroStride
```

#### 5. `save_multiple_preferences`

Save multiple preferences at once.

**Parameters:**
- `user_id` (string): User identifier
- `preferences_json` (string): JSON object with preferences

**Example:**
```json
{
  "user_id": "aswin",
  "preferences_json": "{\"shoe_size\": \"10\", \"max_budget\": 200, \"preferred_colors\": [\"black\", \"gray\"]}"
}
```

#### 6. `check_blockchain_sync`

Verify preferences are synced to blockchain.

**Parameters:**
- `user_id` (string): User identifier

**Response:**
```
**Local Storage:** 2 preferences
  - shoe_size: 10
  - max_budget: 200

**Blockchain (Membase Memories):**
  - ✅ Found 2 preference(s) on blockchain!
  - Bucket: `preferences_aswin`
  - Synced preferences:
    - shoe_size: 10
    - max_budget: 200

**Hub URL:** https://testnet.hub.membase.io
**Membase ID:** ecomagent_consumer_prefs

**Verify on Blockchain (Manual):**
  - Memories: https://testnet.hub.membase.io/needle.html?owner=aswin
  - Look for: `preferences_aswin`
```

---

## Verifying On-Chain Storage

### Method 1: Use check_blockchain_sync Tool

In Claude Desktop, ask:
```
"Check if my preferences are synced to blockchain"
```

This will show both local and blockchain data with synced preferences.

### Method 2: Membase Hub Dashboard (Browser)

Visit the Memories page directly:
```
https://testnet.hub.membase.io/needle.html?owner=YOUR_USER_ID
```

Look for `preferences_YOUR_USER_ID` entry. Click `[click to show]` to see data.

### Method 3: Check MCP Server Logs

Look for these messages:
```
Background sync queued: user_id
Downloading from hub for user: user_id
```

**Error indicators:**
```
Error during upload: 599 Server Error
```

### Method 4: Python SDK

```python
from membase.storage.hub import hub_client
hub_client.initialize("https://testnet.hub.membase.io")
data = hub_client.download_hub(owner="YOUR_USER_ID", filename="preferences_YOUR_USER_ID")
print(data)
```

---

## Technical Implementation

### File Structure

```
eComAgent/
├── src/
│   └── mcp/
│       ├── consumer_mcp_server.py    # Main MCP server
│       └── consumer_preferences.json  # Local fallback storage
├── .env                               # Environment configuration
└── specs/
    └── consumer-preferences-membase-integration.md  # This document
```

### Key Classes

#### PreferenceStore (`consumer_mcp_server.py`)

```python
class PreferenceStore:
    """
    Storage for user preferences.
    Primary: Unibase Membase (decentralized on BNB Chain)
    Fallback: Local JSON file
    """

    def __init__(self):
        # Initialize Membase if MEMBASE_ID is set
        if self.membase_id:
            from membase.memory.multi_memory import MultiMemory
            self._MultiMemory = MultiMemory
            self.membase_enabled = True

    def _get_user_memory(self, user_id: str):
        """Get or create MultiMemory instance for a user"""
        if user_id not in self._memories:
            self._memories[user_id] = self._MultiMemory(
                membase_account=user_id,
                auto_upload_to_hub=False,  # Non-blocking
                default_conversation_id=f"preferences_{user_id}",
                preload_from_hub=False     # Non-blocking
            )
        return self._memories[user_id]

    def _upload_to_hub_async(self, user_id: str, key: str, value: any):
        """Upload preference to Membase hub in background"""
        import threading
        def upload():
            from membase.storage.hub import hub_client
            hub_client.upload_hub(
                owner=user_id,
                filename=f"pref_{key}",
                msg=json.dumps({...}),
                bucket=f"preferences_{user_id}",
                wait=False  # Non-blocking
            )
        thread = threading.Thread(target=upload, daemon=True)
        thread.start()

    def save_preference(self, user_id: str, key: str, value: any):
        # 1. Save to local (fast, ~8ms)
        self._save_storage()

        # 2. Queue blockchain upload (background, non-blocking)
        if self.membase_enabled:
            self._upload_to_hub_async(user_id, key, value)
```

### Membase SDK Components Used

| Component | Purpose |
|-----------|---------|
| `MultiMemory` | Manages per-user memory |
| `Message` | Individual preference data unit |
| `hub_client` | HTTP client for Membase hub API |

### Hub API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/upload` | POST | Upload preference data |
| `/api/download` | POST | Retrieve preference data |
| `/api/conversation` | POST | List user conversations |

---

## Performance Optimizations

### Non-Blocking Blockchain Uploads

The MCP server uses a **local-first, blockchain-background** architecture:

1. **Local save** happens immediately (~8ms)
2. **Blockchain upload** queued in background thread
3. Response returned to user without waiting for blockchain

```
User Request
    │
    ▼
┌─────────────────────┐
│ Save to local JSON  │ ◄── ~8ms (immediate)
└──────────┬──────────┘
           │
           ├──────────────────────────────┐
           ▼                              ▼
    Return to User              Background Thread
    (fast response)             (blockchain upload)
                                      │
                                      ▼
                               Membase Hub
                               (BNB Chain)
```

### Why Non-Blocking?

The Membase hub can be slow or return errors (599 timeouts). Blocking on hub response would:
- Cause 4+ minute delays
- Risk MCP timeout (60s limit)
- Poor user experience

With non-blocking uploads:
- User sees response in <100ms
- Blockchain sync happens asynchronously
- Local storage ensures data safety

---

## Testing

### Manual Test - Local Save

```bash
cd /mnt/e/Hackathon/UK\ AI\ Agent\ Hackathon\ Ep3/eComAgent
source venv/bin/activate

python -c "
import time
start = time.time()
# Test local save speed
from src.mcp.consumer_mcp_server import store
result = store.save_preference('test_user', 'shoe_size', '10')
print(f'Time: {(time.time()-start)*1000:.1f}ms')
print(f'Result: {result}')
"
```

### Verify Blockchain Sync

Visit in browser:
```
https://testnet.hub.membase.io/needle.html?owner=test_user
```

Or use Python SDK:
```python
from membase.storage.hub import hub_client
hub_client.initialize("https://testnet.hub.membase.io")
data = hub_client.download_hub(owner="test_user", filename="preferences_test_user")
print(data)
```

### Run MCP Server Manually

```bash
python src/mcp/consumer_mcp_server.py
```

---

## Troubleshooting

### Issue: "MEMBASE_ID not set - using local storage only"

**Cause:** Environment variable not configured
**Solution:** Add `MEMBASE_ID=your_id` to `.env` file

### Issue: "Membase SDK import failed"

**Cause:** SDK not installed
**Solution:** `pip install membase`

### Issue: Preferences not syncing to blockchain

**Cause:** Network issues or hub unavailable
**Solution:**
1. Check internet connection
2. Verify hub is accessible: `curl https://testnet.hub.membase.io`
3. Check logs for 599 errors (hub overloaded, retry later)

### Issue: MCP server not starting

**Cause:** Python path or venv issues
**Solution:**
1. Verify venv exists: `ls venv/bin/python`
2. Check Claude Desktop logs
3. Test manually: `python src/mcp/consumer_mcp_server.py`

### Issue: Slow preference saving

**Cause:** Old blocking code
**Solution:** Update to latest `consumer_mcp_server.py` with non-blocking uploads

---

## Bounty Submission Checklist

### Submission Criteria

| Criteria | Status | Evidence |
|----------|--------|----------|
| Working demo using Unibase memory layer | ✅ | Claude Desktop integration |
| Source code on GitHub | ✅ | eComAgent repository |
| Deployment instructions | ✅ | This document |
| Testing instructions | ✅ | Testing section above |
| Documentation | ✅ | This document |
| Demo video | ⏳ | To be recorded |

### Judging Criteria Alignment

| Criteria (Weight) | How We Address It |
|-------------------|-------------------|
| **Innovation (30%)** | Novel hybrid RAG + blockchain memory for e-commerce AI agents. First MCP server using Membase for Claude Desktop. |
| **Technical Complexity (30%)** | Multi-layer architecture: MCP ↔ Membase ↔ BNB Chain. Non-blocking sync, local fallback, cross-platform. |
| **User Experience (20%)** | Natural language interface, instant responses (~8ms), automatic preference learning. |
| **Documentation (20%)** | Comprehensive specs, setup guides, API reference, troubleshooting. |

---

## Cross-Platform Interoperability

The consumer preferences can be accessed from multiple platforms:

1. **Claude Desktop** - via MCP tools
2. **Any LLM** - via Membase hub API
3. **Custom agents** - via Membase SDK
4. **Web apps** - via hub REST API

```python
# Access from any platform
from membase.storage.hub import hub_client

# Retrieve user preferences
conversations = hub_client.list_conversations(owner="user_id")
data = hub_client.download_hub(owner="user_id", filename="pref_shoe_size")
```

---

## References

- [Unibase Website](https://www.unibase.com/)
- [Unibase Documentation](https://openos-labs.gitbook.io/unibase-docs/)
- [Membase GitHub](https://github.com/unibaseio/membase)
- [BNB Chain](https://www.bnbchain.org/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [DoraHacks Hackathon](https://dorahacks.io/hackathon/1762)

---

## Changelog

### v1.0.3 (2025-12-06)
- Fixed `check_blockchain_sync` to use `hub_client.download_hub()`
- Data is stored in Membase Memories (needle), not Conversations
- Now shows actual synced preferences from blockchain
- Added direct verification link to needle.html
- Updated all documentation with correct verification methods

### v1.0.2 (2025-12-06)
- Added `check_blockchain_sync` tool for verification
- Updated documentation for hackathon bounty alignment
- Added cross-platform interoperability section
- Added bounty submission checklist

### v1.0.1 (2025-12-06)
- Fixed slow save issue (4 min → 8ms)
- Made blockchain uploads non-blocking
- Changed to local-first architecture
- Background thread for hub uploads

### v1.0.0 (2025-12-06)
- Initial implementation
- Membase SDK integration with MultiMemory
- MCP server with 5 preference tools
- Local JSON fallback storage
- BNB Chain testnet support
