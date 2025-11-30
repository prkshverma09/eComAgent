from hyperon import MeTTa, S, ValueAtom

class PIMRAG:
    def __init__(self, metta_instance: MeTTa):
        self.metta = metta_instance

    def get_product_family(self, uuid: str):
        """
        Get the family of a product.
        Query: (is_a <uuid> $family)
        """
        # uuid is passed as a string, but in the graph it acts as a symbol.
        # We need to ensure we don't wrap it in quotes if it's stored as a symbol.
        # Based on pim_knowledge.py: S(product_uuid) -> stored as Symbol.

        query_str = f'!(match &self (is_a {uuid} $family) $family)'
        results = self.metta.run(query_str)
        # Results are a list of lists of atoms.
        # Extract the family name (Symbol or String).
        families = []
        if results:
            for result in results:
                for atom in result:
                    families.append(str(atom))
        return families

    def get_product_categories(self, uuid: str):
        """
        Get categories for a product.
        Query: (has_category <uuid> $cat)
        """
        query_str = f'!(match &self (has_category {uuid} $cat) $cat)'
        results = self.metta.run(query_str)
        categories = []
        if results:
            for result in results:
                for atom in result:
                    categories.append(str(atom))
        return list(set(categories))

    def get_product_attribute(self, uuid: str, attribute_name: str):
        """
        Get value of a specific attribute.
        Query: (has_attribute <uuid> <attribute_name> $val)
        """
        # attribute_name is a string in python, but a symbol in the graph S(attribute_name).
        query_str = f'!(match &self (has_attribute {uuid} {attribute_name} $val) $val)'
        results = self.metta.run(query_str)
        values = []
        if results:
            for result in results:
                for atom in result:
                    # The value is a ValueAtom, so we get the underlying object
                    try:
                        val = atom.get_object().value
                        values.append(val)
                    except AttributeError:
                        # Fallback if it's a Symbol or other atom type
                        values.append(str(atom))
        return values

    def find_products_by_category(self, category: str):
        """
        Find all product UUIDs in a given category.
        Query: (has_category $uuid <category>)
        """
        query_str = f'!(match &self (has_category $uuid {category}) $uuid)'
        results = self.metta.run(query_str)
        uuids = []
        if results:
            for result in results:
                for atom in result:
                    uuids.append(str(atom))
        return list(set(uuids))

    def find_products_by_attribute(self, attribute_name: str, value):
        """
        Find products that have a specific attribute value.
        Query: (has_attribute $uuid <attribute_name> <value>)
        Note: Matching exact ValueAtoms in queries might be tricky depending on type.
        For now, this assumes simple string match or we might need to iterate if strict matching fails.
        """
        # This is complex because 'value' needs to be represented exactly as it is in the atom.
        # For simplicity in this iteration, we might stick to category/family lookups
        # or implement a filter in python if the graph query is too rigid for complex ValueAtoms.

        # Let's try a broad query and filter in Python for safety
        query_str = f'!(match &self (has_attribute $uuid {attribute_name} $val) ($uuid $val))'
        results = self.metta.run(query_str)
        matched_uuids = []

        if results:
            for result in results:
                if len(result) == 2: # ($uuid $val)
                    uuid_atom = result[0]
                    val_atom = result[1]
                    try:
                        val_obj = val_atom.get_object().value
                        # loose comparison (e.g. string vs int handling)
                        if str(val_obj) == str(value):
                            matched_uuids.append(str(uuid_atom))
                    except AttributeError:
                         if str(val_atom) == str(value):
                            matched_uuids.append(str(uuid_atom))

        return list(set(matched_uuids))

