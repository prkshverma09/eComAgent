import json
from openai import OpenAI
from pim_rag import PIMRAG
from vector_store import PIMVectorStore

class LLM:
    def __init__(self, api_key):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.asi1.ai/v1"
        )

    def create_completion(self, prompt, max_tokens=300):
        completion = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="asi1-mini",
            max_tokens=max_tokens
        )
        return completion.choices[0].message.content

def process_pim_query(query: str, rag: PIMRAG, llm: LLM, vector_store: PIMVectorStore = None):
    """
    Process the user query using the Hybrid RAG system (Vector DB + MeTTa).
    """
    if vector_store:
        # print(f"DEBUG: Using Hybrid RAG for query: '{query}'") # Silencing log for cleaner output
        
        # 1. Semantic Search to find relevant products
        # Get top 3 results
        search_results = vector_store.search(query, k=3)

        if not search_results:
            return "I couldn't find any relevant products in our catalog matching your query."

        # 2. Enrich with structured data from MeTTa
        context_blocks = []
        for result in search_results:
            uuid = result['uuid']
            # Fetch structured context from MeTTa
            metta_context = rag.get_full_product_context(uuid)
            context_blocks.append(f"--- Product Context ---\n{metta_context}\n-----------------------")

        full_context = "\n\n".join(context_blocks)

        # 3. LLM Synthesis
        prompt = (
            f"User Question: '{query}'\n\n"
            f"Below is detailed product information retrieved from the knowledge base:\n"
            f"{full_context}\n\n"
            "Using ONLY the product information above, answer the user's question.\n"
            "If the information is relevant, recommend the products mentioned.\n"
            "If the information doesn't answer the question, say you don't know."
        )

        response = llm.create_completion(prompt)
        return response

    else:
        # Fallback to old intent-based logic if vector_store is not provided (legacy support)
        # For new flow, we prefer vector store, but keeping this prevents breakage if store fails init
        return "Vector Store not initialized. Cannot perform semantic search."
