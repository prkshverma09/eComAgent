# Plan: Implement PIM Agent

I will create a set of Python files in `src/` to implement an agent that answers questions about the PIM data using the MeTTa knowledge graph.

## 1. `src/pim_rag.py`
Create a `PIMRAG` class that wraps the MeTTa queries.
- **Constructor**: Accepts `metta_instance`.
- **Methods**:
    - `get_product_family(uuid)`: Matches `(is_a uuid $family)`.
    - `get_product_categories(uuid)`: Matches `(has_category uuid $cat)`.
    - `get_product_attribute(uuid, attribute)`: Matches `(has_attribute uuid attribute $val)`.
    - `find_products_by_category(category)`: Matches `(has_category $uuid category)`.
    - `find_products_by_attribute(attribute, value)`: Matches `(has_attribute $uuid attribute value)`.
- **Constraint**: No `add_knowledge` method will be implemented.

## 2. `src/pim_utils.py`
Create utilities for LLM interaction and query processing.
- **Class `LLM`**: Re-use the `OpenAI` client wrapper from `example/metta/utils.py`.
- **Function `get_pim_intent(query, llm)`**:
    - Use LLM to classify query into intents: `get_family`, `get_category`, `get_attribute`, `find_by_category`, `unknown`.
    - Extract entities: `uuid`, `attribute_name`, `category_name`.
- **Function `process_pim_query(query, rag, llm)`**:
    - Call `get_pim_intent`.
    - Execute corresponding method in `PIMRAG`.
    - Format the output into a human-readable response using the LLM (humanize).

## 3. `src/pim_agent.py`
Create the uAgent entry point.
- **Setup**:
    - Initialize `MeTTa`.
    - Call `initialize_pim_knowledge_graph(metta, "data/Example_PIM_Data.json")`.
    - Initialize `PIMRAG(metta)` and `LLM`.
    - Create `Agent` with `chat_protocol`.
- **Handlers**:
    - `@chat_proto.on_message(ChatMessage)`: Receive query, call `process_pim_query`, send back response.

## 4. `requirements.txt`
- Ensure `uagents`, `openai`, `python-dotenv` are listed (they seem to be used in the example but check if they need to be added).

## 5. Todos (Completed)
- [x] Create `src/pim_rag.py`
- [x] Create `src/pim_utils.py`
- [x] Create `src/pim_agent.py`
- [x] Update `requirements.txt` with agent dependencies
- [x] Create .env file template
- [x] Test installation of new dependencies
- [x] Write integration test for Agent logic (`tests/test_pim_agent.py`)
- [x] Test `src/pim_agent.py` script executability (dry run)
