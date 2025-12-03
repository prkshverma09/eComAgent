import unittest
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from pim_rag import PIMRAG
from pim_utils import process_pim_query, LLM
from vector_store import PIMVectorStore
from hyperon import MeTTa
from pim_knowledge import initialize_pim_knowledge_graph
import json

# Load environment variables (expecting .env file at project root)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class TestPIMAgentLive(unittest.TestCase):
    def setUp(self):
        # Check for API Key
        self.api_key = os.getenv("ASI_ONE_API_KEY")
        if not self.api_key or self.api_key == "your_actual_api_key_here":
            self.skipTest("ASI_ONE_API_KEY not found or invalid in .env")

        # Setup real components
        self.metta = MeTTa()
        self.data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'Example_PIM_Data.json')
        initialize_pim_knowledge_graph(self.metta, self.data_path)
        self.rag = PIMRAG(self.metta)
        self.llm = LLM(api_key=self.api_key)
        
        # Setup Vector Store
        self.vector_store = PIMVectorStore(db_path="./test_chroma_db_live")
        with open(self.data_path, 'r') as f:
            data = json.load(f)
            self.vector_store.ingest_pim_data(data)

    def _ask_and_print(self, query):
        print(f"\nQ: {query}")
        response = process_pim_query(query, self.rag, self.llm, vector_store=self.vector_store)
        print(f"A: {response}\n")
        return response.lower()

    # --- Baseline Structural Tests ---
    def test_live_family_query(self):
        response = self._ask_and_print("What family does product fc24e6c3-933c-4a93-8a81-e5c703d134d5 belong to?")
        self.assertTrue("clothing" in response, f"Expected 'clothing' in response, got: {response}")

    def test_live_category_query(self):
        response = self._ask_and_print("Which category is product fc24e6c3-933c-4a93-8a81-e5c703d134d5 in?")
        self.assertTrue("tshirts" in response, f"Expected 'tshirts' in response, got: {response}")

    def test_live_attribute_query(self):
        response = self._ask_and_print("What is the color of product fc24e6c3-933c-4a93-8a81-e5c703d134d5?")
        self.assertTrue("brown" in response, f"Expected 'brown' in response, got: {response}")

    # --- Semantic / Vector DB Tests ---
    def test_semantic_season_query(self):
        # "Summer" is in the collection data, "Hot weather" is the semantic query.
        response = self._ask_and_print("Do you have anything suitable for hot weather?")
        # Expecting it to find the 'summer_2017' collection item
        self.assertTrue("jack" in response or "t-shirt" in response or "tshirt" in response, 
                        f"Expected product recommendation for hot weather, got: {response}")

    def test_semantic_weight_query(self):
        # User asks vaguely about "heavy" or specific weight without mentioning exact attribute name
        response = self._ask_and_print("I am looking for something that weighs around 800g.")
        self.assertTrue("800" in response or "gram" in response, 
                        f"Expected weight confirmation (800g), got: {response}")

    def test_semantic_vague_category(self):
        # "Casual tops" -> should map to "tshirts" via vector similarity
        response = self._ask_and_print("Show me some casual tops.")
        self.assertTrue("tshirts" in response or "t-shirt" in response, 
                        f"Expected 'tshirts' recommendation for 'casual tops', got: {response}")

if __name__ == '__main__':
    unittest.main()
