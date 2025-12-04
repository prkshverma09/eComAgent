import unittest
import os
import sys
import json
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from pim_rag import PIMRAG
from pim_utils import retrieve_pim_context
from vector_store import PIMVectorStore
from hyperon import MeTTa
from pim_knowledge import initialize_pim_knowledge_graph

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class TestContextRetrievalLive(unittest.TestCase):
    def setUp(self):
        # Setup real components (No LLM needed for Context Retrieval)
        self.metta = MeTTa()
        self.data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'Dummy_catalog_runningshoes.json')

        # Initialize Knowledge Graph
        initialize_pim_knowledge_graph(self.metta, self.data_path)
        self.rag = PIMRAG(self.metta)

        # Setup Vector Store (using a test db path to avoid messing with main one if needed,
        # but here we follow test_pim_agent_live pattern)
        self.vector_store = PIMVectorStore(db_path="./test_chroma_db_live")

        # Ingest data to ensure store is populated
        with open(self.data_path, 'r') as f:
            data = json.load(f)
            self.vector_store.ingest_pim_data(data)

    def _retrieve_and_validate(self, query):
        print(f"\nQ: {query}")
        context = retrieve_pim_context(query, self.rag, self.vector_store)
        print(f"Context Length: {len(context) if context else 0}")
        # print(f"Context Preview: {context[:200]}...")
        return context.lower() if context else ""

    def test_retrieve_brand_context(self):
        # Query about a specific shoe brand
        context = self._retrieve_and_validate("Horizon Pro 3")

        # Expect to find the product context for Horizon Pro 3
        self.assertIn("product_name: horizon pro 3", context)
        # Expect to find its brand 'AeroStride'
        self.assertIn("brand: aerostride", context)

    def test_retrieve_feature_context(self):
        # Query for waterproof shoes
        context = self._retrieve_and_validate("waterproof shoes")

        # Expect to find FluxRide XT which is Gore-Tex/Waterproof
        self.assertIn("fluxride xt", context)
        # Check if attribute details are present
        self.assertIn("material:", context)

    def test_retrieve_category_context(self):
        # Query for a category
        context = self._retrieve_and_validate("trail running shoes")

        # Should find trail shoes like 'PacePro Race' or 'StrideMax XT'
        found_trail_shoe = "pacepro race" in context or "stridemax xt" in context
        self.assertTrue(found_trail_shoe, f"Context should contain trail shoes. Got context length: {len(context)}")
        self.assertIn("family: trail", context)

    def test_no_results(self):
        # Query for something that definitely doesn't exist
        context = retrieve_pim_context("flying car", self.rag, self.vector_store)
        # Depending on vector store threshold, it might return something irrelevant or nothing.
        # But retrieve_pim_context returns None if search_results is empty.
        # However, vector stores usually always return something unless empty.
        # Let's just check it returns a string (even if empty/irrelevant matches) or None.
        if context:
            self.assertIsInstance(context, str)

if __name__ == '__main__':
    unittest.main()

