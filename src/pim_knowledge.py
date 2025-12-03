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

    # Handle list of products (backfill support)
    products = data if isinstance(data, list) else [data]

    for product in products:
        # Schema adaptation: Check if using old UUID-based schema or new Brand/Product Name schema
        # Generate a synthetic UUID if missing but Product Name exists (for reproducibility)
        product_uuid = product.get("uuid")
        if not product_uuid and "Product Name" in product:
            import hashlib
            # Create a deterministic UUID from Brand + Product Name
            unique_str = f"{product.get('Brand', '')}_{product.get('Product Name', '')}"
            product_uuid = hashlib.md5(unique_str.encode()).hexdigest()
            # Store it back in product dict so we can use it later if needed (though local scope)
        
        if not product_uuid:
            continue

        # Family -> (is_a <uuid> <family>)
        # Map "Type" to Family if "family" key is missing
        family = product.get("family") or product.get("Type")
        if family:
            metta.space().add_atom(E(S("is_a"), S(product_uuid), S(str(family))))

        # Categories -> (has_category <uuid> <category>)
        # Map "Type", "Gender", "Season" to categories if explicit "categories" list missing
        categories = product.get("categories", [])
        if not categories:
            if product.get("Type"): categories.append(product.get("Type"))
            if product.get("Gender"): categories.append(product.get("Gender"))
            if product.get("Season"): categories.append(product.get("Season"))
            
        for category in categories:
            metta.space().add_atom(E(S("has_category"), S(product_uuid), S(str(category))))

        # Values -> (has_attribute <uuid> <attribute_name> <value>)
        # Old Schema: values dict with list of entries
        # New Schema: flat keys like "Brand", "Price", "Material"
        
        values_dict = product.get("values", {})
        if values_dict:
            # Old Schema Handler
            for attribute_name, entries in values_dict.items():
                if not isinstance(entries, list):
                    continue
                for entry in entries:
                    val_data = entry.get("data")
                    if val_data is None:
                        continue
                    val_atom = ValueAtom(val_data)
                    metta.space().add_atom(E(S("has_attribute"), S(product_uuid), S(attribute_name), val_atom))
        else:
            # New Schema Handler (Flat keys)
            # Exclude keys we already processed or are structural
            exclude_keys = ["uuid", "family", "categories", "Type", "Gender", "Season", "values"]
            for key, val in product.items():
                if key not in exclude_keys and val is not None:
                    # Clean key for usage as symbol (remove spaces/special chars if needed, but S() handles strings)
                    # Ideally standardize keys to lowercase/snake_case
                    clean_key = key.lower().replace(" ", "_").replace("(", "").replace(")", "")
                    val_atom = ValueAtom(val)
                    metta.space().add_atom(E(S("has_attribute"), S(product_uuid), S(clean_key), val_atom))

