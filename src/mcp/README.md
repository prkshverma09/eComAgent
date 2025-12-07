# MCP Servers for eComAgent

This directory contains MCP (Model Context Protocol) servers that integrate with Claude Desktop.

## Available Servers

| Server | File | Purpose |
|--------|------|---------|
| **Product Search** | `context_mcp_server.py` | Retrieves product information from the running shoes catalog |
| **Consumer Preferences** | `consumer_mcp_server.py` | Stores user preferences on BNB Chain via Membase |

---

## Product Search MCP Server

Exposes the product knowledge base to Claude Desktop using Hybrid RAG (MeTTa + ChromaDB).

### Tool: `get_product_context`

Retrieves relevant product information from the running shoes catalog:
- Brand and product name
- Type (Road, Trail, Race, etc.)
- Materials and features
- Price, ratings, and reviews

### Example Queries
- "What waterproof running shoes do you have?"
- "Show me marathon racing shoes"
- "Find running shoes under $100"

---

## Consumer Preferences MCP Server

Stores user shopping preferences on the BNB Chain blockchain via Unibase Membase.

### Tools

| Tool | Description |
|------|-------------|
| `save_preference` | Save a single preference |
| `get_preferences` | Get all saved preferences |
| `clear_preferences` | Clear all preferences |
| `get_personalized_query` | Enhance search with preferences |
| `save_multiple_preferences` | Save multiple at once |
| `check_blockchain_sync` | Verify blockchain storage |

### Example Queries
- "I wear size 10 shoes"
- "My budget is under £200"
- "Check my blockchain sync status"

### Verify On-Chain Storage
Visit: `https://testnet.hub.membase.io/needle.html?owner=YOUR_USER_ID`

---

## Setup

### 1. Prerequisites

- Python 3.10+ (use `venv311`)
- Claude Desktop installed

### 2. Configure Claude Desktop

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "product-search": {
      "command": "/path/to/eComAgent/venv311/bin/python",
      "args": ["/path/to/eComAgent/src/mcp/context_mcp_server.py"]
    },
    "consumer-preferences": {
      "command": "/path/to/eComAgent/venv311/bin/python",
      "args": ["/path/to/eComAgent/src/mcp/consumer_mcp_server.py"]
    }
  }
}
```

### 3. Restart Claude Desktop

Restart Claude Desktop for changes to take effect.

---

## Testing

```bash
cd /path/to/eComAgent
source venv311/bin/activate

# Test product search server
python src/mcp/context_mcp_server.py

# Test consumer preferences server
python src/mcp/consumer_mcp_server.py
```

The servers communicate via stdio (JSON-RPC).

