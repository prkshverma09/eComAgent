# eComAgent

A Python project for e-commerce agent functionality, powered by a **Hybrid RAG** system that combines a Knowledge Graph (MeTTa) with a Vector Database (ChromaDB) and an LLM (ASI:One/OpenAI).

## Project Structure

- `data/`: Contains PIM data files (e.g., `Example_PIM_Data.json`).
- `src/`: Source code for the agent, RAG logic, and vector store.
  - `pim_agent.py`: Main entry point for the uAgent.
  - `pim_rag.py`: Knowledge Graph logic using Hyperon/MeTTa.
  - `vector_store.py`: Semantic search logic using ChromaDB.
- `tests/`: Integration tests.
- `requirements.txt`: Python dependencies.

## Setup

1. **Create and Activate Virtual Environment**:
   It is recommended to use **Python 3.9** or newer (compatible with `hyperon` and `uagents`).
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy the example environment file and fill in your details:
   ```bash
   cp env.example .env
   ```

   **Required `.env` variables:**
   - `ASI_ONE_API_KEY`: API Key for the LLM (OpenAI compatible).
   - `AGENT_SEED`: A random string to secure your agent's identity (e.g., generated via `openssl rand -hex 16`).
   - `AGENTVERSE_MAILBOX_KEY`: (Optional) Required if you want to connect your local agent to the Agentverse network. Get this from [Agentverse.ai](https://agentverse.ai).

## Testing

### Automated Tests
We provide integration tests to verify the logic without needing to run the full agent network.

1. **Run Logic Tests (Mocked)**:
   Verifies the internal logic flow using mocked LLM and Vector Store.
   ```bash
   python tests/test_pim_agent.py
   ```

2. **Run Live Integration Tests**:
   **Requires valid `ASI_ONE_API_KEY`**. Sends real queries to the LLM and Vector Store to verify end-to-end RAG performance.
   ```bash
   python tests/test_pim_agent_live.py
   ```

## Running the Agent

### 1. Local Run
To start the agent on your machine:
```bash
python src/pim_agent.py
```
*   The agent will initialize the Knowledge Graph and Vector Store (ingesting data from `data/Example_PIM_Data.json`).
*   It will print its **uAgent Address** (starts with `agent1...`) to the console.

### 2. Connect to Agentverse (Public Access)
To let friends or other agents interact with your local agent:
1.  Register your agent on [Agentverse.ai](https://agentverse.ai) as a **Local Agent**.
2.  Get your **Mailbox API Key**.
3.  Add it to `.env` as `AGENTVERSE_MAILBOX_KEY`.
4.  Restart your agent: `python src/pim_agent.py`.
5.  Your agent is now online and reachable via the Agentverse Explorer!

### 3. Interact
You can interact with your running agent via:
- **Agentverse**: Search for your agent address in the Explorer and click "Message".
- **Another uAgent**: Write a script to send messages to your agent's address.

**Example Queries:**
- "What family does product fc24e6c3... belong to?"
- "Do you have any summer clothing?"
- "What is the color of this t-shirt?"
