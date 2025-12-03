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

    def test_live_family_query(self):
        query = "What family does product fc24e6c3-933c-4a93-8a81-e5c703d134d5 belong to?"
        print(f"\n[Live Test] Sending query: '{query}'")

        response = process_pim_query(query, self.rag, self.llm, vector_store=self.vector_store)
        print(f"[Live Test] Response: {response}")

        # Verify the response contains relevant info
        # We expect "clothing" to be mentioned in the humanized response
        self.assertTrue("clothing" in response.lower(), f"Expected 'clothing' in response, got: {response}")

    def test_live_category_query(self):
        query = "Which category is product fc24e6c3-933c-4a93-8a81-e5c703d134d5 in?"
        print(f"\n[Live Test] Sending query: '{query}'")

        response = process_pim_query(query, self.rag, self.llm, vector_store=self.vector_store)
        print(f"[Live Test] Response: {response}")

        self.assertTrue("tshirts" in response.lower(), f"Expected 'tshirts' in response, got: {response}")

    def test_live_attribute_query(self):
        query = "What is the color of product fc24e6c3-933c-4a93-8a81-e5c703d134d5?"
        print(f"\n[Live Test] Sending query: '{query}'")

        response = process_pim_query(query, self.rag, self.llm, vector_store=self.vector_store)
        print(f"[Live Test] Response: {response}")

        self.assertTrue("brown" in response.lower(), f"Expected 'brown' in response, got: {response}")

if __name__ == '__main__':
    unittest.main()

