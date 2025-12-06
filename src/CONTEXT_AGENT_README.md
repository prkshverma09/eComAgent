# Context Agent - Raw Product Context Retrieval Agent

A specialized agent built on the **Fetch.ai uAgents framework** that provides **raw product context retrieval** using a **Hybrid RAG** architecture. Unlike the PIM Agent, this agent returns structured product data **without LLM synthesis**, making it ideal for programmatic agent-to-agent communication.

## 🎯 What It Does

The Context Agent is a data retrieval service that:

1. **Retrieves raw product context** from the hybrid knowledge base
2. **Returns structured data** without LLM processing (faster, deterministic)
3. **Supports two protocols**:
   - **Chat Protocol** - For Agentverse UI interaction
   - **Context Retrieval Protocol** - For agent-to-agent communication
4. **Powers the MCP Server** for Claude Desktop integration

### Use Cases

```
┌─────────────────────────────────────────────────────────────┐
│  Use Case 1: Agentverse UI Chat                             │
│  User → Chat UI → Context Agent → Raw product context       │
├─────────────────────────────────────────────────────────────┤
│  Use Case 2: Agent-to-Agent Communication                   │
│  MCP Server → ContextRequest → Context Agent → Response     │
├─────────────────────────────────────────────────────────────┤
│  Use Case 3: Claude Desktop                                 │
│  Claude → MCP Server → Context Agent → Structured Data      │
└─────────────────────────────────────────────────────────────┘
```

### Example Queries

```
"waterproof trail shoes"
"marathon running shoes"
"stability shoes for overpronation"
"cushioned road running shoes under $200"
```

### Example Response (Raw Context)

```
--- Product Context ---
Product UUID: 5a2b3c4d5e6f7g8h9i0j
Family: Trail Running
Categories: Trail, Waterproof, Men
Attributes: brand: TerraSprint; product_name: Trail Master; price: 179.99; ...
-----------------------

--- Product Context ---
Product UUID: 1a2b3c4d5e6f7g8h9i0k
...
```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Context Agent                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │   uAgents    │    │  Chat Proto  │    │  Agentverse      │   │
│  │  Framework   │◄───│  (v0.3.0)    │◄───│  Mailbox         │   │
│  └──────────────┘    └──────────────┘    └──────────────────┘   │
│         │                    │                                  │
│         │            ┌───────┴───────┐                          │
│         │            │ Context Proto │◄── Other Agents/MCP      │
│         │            │  (v1.0.0)     │                          │
│         │            └───────────────┘                          │
│         ▼                                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Hybrid RAG System                           │   │
│  │  ┌─────────────────┐      ┌─────────────────────────┐    │   │
│  │  │   ChromaDB      │      │   MeTTa Knowledge       │    │   │
│  │  │  Vector Store   │      │   Graph                 │    │   │
│  │  │  (Semantic)     │      │   (Structured)          │    │   │
│  │  └────────┬────────┘      └───────────┬─────────────┘    │   │
│  │           │                           │                  │   │
│  │           └───────────┬───────────────┘                  │   │
│  │                       ▼                                  │   │
│  │              ┌─────────────────┐                         │   │
│  │              │  Raw Context    │  (No LLM Processing)    │   │
│  │              │  Aggregation    │                         │   │
│  │              └─────────────────┘                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Context Agent vs PIM Agent

| Feature | Context Agent | PIM Agent |
|---------|---------------|-----------|
| **Purpose** | Raw data retrieval | Conversational assistant |
| **LLM Processing** | ❌ No | ✅ Yes (ASI-1) |
| **Response Type** | Structured context | Natural language |
| **Speed** | Faster | Slower (LLM latency) |
| **Deterministic** | ✅ Yes | ❌ No (LLM variance) |
| **Primary Use** | Agent-to-agent | Human-to-agent |
| **Default Port** | 8007 | 8006 |

---

## 🛠️ Technologies Used

### 1. **uAgents Framework** (Fetch.ai)
- **Purpose**: Core agent framework for building autonomous, decentralized agents
- **Features Used**:
  - `Agent` class for agent lifecycle management
  - `Protocol` for defining message handlers
  - `Context` for state management and message passing
  - Mailbox integration for cloud-based communication

### 2. **Agent Chat Protocol (v0.3.0)**
- **Purpose**: Standardized communication for Agentverse UI chat
- **Source**: `uagents_core.contrib.protocols.chat`
- **Message Types**:
  - `ChatMessage` - Main message container
  - `ChatAcknowledgement` - Message receipt confirmation
  - `TextContent` - Text payload
  - `StartSessionContent` / `EndSessionContent` - Session lifecycle

### 3. **Context Retrieval Protocol (v1.0.0)**
- **Purpose**: Custom protocol for programmatic agent-to-agent communication
- **Message Types**:
  ```python
  class ContextRequest(Model):
      query: str  # The search query
  
  class ContextResponse(Model):
      context: str  # Raw product context
  ```
- **Usage**: Used by MCP Server to fetch context for Claude Desktop

### 4. **Agentverse Mailbox**
- **Purpose**: Cloud-hosted message relay enabling local agents to receive messages from the internet
- **Why Needed**: Local agents behind NAT/firewalls cannot receive direct connections
- **Configuration**: Set via `AGENTVERSE_MAILBOX_KEY` environment variable

### 5. **MeTTa Knowledge Graph** (Hyperon)
- **Purpose**: Structured knowledge representation and symbolic reasoning
- **Data Model**:
  ```metta
  (is_a <product_uuid> <family>)           ; Product taxonomy
  (has_category <product_uuid> <category>) ; Product categories
  (has_attribute <product_uuid> <attr> <value>) ; Product attributes
  ```
- **Queries**: Pattern matching for structured retrieval
- **Strengths**: Exact matches, relationships, attribute filtering

### 6. **ChromaDB Vector Store**
- **Purpose**: Semantic similarity search using embeddings
- **Embedding Model**: `all-MiniLM-L6-v2` (Sentence Transformers)
- **Storage**: Persistent local database (`./chroma_db`)
- **Strengths**: Natural language understanding, fuzzy matching, semantic relevance

### 7. **Hybrid RAG (Retrieval Augmented Generation)**
- **Purpose**: Combines Vector DB semantic search with Knowledge Graph structured retrieval
- **Flow**:
  1. User query → ChromaDB semantic search (find relevant products)
  2. Product UUIDs → MeTTa query (enrich with structured data)
  3. Combined context → Return raw (no LLM step)

---

## 📁 File Structure

```
src/
├── context_agent.py    # Main agent entry point (this file)
├── pim_rag.py          # MeTTa knowledge graph queries
├── pim_knowledge.py    # Knowledge graph initialization
├── pim_utils.py        # Context retrieval utilities
├── vector_store.py     # ChromaDB vector store operations
└── mcp/
    └── context_mcp_server_agent.py  # MCP server that uses this agent

data/
└── updated_running_shoes_full_catalog.json  # Product catalog
```

---

## 🚀 Running the Agent Locally

### Prerequisites

1. **Python 3.10+** (required for `uagents-core`)
2. **Agentverse Account** from [agentverse.ai](https://agentverse.ai) (optional, for UI chat)

### Step 1: Set Up Environment

```bash
# Create virtual environment with Python 3.10+
python3.11 -m venv venv311
source venv311/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```env
# Context Agent Configuration
CONTEXT_AGENT_NAME="Context Retrieval Agent"
CONTEXT_AGENT_PORT=8007
CONTEXT_AGENT_SEED=context_agent_seed_phrase

# Required for Agentverse UI Chat (optional)
AGENTVERSE_MAILBOX_KEY=your_mailbox_key_here

# Suppress warnings
TOKENIZERS_PARALLELISM=false
```

### Step 3: Run the Agent

```bash
cd src
python context_agent.py
```

**Expected Output:**
```
Loading .env from: /path/to/eComAgent/.env
.env exists: True
Configuring agent with Agentverse Mailbox...
Initializing Vector Store...
Starting Context Agent on port 8007...
Using official AgentChatProtocol v0.3.0

INFO:     [Context Retrieval Agent]: Context Agent started with address: agent1q05xsy54st3hpq09nqjznp2vs3dqhatdk0vknk0gxzm47gt94k5wklpj5h8
INFO:     [Context Retrieval Agent]: Using official AgentChatProtocol v0.3.0
INFO:     [Context Retrieval Agent]: Protocol digest: proto:a8f5...
INFO:     [Context Retrieval Agent]: Agent inspector available at https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A8007&address=agent1q05...
INFO:     [Context Retrieval Agent]: Starting server on http://0.0.0.0:8007 (Press CTRL+C to quit)
```

---

## 💬 Using the Agent

### Option 1: Via Agentverse UI Chat

1. Look for the Agent Inspector URL in the logs
2. Open the URL in your browser
3. Click **"Chat with Agent"**
4. Type your query (e.g., "waterproof trail shoes")
5. Receive raw product context in response

### Option 2: Via MCP Server (Claude Desktop)

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

### Option 3: Programmatic Agent-to-Agent

Send a `ContextRequest` message to the agent:

```python
from uagents import Agent, Context
from uagents.communication import send_sync_message

# Define the message model (must match context_agent.py)
class ContextRequest(Model):
    query: str

class ContextResponse(Model):
    context: str

# Send request
response = await send_sync_message(
    destination="agent1q05xsy54st3hpq09nqjznp2vs3dqhatdk0vknk0gxzm47gt94k5wklpj5h8",
    message=ContextRequest(query="waterproof trail shoes"),
    response_type=ContextResponse,
    timeout=10
)

print(response.context)
```

---

## 📡 Protocol Details

### Chat Protocol Messages

```
Incoming: ChatMessage
  └── content: [TextContent(text="user query")]

Outgoing: ChatAcknowledgement
  └── acknowledged_msg_id: <original_msg_id>

Outgoing: ChatMessage
  └── content: [TextContent(text="**Context Retrieved:**\n\n<raw_context>")]
```

### Context Retrieval Protocol Messages

```
Incoming: ContextRequest
  └── query: "waterproof trail shoes"

Outgoing: ContextResponse
  └── context: "--- Product Context ---\nProduct UUID: ...\n---"
```

---

## 🔧 Troubleshooting

### "AGENTVERSE_MAILBOX_KEY not found"
- Ensure `.env` file is in project root (not in `src/`)
- This is optional - agent will work locally without it

### "ModuleNotFoundError: uagents_core"
- Requires Python 3.10+
- Install with: `pip install uagents-core`

### "No relevant context found"
- Check that the product catalog JSON file exists
- Verify ChromaDB was initialized correctly

### "Agent not responding to ContextRequest"
- Ensure you're using the correct agent address
- Verify the agent is running on the expected port (8007)

---

## 📊 Data Source

The agent uses `data/updated_running_shoes_full_catalog.json` containing:

- **10 Running Shoe Brands**: AeroStride, CloudTrail, FleetStep, etc.
- **50 Products** with detailed attributes
- **Attributes**: Price, Material, Weight, Drop, Cushioning, Reviews, etc.

---

## 🔗 Related Files

| File | Purpose |
|------|---------|
| `pim_agent.py` | Full conversational agent with LLM |
| `mcp/context_mcp_server_agent.py` | MCP server that queries this agent |
| `pim_utils.py` | Shared `retrieve_pim_context()` function |

---

## 📚 References

- [uAgents Documentation](https://docs.fetch.ai/uAgents/)
- [Agent Chat Protocol](https://uagents.fetch.ai/docs/guides/chat_protocol)
- [Agentverse Documentation](https://docs.fetch.ai/agentverse/)
- [MeTTa Language](https://metta-lang.dev/)
- [ChromaDB Documentation](https://docs.trychroma.com/)

