from hyperon import MeTTa, S, ValueAtom

class PIMRAG:
    def __init__(self, metta_instance: MeTTa):
        self.metta = metta_instance

    def get_product_family(self, uuid: str):
        """
        Get the family of a product.
        Query: (is_a <uuid> $family)
        """
        query_str = f'!(match &self (is_a {uuid} $family) $family)'
        results = self.metta.run(query_str)
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
        query_str = f'!(match &self (has_attribute {uuid} {attribute_name} $val) $val)'
        results = self.metta.run(query_str)
        values = []
        if results:
            for result in results:
                for atom in result:
                    try:
                        val = atom.get_object().value
                        values.append(val)
                    except AttributeError:
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
        """
        query_str = f'!(match &self (has_attribute $uuid {attribute_name} $val) ($uuid $val))'
        results = self.metta.run(query_str)
        matched_uuids = []

        if results:
            for result in results:
                if len(result) == 2:
                    uuid_atom = result[0]
                    val_atom = result[1]
                    try:
                        val_obj = val_atom.get_object().value
                        if str(val_obj) == str(value):
                            matched_uuids.append(str(uuid_atom))
                    except AttributeError:
                         if str(val_atom) == str(value):
                            matched_uuids.append(str(uuid_atom))

        return list(set(matched_uuids))

    def get_full_product_context(self, uuid: str):
        """
        Retrieve all known structured facts about a product from MeTTa.
        Returns a formatted string suitable for LLM context.
        """
        # Get Family
        families = self.get_product_family(uuid)

        # Get Categories
        categories = self.get_product_categories(uuid)

        # Get All Attributes
        # Query: (has_attribute <uuid> $attr $val)
        # We need to iterate over results properly.
        # Metta match returns a list of results, where each result is a tuple of matched atoms.
        query_str = f'!(match &self (has_attribute {uuid} $attr $val) ($attr $val))'
        results = self.metta.run(query_str)

        attributes = {}
        # results structure: [[(col, val), (col2, val2)], ...] or something similar depending on run()
        # MeTTa.run() returns a list of lists of Atoms.
        # Since our query returns a tuple ($attr $val), each 'result' in 'results'
        # is a list containing ONE ExpressionAtom which is the tuple.
        # Example: [ [ (attr val) ], [ (attr2 val2) ] ]

        if results:
            for result_list in results:
                for atom in result_list:
                    # atom is likely an ExpressionAtom: (attr val)
                    children = atom.get_children()
                    if len(children) == 2:
                        attr_name_atom = children[0]
                        val_atom = children[1]

                        attr_name = str(attr_name_atom)
                        try:
                            val = val_atom.get_object().value
                        except AttributeError:
                            val = str(val_atom)

                        if attr_name in attributes:
                            if isinstance(attributes[attr_name], list):
                                attributes[attr_name].append(val)
                            else:
                                attributes[attr_name] = [attributes[attr_name], val]
                        else:
                            attributes[attr_name] = val

        # Format Context
        context_parts = [f"Product UUID: {uuid}"]
        if families:
            context_parts.append(f"Family: {', '.join(families)}")
        if categories:
            context_parts.append(f"Categories: {', '.join(categories)}")

        if attributes:
            attr_strs = []
            for k, v in attributes.items():
                attr_strs.append(f"{k}: {v}")
            context_parts.append("Attributes: " + "; ".join(attr_strs))

        return "\n".join(context_parts)
