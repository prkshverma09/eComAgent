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
        """
        # Extract fields
        uuid = product.get("uuid", "")
        family = product.get("family", "")
        categories = ", ".join(product.get("categories", []))

        # Flatten values
        values_dict = product.get("values", {})
        attributes = []

        for attr_name, entries in values_dict.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                val = entry.get("data")
                # Handle dictionary values (e.g. weight with unit)
                if isinstance(val, dict):
                     val_str = " ".join([str(v) for v in val.values()])
                else:
                    val_str = str(val)
                attributes.append(f"{attr_name} is {val_str}")

        description = f"Product {uuid} is a {family} item. "
        if categories:
            description += f"It belongs to categories: {categories}. "
        if attributes:
            description += f"Attributes: {', '.join(attributes)}."

        return description

    def ingest_pim_data(self, json_data: dict):
        """
        Ingest PIM data into the vector store.
        """
        # If input is the root dict, it might be a single product or we might need to handle list.
        # Example_PIM_Data.json seems to contain a single product object based on previous reads.
        # But usually PIM data is a list. We will handle single dict or list of dicts.

        products = []
        if isinstance(json_data, dict):
            # Check if it's a single product (has uuid) or a wrapper
            if "uuid" in json_data:
                products = [json_data]
            else:
                # If it's a wrapper, maybe "products" key?
                # For now assume single product as per example file content.
                pass
        elif isinstance(json_data, list):
            products = json_data

        if not products:
            print("No products found to ingest.")
            return

        ids = []
        documents = []
        metadatas = []

        for product in products:
            uuid = product.get("uuid")
            if not uuid:
                continue

            desc = self._generate_description(product)

            ids.append(uuid)
            documents.append(desc)
            metadatas.append({"family": product.get("family", ""), "uuid": uuid})

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

