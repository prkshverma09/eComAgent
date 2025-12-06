# eComAgent - Hybrid RAG E-Commerce Agent System

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

---

## 📋 Quick Reference (Hackathon Submission)

| | |
|---|---|
| **GitHub Repository** | [https://github.com/prkshverma09/eComAgent](https://github.com/prkshverma09/eComAgent) |

### Agent 1: E-Commerce Agent (PIM Agent)

| | |
|---|---|
| **Name** | E-Commerce Agent |
| **Handle** | `@e-com-agent` |
| **Address** | `agent1qdkcpq3239pvygtscjmd78fxgh3cmedgm5gw0xqy9wsvrevqvplr5jlyeg5` |
| **Purpose** | Conversational AI assistant that answers natural language product queries using Hybrid RAG + ASI-1 LLM |
| **Agentverse** | [View Profile](https://agentverse.ai/agents/details/agent1qdkcpq3239pvygtscjmd78fxgh3cmedgm5gw0xqy9wsvrevqvplr5jlyeg5/profile) |

### Agent 2: E-Com Context Retrieval Agent (Context Agent)

| | |
|---|---|
| **Name** | E-Com Context Retrieval Agent |
| **Handle** | `@e-com-context-retrieval-agent` |
| **Address** | `agent1q05xsy54st3hpq09nqjznp2vs3dqhatdk0vknk0gxzm47gt94k5wklpj5h8` |
| **Purpose** | Fast, deterministic raw product data retrieval for agent-to-agent communication and MCP Server integration |
| **Agentverse** | [View Profile](https://agentverse.ai/agents/details/agent1q05xsy54st3hpq09nqjznp2vs3dqhatdk0vknk0gxzm47gt94k5wklpj5h8/profile) |

### MCP Server: Consumer Preferences (Membase)

| | |
|---|---|
| **Name** | Consumer Preferences MCP Server |
| **Storage** | Local JSON + BNB Chain (Membase) |
| **Purpose** | Store user shopping preferences on blockchain for persistent, decentralized memory |
| **Hub URL** | https://testnet.hub.membase.io |

---

## 📖 Project Overview

A multi-agent e-commerce system built on the **Fetch.ai uAgents framework** that provides intelligent product information retrieval using a **Hybrid RAG (Retrieval Augmented Generation)** architecture combining **MeTTa Knowledge Graphs**, **ChromaDB Vector Database**, and **ASI-1 LLM**. The system also includes **Consumer Preferences** storage on **BNB Chain** via **Unibase Membase** for persistent, decentralized user preference management.

---

## 🌟 Key Features

- **🤖 Two Specialized Agents** - PIM Agent (conversational) and Context Agent (data retrieval)
- **🔍 Hybrid RAG** - Combines semantic search with structured knowledge graphs
- **💬 Agent Chat Protocol** - Chat via Agentverse UI or ASI:One
- **🔌 MCP Servers** - Claude Desktop integration for AI-powered product queries and consumer preferences
- **⛓️ Blockchain Memory** - Consumer preferences stored on BNB Chain via Unibase Membase
- **🧠 MeTTa Knowledge Graph** - Symbolic reasoning for structured product data
- **📊 ChromaDB Vector Store** - Semantic similarity search
- **⚡ ASI-1 LLM** - Natural language response synthesis

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          eComAgent System                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────┐    ┌─────────────────────────────┐        │
│  │      PIM Agent (8006)       │    │   Context Agent (8007)      │        │
│  │   Conversational Assistant  │    │   Raw Data Retrieval        │        │
│  │                             │    │                             │        │
│  │  ┌───────────────────────┐  │    │  ┌───────────────────────┐  │        │
│  │  │  Agent Chat Protocol  │  │    │  │  Agent Chat Protocol  │  │        │
│  │  │      (v0.3.0)         │  │    │  │      (v0.3.0)         │  │        │
│  │  └───────────────────────┘  │    │  └───────────────────────┘  │        │
│  │  ┌───────────────────────┐  │    │  ┌───────────────────────┐  │        │
│  │  │    Hybrid RAG +       │  │    │  │ Context Retrieval     │  │        │
│  │  │    ASI-1 LLM          │  │    │  │ Protocol (v1.0.0)     │  │        │
│  │  └───────────────────────┘  │    │  └───────────────────────┘  │        │
│  └──────────────┬──────────────┘    └──────────────┬──────────────┘        │
│                 │                                   │                       │
│                 └──────────────┬────────────────────┘                       │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     Shared Hybrid RAG System                         │   │
│  │  ┌─────────────────────┐         ┌─────────────────────────────┐     │   │
│  │  │     ChromaDB        │         │   MeTTa Knowledge Graph     │     │   │
│  │  │   Vector Store      │         │   (Hyperon)                 │     │   │
│  │  │  (Semantic Search)  │         │  (Structured Reasoning)     │     │   │
│  │  └──────────┬──────────┘         └─────────────┬───────────────┘     │   │
│  │             │                                  │                     │   │
│  │             └─────────────┬────────────────────┘                     │   │
│  │                           ▼                                          │   │
│  │              ┌─────────────────────────┐                             │   │
│  │              │    Product Catalog      │                             │   │
│  │              │  (50 Running Shoes)     │                             │   │
│  │              └─────────────────────────┘                             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                   Consumer Preferences (MCP Server)                  │   │
│  │  ┌─────────────────────┐         ┌─────────────────────────────┐     │   │
│  │  │   Local JSON        │         │   Unibase Membase           │     │   │
│  │  │   (Instant Save)    │────────▶│   (BNB Chain Sync)          │     │   │
│  │  └─────────────────────┘         └─────────────────────────────┘     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      External Integrations                           │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │   │
│  │  │  Agentverse     │  │   ASI:One       │  │   Claude Desktop    │   │   │
│  │  │  Mailbox + UI   │  │   Chat UI       │  │   (via MCP Server)  │   │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Agents Overview

### PIM Agent (E-Commerce Agent)

**Purpose**: Conversational AI assistant for natural language product queries

| Feature | Details |
|---------|---------|
| **Name** | E-Commerce Agent |
| **Handle** | `@e-com-agent` |
| **Address** | `agent1qdkcpq3239pvygtscjmd78fxgh3cmedgm5gw0xqy9wsvrevqvplr5jlyeg5` |
| **Port** | 8006 |
| **Protocol** | Agent Chat Protocol v0.3.0 |
| **LLM** | ASI-1 (asi1-mini) |
| **Response** | Natural language |
| **Best For** | Human-to-agent interaction |
| **Agentverse** | [View Profile](https://agentverse.ai/agents/details/agent1qdkcpq3239pvygtscjmd78fxgh3cmedgm5gw0xqy9wsvrevqvplr5jlyeg5/profile) |

**Example Interaction:**
```
User: "Show me waterproof trail running shoes under $200"

Agent: "Based on the product catalog, here are the waterproof trail
running shoes available:

1. **TerraSprint Trail Master** ($179.99)
   - Waterproof Gore-Tex membrane
   - Aggressive Vibram outsole
   ..."
```

📖 **Detailed Documentation**: [src/PIM_AGENT_README.md](src/PIM_AGENT_README.md)

---

### Context Agent (E-Com Context Retrieval Agent)

**Purpose**: Fast, deterministic product context retrieval without LLM processing

| Feature | Details |
|---------|---------|
| **Name** | E-Com Context Retrieval Agent |
| **Handle** | `@e-com-context-retrieval-agent` |
| **Address** | `agent1q05xsy54st3hpq09nqjznp2vs3dqhatdk0vknk0gxzm47gt94k5wklpj5h8` |
| **Port** | 8007 |
| **Protocols** | Agent Chat Protocol v0.3.0 + Context Retrieval v1.0.0 |
| **LLM** | None (raw data only) |
| **Response** | Structured context |
| **Best For** | Agent-to-agent, MCP Server |
| **Agentverse** | [View Profile](https://agentverse.ai/agents/details/agent1q05xsy54st3hpq09nqjznp2vs3dqhatdk0vknk0gxzm47gt94k5wklpj5h8/profile) |

**Example Response:**
```
--- Product Context ---
Product UUID: 5a2b3c4d5e6f7g8h9i0j
Family: Trail Running
Categories: Trail, Waterproof, Men
Attributes: brand: TerraSprint; product_name: Trail Master; price: 179.99; ...
-----------------------
```

📖 **Detailed Documentation**: [src/CONTEXT_AGENT_README.md](src/CONTEXT_AGENT_README.md)

---

### Consumer Preferences MCP Server

**Purpose**: Store user shopping preferences on BNB Chain via Unibase Membase

| Feature | Details |
|---------|---------|
| **Storage** | Local JSON + BNB Chain (Membase) |
| **Protocol** | MCP (Model Context Protocol) |
| **Blockchain** | BNB Chain Testnet |
| **Hub URL** | https://testnet.hub.membase.io |
| **Tools** | 6 MCP tools for preference management |

**Available Tools:**

| Tool | Description |
|------|-------------|
| `save_preference` | Save a single preference (shoe_size, max_budget, etc.) |
| `get_preferences` | Retrieve all saved preferences for a user |
| `clear_preferences` | Delete all preferences for a user |
| `get_personalized_query` | Enhance a search query with user preferences |
| `save_multiple_preferences` | Save multiple preferences at once |
| `check_blockchain_sync` | Verify if preferences are synced to blockchain |

**Example Interaction:**
```
User: "I wear size 10 shoes and my budget is under £200"

Claude: Preference saved! ⛓️ (syncing to BNB Chain in background)
- shoe_size: 10
- max_budget: 200
```

📖 **Detailed Documentation**: [docs/USER_GUIDE_CONSUMER_PREFERENCES.md](docs/USER_GUIDE_CONSUMER_PREFERENCES.md)

---

## 🔄 Agent Comparison

| Feature | PIM Agent | Context Agent |
|---------|-----------|---------------|
| **Purpose** | Conversational assistant | Raw data retrieval |
| **LLM Processing** | ✅ Yes (ASI-1) | ❌ No |
| **Response Type** | Natural language | Structured context |
| **Speed** | Slower (LLM latency) | Faster |
| **Deterministic** | ❌ No (LLM variance) | ✅ Yes |
| **Primary Use** | Human-to-agent | Agent-to-agent, MCP |
| **Port** | 8006 | 8007 |

---

## 🛠️ Technologies Used

### Core Framework
- **[uAgents](https://docs.fetch.ai/uAgents/)** - Fetch.ai's agent framework for autonomous, decentralized agents
- **[Agent Chat Protocol v0.3.0](https://uagents.fetch.ai/docs/guides/chat_protocol)** - Standardized agent communication
- **[Agentverse](https://agentverse.ai)** - Cloud platform for agent hosting and discovery

### Knowledge & Retrieval
- **[MeTTa](https://metta-lang.dev/)** (Hyperon) - Symbolic knowledge graph with pattern matching
- **[ChromaDB](https://docs.trychroma.com/)** - Vector database for semantic similarity search
- **[Sentence Transformers](https://www.sbert.net/)** - `all-MiniLM-L6-v2` for embeddings

### AI & LLM
- **[ASI-1 LLM](https://asi1.ai)** - Fetch.ai's `asi1-mini` model for response synthesis

### Integration
- **[MCP (Model Context Protocol)](https://modelcontextprotocol.io/)** - Claude Desktop integration via FastMCP
- **[Unibase Membase](https://membase.io/)** - Decentralized AI memory on BNB Chain for consumer preferences

---

## 📁 Project Structure

```
eComAgent/
├── data/
│   └── updated_running_shoes_full_catalog.json  # Product catalog (50 shoes)
├── docs/
│   └── USER_GUIDE_CONSUMER_PREFERENCES.md       # Consumer preferences guide
├── src/
│   ├── pim_agent.py          # PIM Agent - Conversational assistant
│   ├── context_agent.py      # Context Agent - Raw data retrieval
│   ├── pim_agent_client.py   # CLI client for testing PIM Agent
│   ├── pim_rag.py            # MeTTa knowledge graph queries
│   ├── pim_knowledge.py      # Knowledge graph initialization
│   ├── pim_utils.py          # LLM wrapper and query processing
│   ├── vector_store.py       # ChromaDB vector store operations
│   ├── PIM_AGENT_README.md   # PIM Agent documentation
│   ├── CONTEXT_AGENT_README.md # Context Agent documentation
│   └── mcp/
│       ├── context_mcp_server_agent.py  # MCP server for product search
│       └── consumer_mcp_server.py       # MCP server for consumer preferences (Membase)
├── tests/
│   ├── test_pim_agent.py             # Unit tests (mocked)
│   ├── test_pim_agent_live.py        # Live integration tests
│   ├── test_context_agent_integration.py
│   └── test_consumer_preferences.py  # Consumer preferences tests
├── .env                      # Environment variables (create from env.example)
├── env.example               # Example environment file
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (required for `uagents-core`)
- **ASI-1 API Key** from [asi1.ai](https://asi1.ai) (for PIM Agent)
- **Agentverse Account** from [agentverse.ai](https://agentverse.ai) (for cloud chat)

### Step 1: Clone & Set Up Environment

```bash
git clone https://github.com/prkshverma09/eComAgent.git
cd eComAgent

# Create virtual environment with Python 3.10+
python3.11 -m venv venv311
source venv311/bin/activate  # On Windows: venv311\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```bash
cp env.example .env
```

Edit `.env` with your credentials:

```env
# Required for PIM Agent (LLM)
ASI_ONE_API_KEY=your_asi1_api_key_here

# Agent Seeds (unique per agent)
AGENT_SEED=pim_agent_seed_phrase
CONTEXT_AGENT_SEED=context_agent_seed_phrase

# Agent Ports
AGENT_PORT=8006
CONTEXT_AGENT_PORT=8007

# Agent Names
AGENT_NAME="PIM Agent"
CONTEXT_AGENT_NAME="Context Retrieval Agent"

# Required for Agentverse UI Chat
AGENTVERSE_MAILBOX_KEY=your_mailbox_key_here

# Consumer Preferences (Membase blockchain storage)
MEMBASE_ID=your_membase_id
MEMBASE_HUB=https://testnet.hub.membase.io

# Suppress warnings
TOKENIZERS_PARALLELISM=false
```

### Step 3: Get Mailbox Key (for Agentverse UI)

1. Go to [agentverse.ai](https://agentverse.ai)
2. Navigate to **Agents** → **My Agents**
3. Click **+ New Agent** → Select **Mailbox Agent**
4. Copy the generated **Mailbox API Key**
5. Paste into `.env` as `AGENTVERSE_MAILBOX_KEY`

### Step 4: Run the Agents

**Terminal 1 - PIM Agent:**
```bash
cd src
python pim_agent.py
```

**Terminal 2 - Context Agent:**
```bash
cd src
python context_agent.py
```

---

## 💬 Interacting with Agents

### Via Agentverse UI

1. Look for the **Agent Inspector URL** in the agent logs:
   ```
   Agent inspector available at https://agentverse.ai/inspect/?uri=...
   ```
2. Open the URL in your browser
3. Click **"Chat with Agent"**

### Via ASI:One Chat

1. Go to [asi1.ai/chat](https://asi1.ai/chat)
2. Click **"+ New Chat"**
3. Search for your agent by address or name
4. Start chatting!

### Via CLI Client (Local Testing)

```bash
cd src
python pim_agent_client.py "Show me waterproof trail running shoes"
```

### Via Claude Desktop (MCP Server)

1. Start the Context Agent:
   ```bash
   cd src && python context_agent.py
   ```

2. Start the MCP Server:
   ```bash
   cd src/mcp && python context_mcp_server_agent.py
   ```

3. Configure Claude Desktop to use the MCP server

4. Ask Claude about products - it will query the Context Agent

### Via Claude Desktop (Consumer Preferences)

1. Locate Claude Desktop config file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the consumer-preferences MCP server:
   ```json
   {
     "mcpServers": {
       "consumer-preferences": {
         "command": "python",
         "args": ["/path/to/eComAgent/src/mcp/consumer_mcp_server.py"]
       }
     }
   }
   ```

3. Restart Claude Desktop completely (check system tray)

4. Tell Claude your preferences - they sync to BNB Chain via Membase:
   ```
   "I wear size 10 shoes and my budget is under £200"
   ```

5. Verify blockchain sync:
   ```bash
   curl -X POST https://testnet.hub.membase.io/api/conversation \
     -d "owner=default_user"
   ```

---

## 🧪 Testing

### Unit Tests (Mocked)

```bash
python tests/test_pim_agent.py
```

### Live Integration Tests

**Requires valid `ASI_ONE_API_KEY`**:

```bash
# Test PIM Agent
python tests/test_pim_agent_live.py

# Test Context Agent
python tests/test_context_agent_integration.py
```

### Consumer Preferences Tests

```bash
# Test consumer preferences with blockchain sync
python tests/test_consumer_preferences.py

# Verify blockchain storage
curl -X POST https://testnet.hub.membase.io/api/conversation \
  -d "owner=default_user"
```

---

## 📊 Data Source

The agents use `data/updated_running_shoes_full_catalog.json` containing:

- **10 Running Shoe Brands**: AeroStride, CloudTrail, FleetStep, NimbusPath, NovaStride, PulseTrack, RoadRift, TerraSprint, UrbanTempo, VelociRun
- **50 Products** with detailed attributes
- **Attributes**: Price, Material, Weight, Drop, Cushioning, Stability, Reviews, Ratings, etc.

### Example Product Structure

```json
{
  "Brand": "TerraSprint",
  "Product Name": "Trail Master",
  "Type": "Trail Running",
  "Gender": "Men",
  "Price": 179.99,
  "Material": "Gore-Tex Waterproof Mesh",
  "Weight (g)": 295,
  "Drop (mm)": 8,
  "Cushioning": "Moderate",
  "Description (Short)": "Waterproof trail running shoe with aggressive grip..."
}
```

---

## 🔧 Troubleshooting

### "AGENTVERSE_MAILBOX_KEY not found"
- Ensure `.env` file is in project root (not in `src/`)
- Check the key is not commented out

### "ModuleNotFoundError: uagents_core"
- Requires Python 3.10+
- Install with: `pip install uagents-core`

### "Chat messages not appearing in agent logs"
- Verify Mailbox is connected (look for "Mailbox session successfully resumed")
- Ensure you're using the Agent Chat Protocol link

### "LLM API Error"
- Check `ASI_ONE_API_KEY` is valid
- Verify internet connectivity

### "No relevant context found"
- Check that the product catalog JSON file exists
- Verify ChromaDB was initialized correctly

### "Consumer preferences not syncing to blockchain"
- Verify internet connectivity to `https://testnet.hub.membase.io`
- Check that the MCP server started without errors
- Preferences are saved locally first, blockchain sync happens in background
- Use `check_blockchain_sync` tool to verify sync status

### "MCP server disconnected"
- Ensure MCP server file path is correct in `claude_desktop_config.json`
- Restart Claude Desktop completely (check system tray)
- Check MCP server logs for errors

---

## 🔗 Extra Resources Required

To run this project, you will need:

| Resource | Description | Link |
|----------|-------------|------|
| **ASI-1 API Key** | Required for LLM-powered responses in PIM Agent | [Get API Key](https://asi1.ai) |
| **Agentverse Account** | Required for Mailbox and cloud chat functionality | [Sign Up](https://agentverse.ai) |
| **Python 3.10+** | Required for `uagents-core` package | [Download](https://www.python.org/downloads/) |
| **Unibase Membase** | Blockchain memory for consumer preferences (BNB Chain) | [Documentation](https://membase.io/) |

---

## 📚 References

- [uAgents Documentation](https://docs.fetch.ai/uAgents/)
- [Agent Chat Protocol](https://uagents.fetch.ai/docs/guides/chat_protocol)
- [Agentverse Documentation](https://docs.fetch.ai/agentverse/)
- [MeTTa Language](https://metta-lang.dev/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [ASI-1 API](https://asi1.ai/docs)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Unibase Membase SDK](https://github.com/unibaseio/membase-sdk-python)
- [Membase Documentation](https://membase.io/)

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2024 Prakash Verma

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📬 Contact

**Prakash Verma**

- GitHub: [@prkshverma09](https://github.com/prkshverma09)
- Project Repository: [eComAgent](https://github.com/prkshverma09/eComAgent)

---

## 🙏 Acknowledgments

- [Fetch.ai](https://fetch.ai) for the uAgents framework and ASI-1 LLM
- [Hyperon](https://hyperon.io) for MeTTa knowledge graph
- [ChromaDB](https://www.trychroma.com/) for vector database
- [Anthropic](https://anthropic.com) for Claude and MCP
- [Unibase](https://membase.io/) for Membase blockchain memory SDK
