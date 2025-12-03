<!-- 9cd2fe75-e70b-4b20-9da3-10ded592c559 1504ac53-1339-4610-a1f3-1cb3b49fa9f2 -->
# Plan: Hybrid RAG with Vector DB & MeTTa

I will upgrade the agent to support unstructured queries by adding a local Vector DB. The system will use semantic search to find relevant products and then fetch their structured details from the MeTTa Knowledge Graph to provide rich context to the LLM.

## 1. Dependencies

- Add `chromadb` and `sentence-transformers` to `requirements.txt`.
- `chromadb`: Open-source local vector database.
- `sentence-transformers`: For generating local embeddings (e.g., `all-MiniLM-L6-v2`) without API costs.

## 2. `src/vector_store.py` (New)

Create a class `PIMVectorStore` to manage embeddings.

- **Init**: Initialize ChromaDB client (persistent storage in `./chroma_db`) and the embedding model.
- **`ingest_pim_data(json_data)`**:
    - Iterate through products in `Example_PIM_Data.json`.
    - **Text Generation**: Create a descriptive string for each product (e.g., *"Product Jack is a brown t-shirt in family clothing..."*) by combining family, categories, and attributes.
    - **Storage**: Upsert these strings into ChromaDB with the product `uuid` as metadata.
- **`search(query, k=3)`**:
    - Embed the user query.
    - Query ChromaDB.
    - Return a list of relevant `uuid`s and their distances.

## 3. `src/pim_rag.py` (Update)

Enhance `PIMRAG` to fetch comprehensive product contexts.

- **`get_full_product_context(uuid)`**:
    - Run multiple MeTTa queries to gather all info for a specific UUID:
        - Family: `(is_a uuid $f)`
        - Categories: `(has_category uuid $c)`
        - Attributes: `(has_attribute uuid $a $v)`
    - Return a structured dictionary or formatted string of all facts about this product.

## 4. `src/pim_utils.py` (Update)

Refactor `process_pim_query` to use the Hybrid approach.

- **Remove** rigid intent classification as the primary driver (can keep as optimization, but Hybrid is default).
- **New Flow**:

    1.  **Semantic Search**: Call `vector_store.search(query)` to get relevant product UUIDs.
    2.  **Context Enrichment**: For each found UUID, call `rag.get_full_product_context(uuid)` to get authoritative data from MeTTa.
    3.  **LLM Synthesis**: Construct a prompt containing the user query and the retrieved structured context.

        - *Prompt*: "User Question: {query}. Relevant Product Data: {formatted_metta_data}. Answer the user based on this data."

## 5. `src/pim_agent.py` (Update)

- Initialize `PIMVectorStore`.
- Call `ingest_pim_data` on startup (idempotent check ensures we don't duplicate logic if DB exists).
- Pass vector store to `process_pim_query`.

## 6. Execution Steps

1.  Update requirements.
2.  Implement Vector Store.
3.  Update RAG logic.
4.  Update Utils/Agent logic.
5.  Run integration test to verify "arbitrary" query handling (e.g., "Do you have anything suitable for summer?").

### To-dos

- [ ] Update `requirements.txt` with `chromadb` and `sentence-transformers`
- [ ] Create `src/vector_store.py` for ChromaDB management
- [ ] Update `src/pim_rag.py` with `get_full_product_context`
- [ ] Update `src/pim_utils.py` to implement Hybrid RAG flow
- [ ] Update `src/pim_agent.py` to initialize and wire Vector Store