import json
from hyperon import MeTTa, E, S, ValueAtom

def initialize_pim_knowledge_graph(metta: MeTTa, file_path: str):
    """
    Initialize the MeTTa knowledge graph with PIM data from a JSON file.

    Args:
        metta (MeTTa): The MeTTa instance to populate.
        file_path (str): Path to the PIM JSON data file.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {file_path}")
        return

    # Extract UUID (Central Node)
    product_uuid = data.get("uuid")
    if not product_uuid:
        return

    # Family -> (is_a <uuid> <family>)
    family = data.get("family")
    if family:
        metta.space().add_atom(E(S("is_a"), S(product_uuid), S(family)))

    # Categories -> (has_category <uuid> <category>)
    categories = data.get("categories", [])
    for category in categories:
        metta.space().add_atom(E(S("has_category"), S(product_uuid), S(category)))

    # Values -> (has_attribute <uuid> <attribute_name> <value>)
    values = data.get("values", {})
    for attribute_name, entries in values.items():
        if not isinstance(entries, list):
            continue

        for entry in entries:
            val_data = entry.get("data")
            if val_data is None:
                continue

            # Determine Atom type based on value nature
            # For complex structures (dicts, lists) or non-string primitives, use ValueAtom
            # For simple strings that might be used as identifiers, we could use S, but
            # to be consistent with the plan's flexibility, we'll use ValueAtom for specific data values.
            # However, for simple categorical attributes like 'color' or 'size', Symbols might be better for reasoning.
            # Given the plan says "Use S(<value>) or ValueAtom(<value>)", I will use ValueAtom for consistency
            # with the 'values' semantics of PIM data, unless it's a very simple string.

            # Implementation decision: Use ValueAtom for all attribute values to handle types correctly.
            val_atom = ValueAtom(val_data)

            metta.space().add_atom(E(S("has_attribute"), S(product_uuid), S(attribute_name), val_atom))

