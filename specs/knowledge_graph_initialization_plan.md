<!-- 9cd2fe75-e70b-4b20-9da3-10ded592c559 aaef7fdb-35ac-40d2-8d88-a5705903faad -->
# Plan: Implement PIM Knowledge Graph Mapping

I will create a Python module `src/pim_knowledge.py` that parses the PIM data structure and initializes a MeTTa knowledge graph, following the patterns in `example/metta/knowledge.py`.

## 1. dependencies

- Add `hyperon` to `requirements.txt` to support the MeTTa integration.

## 2. src/pim_knowledge.py

- Create a function `initialize_pim_knowledge_graph(metta: MeTTa, file_path: str)`.
- **Logic**:
    - Load the JSON data from the given file path.
    - Extract the product `uuid` to serve as the central node for the product entity.
    - **Mapping Strategy**:
        - **Family**: `(is_a <uuid> <family>)`
        - **Categories**: `(has_category <uuid> <category>)` for each category.
        - **Attributes (from `values` dict)**: Iterate through attributes (e.g., color, size).
            - Use a generic predicate pattern: `(has_attribute <uuid> <attribute_name> <value>)`.
            - For simple values (strings/numbers), use `S(<value>)` or `ValueAtom(<value>)` depending on type.
            - For complex values (e.g., `weight` with unit/amount), store the dictionary as a `ValueAtom` or flatten it if appropriate (will use `ValueAtom` for structured data to preserve context).
            - Handle the list structure of values (iterating over the list `data` field).

## 3. Usage

- The function can be imported and used in `src/main.py` or other scripts to load PIM context into a MeTTa space.

### To-dos

- [ ] Add `hyperon` to `requirements.txt`
- [ ] Create `src/pim_knowledge.py` with `initialize_pim_knowledge_graph` function