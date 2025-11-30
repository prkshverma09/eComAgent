import unittest
import sys
import os

# Add src to path to import pim_knowledge
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from hyperon import MeTTa, SymbolAtom, ValueAtom
    from pim_knowledge import initialize_pim_knowledge_graph
except ImportError:
    print("Hyperon not installed, skipping tests")
    sys.exit(0)

class TestPIMKnowledgeGraph(unittest.TestCase):
    def setUp(self):
        self.metta = MeTTa()
        self.test_data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'Example_PIM_Data.json')

    def test_knowledge_graph_initialization(self):
        initialize_pim_knowledge_graph(self.metta, self.test_data_path)

        # Verify Product Existence (UUID)
        product_uuid = "fc24e6c3-933c-4a93-8a81-e5c703d134d5"

        # Check Family Relation
        # Query pattern: (is_a product_uuid $x)
        # The atoms in space are symbols, e.g., (is_a fc24e6c3... clothing)
        # But in the match query `(is_a "{product_uuid}" $x)`, the quotes make it a string literal?
        # Actually, S("string") creates a symbol. In the space printout we see `fc24e6c3...` without quotes.
        # This means it is a Symbol, not a String Value.
        # However, in the query `(is_a "{product_uuid}" $x)`, the quotes might be interpreting it as a String Value or a Symbol with quotes?
        # If we look at `example/metta/knowledge.py`: S("symptom"), S("fever")... these are symbols.
        # In our code: S(product_uuid). product_uuid is a string "fc24...". So it becomes a symbol `fc24...`.
        # When querying via `metta.run`, if we use double quotes `"{product_uuid}"`, the parser might see it as a String Value if supported or a Symbol with quotes?
        # Let's try matching with the symbol directly.

        # Debug: Print all atoms in space to see what was added
        # print("Atoms in space:")
        # print(self.metta.space().get_atoms())

        # We need to construct the query such that `product_uuid` is treated as a symbol.
        # In MeTTa script, `(is_a fc24... $x)` would work.
        # So we should insert the uuid string WITHOUT quotes into the query string.

        results = self.metta.run(f'!(match &self (is_a {product_uuid} $x) $x)')
        found_family = False
        for result in results:
             for atom in result:
                 if str(atom) == '"clothing"' or str(atom) == 'clothing':
                     found_family = True
                     break
        self.assertTrue(found_family, f"Family relation not found. Results: {results}")

        # Check Category Relation
        results = self.metta.run(f'!(match &self (has_category {product_uuid} $x) $x)')
        found_category = False
        for result in results:
            for atom in result:
                if str(atom) == 'tshirts':
                    found_category = True
                    break
        self.assertTrue(found_category, f"Category relation not found. Results: {results}")

        # Check Attribute: Color
        results = self.metta.run(f'!(match &self (has_attribute {product_uuid} color $x) $x)')
        found_color = False
        for result in results:
            for atom in result:
                if "brown" in str(atom):
                    found_color = True
                    break
        self.assertTrue(found_color, f"Color attribute not found. Results: {results}")

if __name__ == '__main__':
    unittest.main()
