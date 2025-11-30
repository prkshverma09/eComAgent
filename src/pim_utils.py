import json
from openai import OpenAI
from pim_rag import PIMRAG

class LLM:
    def __init__(self, api_key):
        # Using ASI:One endpoint as per example/metta/utils.py
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.asi1.ai/v1"
        )

    def create_completion(self, prompt, max_tokens=200):
        completion = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="asi1-mini",
            max_tokens=max_tokens
        )
        return completion.choices[0].message.content

def get_pim_intent(query: str, llm: LLM):
    """
    Classify the intent of the user query regarding PIM data.
    Intents:
    - get_family: Asking about product family.
    - get_category: Asking about categories.
    - get_attribute: Asking for a specific attribute (price, color, size, etc.).
    - find_by_category: Looking for products in a category.
    - unknown: Cannot determine.

    Returns: intent (str), extracted_entities (dict)
    """
    prompt = (
        f"Query: '{query}'\n"
        "Analyze this query about e-commerce product data.\n"
        "Classify the intent as one of: 'get_family', 'get_category', 'get_attribute', 'find_by_category', or 'unknown'.\n"
        "Extract relevant entities: 'uuid' (product ID), 'attribute_name' (e.g., color, weight), 'category_name'.\n"
        "Return *only* the result in JSON format like this:\n"
        "{\n"
        "  \"intent\": \"<intent>\",\n"
        "  \"entities\": {\n"
        "    \"uuid\": \"<uuid_if_present>\",\n"
        "    \"attribute_name\": \"<attribute_if_present>\",\n"
        "    \"category_name\": \"<category_if_present>\"\n"
        "  }\n"
        "}"
    )

    response = llm.create_completion(prompt)
    try:
        result = json.loads(response)
        return result.get("intent", "unknown"), result.get("entities", {})
    except json.JSONDecodeError:
        print(f"Error parsing LLM response: {response}")
        return "unknown", {}

def process_pim_query(query: str, rag: PIMRAG, llm: LLM):
    """
    Process the user query using the RAG system and LLM.
    """
    intent, entities = get_pim_intent(query, llm)
    print(f"DEBUG: Intent={intent}, Entities={entities}")

    rag_response = None
    context_str = ""

    uuid = entities.get("uuid")
    attribute = entities.get("attribute_name")
    category = entities.get("category_name")

    # Execute RAG based on intent
    if intent == "get_family" and uuid:
        families = rag.get_product_family(uuid)
        rag_response = f"Product {uuid} belongs to family: {', '.join(families)}" if families else "No family information found."

    elif intent == "get_category" and uuid:
        cats = rag.get_product_categories(uuid)
        rag_response = f"Product {uuid} is in categories: {', '.join(cats)}" if cats else "No category information found."

    elif intent == "get_attribute" and uuid and attribute:
        vals = rag.get_product_attribute(uuid, attribute)
        rag_response = f"Product {uuid} has {attribute}: {vals}" if vals else f"No value found for attribute {attribute}."

    elif intent == "find_by_category" and category:
        uuids = rag.find_products_by_category(category)
        rag_response = f"Products in category '{category}': {', '.join(uuids)}" if uuids else f"No products found in category {category}."

    else:
        rag_response = "I couldn't identify the specific product information you are looking for. Please check the Product UUID or specify the attribute."

    # Humanize the response
    prompt = (
        f"User Query: '{query}'\n"
        f"Data Retrieved: '{rag_response}'\n"
        "You are a helpful e-commerce assistant. Synthesize the above data into a natural, friendly response for the user.\n"
        "If the data is missing or error, politely inform the user."
    )

    final_response = llm.create_completion(prompt)
    return final_response

