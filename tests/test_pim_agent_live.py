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
        # Updated to use the new running shoes catalog
        self.data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'Dummy_catalog_runningshoes.json')
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

    # --- Updated Tests for Running Shoes Catalog ---

    def test_live_brand_query(self):
        # "Brand" is a key attribute in the new schema
        response = self._ask_and_print("What brand is the 'Horizon Pro 3'?")
        self.assertTrue("aerostride" in response, f"Expected 'AeroStride' in response, got: {response}")

    def test_live_attribute_query(self):
        # Check for specific attribute like 'Material'
        response = self._ask_and_print("What material is the 'Tempest Race' made of?")
        self.assertTrue("atomknit" in response or "zoomx" in response, f"Expected material details, got: {response}")

    def test_semantic_usage_query(self):
        # "Marathon" should map to "Tempest Race" or "Velocity Sprint" which have "Marathon" in description
        # Also accepting "Ignite Elite" and "PacePro Race" as valid semantic matches for long distance/marathon
        response = self._ask_and_print("I need a shoe good for running a marathon.")
        self.assertTrue("tempest race" in response or "velocity sprint" in response or "ignite elite" in response or "pacepro race" in response,
                        f"Expected marathon shoe recommendation, got: {response}")

    def test_semantic_feature_query(self):
        # "Waterproof" maps to "FluxRide XT" (Gore-Tex)
        # Debug: Check if FluxRide XT is even retrieved
        # The prompt might fail if retrieval misses.
        query = "Do you have any waterproof shoes?"
        response = self._ask_and_print(query)

        # If vector search fails, we might need to debug embeddings or k value
        # But let's assert strictly for now
        self.assertTrue("fluxride xt" in response, f"Expected FluxRide XT recommendation, got: {response}")

if __name__ == '__main__':
    unittest.main()
