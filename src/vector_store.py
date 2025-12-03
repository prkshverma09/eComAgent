import chromadb
from sentence_transformers import SentenceTransformer
import os
import json

class PIMVectorStore:
    def __init__(self, db_path="./chroma_db"):
        # Initialize persistent client
        self.client = chromadb.PersistentClient(path=db_path)

        # Initialize collection
        # Using default distance (cosine)
        self.collection = self.client.get_or_create_collection(name="pim_products")

        # Initialize embedding model (local)
        # 'all-MiniLM-L6-v2' is fast and good quality for general purpose
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def _generate_description(self, product: dict) -> str:
        """
        Generate a natural language description of the product for embedding.
        Supports both old hierarchical schema and new flat schema.
        """
        # --- Common Identity ---
        uuid = product.get("uuid", "")
        # If no explicit UUID, try to identify by Name/Brand (New Schema)
        if not uuid:
            uuid = f"{product.get('Brand', 'Unknown')} {product.get('Product Name', 'Unknown')}"

        # --- Old Schema Extraction ---
        family = product.get("family", "")
        categories = list(product.get("categories", []))
        attributes = []
        
        values_dict = product.get("values", {})
        if values_dict:
            # Old Schema Logic
            for attr_name, entries in values_dict.items():
                if not isinstance(entries, list): continue
                for entry in entries:
                    val = entry.get("data")
                    if isinstance(val, dict): val_str = " ".join([str(v) for v in val.values()])
                    else: val_str = str(val)
                    attributes.append(f"{attr_name} is {val_str}")
        else:
            # --- New Schema Logic ---
            # Map specific keys to Family/Categories if not present
            if not family: family = product.get("Type", "Product")
            
            # Add structural tags to categories
            if product.get("Type"): categories.append(product.get("Type"))
            if product.get("Gender"): categories.append(product.get("Gender"))
            if product.get("Season"): categories.append(product.get("Season"))
            
            # Treat other keys as attributes
            exclude = ["uuid", "family", "categories", "Type", "Gender", "Season", "values"]
            for k, v in product.items():
                if k not in exclude and v is not None:
                    attributes.append(f"{k} is {v}")
                    # Explicitly add Description (Short) again if it exists to be safe, 
                    # but it is covered by the loop. 
                    # Note: keys like "Description (Short)" will be added as "Description (Short) is ...".

        # --- Construct Description ---
        cat_str = ", ".join([str(c) for c in categories if c])
        
        description = f"Product {uuid} is a {family} item. "
        if cat_str:
            description += f"It belongs to categories: {cat_str}. "
        if attributes:
            description += f"Attributes: {', '.join(attributes)}."
            
        return description

    def ingest_pim_data(self, json_data: dict):
        """
        Ingest PIM data into the vector store.
        """
        products = []
        if isinstance(json_data, dict):
            if "uuid" in json_data:
                products = [json_data]
            # Handle new schema list wrapped in dict if ever happens, but mostly list
        elif isinstance(json_data, list):
            products = json_data
            
        if not products:
            print("No products found to ingest.")
            return

        ids = []
        documents = []
        metadatas = []
        
        import hashlib
        
        for product in products:
            # Determine UUID (consistent with pim_knowledge.py)
            uuid = product.get("uuid")
            if not uuid and "Product Name" in product:
                unique_str = f"{product.get('Brand', '')}_{product.get('Product Name', '')}"
                uuid = hashlib.md5(unique_str.encode()).hexdigest()
            
            if not uuid:
                continue
                
            desc = self._generate_description(product)
            
            # Determine Family for metadata
            family = product.get("family") or product.get("Type", "Unknown")
            
            ids.append(uuid)
            documents.append(desc)
            metadatas.append({"family": str(family), "uuid": uuid})
            
        # Compute embeddings
        if documents:
            embeddings = self.model.encode(documents).tolist()
            
            # Upsert into ChromaDB
            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            # print(f"Ingested {len(documents)} products into Vector Store.") # Silencing log for cleaner output

    def search(self, query: str, k: int = 3):
        """
        Semantic search for products.
        Returns list of results.
        """
        query_embedding = self.model.encode([query]).tolist()

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=k
        )

        # Format results: list of dicts with uuid, distance, document
        formatted_results = []
        if results['ids']:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "uuid": results['ids'][0][i],
                    "document": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i]
                })

        return formatted_results

