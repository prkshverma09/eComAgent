import unittest
from unittest.mock import MagicMock, patch
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from pim_rag import PIMRAG
from pim_utils import process_pim_query, LLM
from hyperon import MeTTa
from pim_knowledge import initialize_pim_knowledge_graph

from vector_store import PIMVectorStore

class TestPIMAgentLogic(unittest.TestCase):
    def setUp(self):
        # Setup real RAG with real data
        self.metta = MeTTa()
        self.data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'Example_PIM_Data.json')
        initialize_pim_knowledge_graph(self.metta, self.data_path)
        self.rag = PIMRAG(self.metta)

        # Mock LLM to avoid API calls
        self.mock_llm = MagicMock(spec=LLM)
        # Mock the create_completion method
        self.mock_llm.create_completion.side_effect = self.llm_response_simulator

        # Mock Vector Store for Hybrid RAG
        self.mock_vector_store = MagicMock(spec=PIMVectorStore)
        # Setup mock search return value (uuid only needed)
        self.mock_vector_store.search.return_value = [
            {"uuid": "fc24e6c3-933c-4a93-8a81-e5c703d134d5", "document": "Mock Doc", "metadata": {}}
        ]

    def llm_response_simulator(self, prompt, max_tokens=200):
        # Simulate LLM responses based on prompt content
        # For Hybrid RAG, the prompt contains "User Question" and "Product Context"
        if "User Question" in prompt:
             return "Humanized response based on retrieved data."

        return "Unknown prompt type"

    def test_get_family_flow(self):
        query = "What family does product fc24e6c3-933c-4a93-8a81-e5c703d134d5 belong to?"

        # Call with mocked vector store
        response = process_pim_query(query, self.rag, self.mock_llm, vector_store=self.mock_vector_store)

        # We expect the mock to return the humanized string
        self.assertEqual(response, "Humanized response based on retrieved data.")

        # Verify Vector Store was searched
        self.assertTrue(self.mock_vector_store.search.called)

        # Manually check RAG retrieval part to ensure logic underneath works
        family = self.rag.get_product_family("fc24e6c3-933c-4a93-8a81-e5c703d134d5")
        self.assertIn("clothing", family)

    def test_get_attribute_flow(self):
        query = "What is the color of product fc24e6c3-933c-4a93-8a81-e5c703d134d5?"
        process_pim_query(query, self.rag, self.mock_llm, vector_store=self.mock_vector_store)

        # Verify underlying RAG fetch
        color = self.rag.get_product_attribute("fc24e6c3-933c-4a93-8a81-e5c703d134d5", "color")
        self.assertIn("brown", str(color))

    def test_find_by_category_flow(self):
        query = "Show me products in tshirts category"
        process_pim_query(query, self.rag, self.mock_llm, vector_store=self.mock_vector_store)

        products = self.rag.find_products_by_category("tshirts")
        self.assertIn("fc24e6c3-933c-4a93-8a81-e5c703d134d5", products)

if __name__ == '__main__':
    unittest.main()

