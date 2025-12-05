# PIM Context MCP Server

This MCP (Model Context Protocol) server exposes the product knowledge base to Claude Desktop, allowing Claude to retrieve relevant product context when answering questions about running shoes.

## Setup

### 1. Prerequisites

- Python 3.10+ (use `venv311`)
- Claude Desktop installed

### 2. Configure Claude Desktop

Add the server to your Claude Desktop configuration:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pim-context": {
      "command": "/Users/paverma/PersonalProjects/eComAgent/venv311/bin/python",
      "args": ["/Users/paverma/PersonalProjects/eComAgent/src/mcp/context_mcp_server.py"]
    }
  }
}
```

### 3. Restart Claude Desktop

After adding the configuration, restart Claude Desktop for the changes to take effect.

## Usage

Once configured, Claude will automatically have access to the `get_product_context` tool. When you ask questions about running shoes, Claude can use this tool to retrieve relevant product information.

### Example Queries

- "What waterproof running shoes do you have?"
- "Show me marathon racing shoes"
- "What's the best shoe for trail running?"
- "Find running shoes under $100"
- "What brand is the Horizon Pro 3?"

## Tool Description

**`get_product_context`**

Retrieves relevant product information from the running shoes catalog. Returns structured product data including:
- Brand and product name
- Type (Road, Trail, Race, etc.)
- Materials and features
- Price, ratings, and reviews
- Size availability and fit information

## Testing

To test the server manually:

```bash
cd /Users/paverma/PersonalProjects/eComAgent
source venv311/bin/activate
python src/mcp/context_mcp_server.py
```

The server communicates via stdio, so it will wait for MCP protocol messages.

