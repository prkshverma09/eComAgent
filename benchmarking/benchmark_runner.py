#!/usr/bin/env python3
"""
Benchmark Runner: Compares AgentFabric Hybrid RAG (MeTTa + Vector) vs Keyword Search

Features:
- Full Hybrid RAG with MeTTa knowledge graph + ChromaDB vector store
- Dual evaluation: Retrieval Quality + Response Quality
- Fair comparison: Both systems use the same LLM for response generation
- Excel file support for custom queries
- Category-specific and sample testing

Usage:
    python benchmark_runner.py --full --evaluate           # Full benchmark with evaluation
    python benchmark_runner.py --sample 10 --evaluate      # Quick test with 10 queries
    python benchmark_runner.py --category attribute_based  # Specific category
    python benchmark_runner.py --query "trail shoes"       # Single query test
    python benchmark_runner.py --question_file questions.xlsx --evaluate  # Custom queries
"""

import argparse
import json
import time
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

from dotenv import load_dotenv
from openai import OpenAI

# Try to import selenium for website testing (optional dependency)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: Selenium not installed. Website search testing will be skipped.")
    print("Install with: pip install selenium webdriver-manager")

# Try to import pandas for Excel support
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


# =============================================================================
# LLM EVALUATOR - Dual Evaluation (Retrieval + Response Quality)
# =============================================================================

class LLMEvaluator:
    """Evaluates retrieval and response quality using LLM-as-judge"""

    RETRIEVAL_EVAL_PROMPT = """You are an expert evaluator for an e-commerce product search system.
Evaluate the RETRIEVAL QUALITY - how relevant are the retrieved products to the user's query?

## User Query
{query}

## Retrieved Products
{products}

## Scoring Criteria (1-5 scale)

1. **RELEVANCE**: How relevant are these products to what the user asked for? (5=perfectly relevant, 1=completely irrelevant)
2. **COVERAGE**: Do the results cover the user's needs? (5=comprehensive, 1=missing key products)
3. **PRECISION**: Are ALL returned products relevant, or are there irrelevant ones? (5=all relevant, 1=mostly irrelevant)

IMPORTANT: If NO products were retrieved, or very few products (0-1), score LOW on all metrics.
A system that fails to find products is NOT performing well, even if it avoids errors.

Respond ONLY with JSON:
{{"relevance": <1-5>, "coverage": <1-5>, "precision": <1-5>, "reasoning": "<brief explanation>"}}
"""

    RESPONSE_EVAL_PROMPT = """You are an expert evaluator for an e-commerce product search system.
Evaluate the RESPONSE QUALITY - how good is the assistant's answer?

## User Query
{query}

## System Response
{response}

## Products Used as Context
{products}

## Scoring Criteria (1-5 scale)

1. **ACCURACY**: Does the response accurately reflect the product data? (5=completely accurate, 1=inaccurate)
2. **HALLUCINATION** (5=none, 1=severe): Does it invent facts NOT in the product data?
3. **HELPFULNESS**: How useful is this response for a real shopper? (5=very helpful, 1=not helpful)
4. **COMPLETENESS**: Does it fully answer the user's question? (5=complete, 1=incomplete)
5. **USEFULNESS**: Does the response provide actionable product recommendations? (5=specific products with details, 1=no recommendations)

IMPORTANT SCORING RULES:
- If the response says "I don't know", "I can't help", "I don't have access", or similar evasive answers:
  * Score ACCURACY as 2 (not technically wrong, but not helpful)
  * Score HALLUCINATION as 3 (avoiding the question is not the same as being truthful)
  * Score HELPFULNESS as 1 (completely unhelpful to a shopper)
  * Score COMPLETENESS as 1 (fails to answer the question)
  * Score USEFULNESS as 1 (no product recommendations)
- A response that TRIES to help with specific products should score higher than one that refuses to answer.
- We want systems that help customers find products, not systems that play it safe by saying nothing.

Respond ONLY with JSON:
{{"accuracy": <1-5>, "hallucination": <1-5>, "helpfulness": <1-5>, "completeness": <1-5>, "usefulness": <1-5>, "reasoning": "<brief explanation>"}}
"""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key, base_url="https://api.asi1.ai/v1")

    def _call_llm(self, prompt: str, max_tokens: int = 300) -> dict:
        """Make LLM call and parse JSON response"""
        try:
            completion = self.client.chat.completions.create(
                model="asi1-mini",
                messages=[
                    {"role": "system", "content": "You are an evaluator. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=max_tokens
            )
            result_text = completion.choices[0].message.content.strip()

            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                print(f"  ⚠ LLM response not valid JSON: {result_text[:100]}...", flush=True)
        except Exception as e:
            print(f"  ⚠ LLM evaluation error: {type(e).__name__}: {str(e)[:100]}", flush=True)
        return {}

    def _format_product(self, product: dict) -> str:
        """Extract product info, preferring 'context' over empty 'name'/'text' fields."""
        # First check if 'context' exists and has content (Hybrid RAG products)
        if product.get('context'):
            return product['context']
        # Then check for non-empty name
        if product.get('name') and product['name'].strip():
            result = product['name']
            if product.get('price'):
                result += f" - {product['price']}"
            if product.get('full_text') and product['full_text'] != product['name']:
                result += f" ({product['full_text'][:100]})"
            return result
        # Then check for non-empty text
        if product.get('text') and product['text'].strip():
            return product['text']
        # Fallback to string representation
        return str(product)[:200]

    def evaluate_retrieval(self, query: str, products: list) -> dict:
        """Evaluate retrieval quality - how relevant are the retrieved products?"""
        products_str = "\n\n".join([
            f"Product {i+1}:\n{self._format_product(p)}"
            for i, p in enumerate(products[:10])
        ]) if products else "No products found"

        prompt = self.RETRIEVAL_EVAL_PROMPT.format(
            query=query,
            products=products_str
        )

        scores = self._call_llm(prompt)
        return {
            "relevance": min(5, max(1, int(scores.get("relevance", 0)))) if scores.get("relevance") else 0,
            "coverage": min(5, max(1, int(scores.get("coverage", 0)))) if scores.get("coverage") else 0,
            "precision": min(5, max(1, int(scores.get("precision", 0)))) if scores.get("precision") else 0,
            "reasoning": scores.get("reasoning", "Evaluation failed")
        }

    def evaluate_response(self, query: str, response: str, products: list) -> dict:
        """Evaluate response quality - accuracy, hallucination, helpfulness"""
        products_str = "\n\n".join([
            f"Product {i+1}:\n{self._format_product(p)}"
            for i, p in enumerate(products[:5])
        ]) if products else "No products found"

        prompt = self.RESPONSE_EVAL_PROMPT.format(
            query=query,
            response=response[:500] if response else "No response",
            products=products_str
        )

        scores = self._call_llm(prompt)
        return {
            "accuracy": min(5, max(1, int(scores.get("accuracy", 0)))) if scores.get("accuracy") else 0,
            "hallucination": min(5, max(1, int(scores.get("hallucination", 0)))) if scores.get("hallucination") else 0,
            "helpfulness": min(5, max(1, int(scores.get("helpfulness", 0)))) if scores.get("helpfulness") else 0,
            "completeness": min(5, max(1, int(scores.get("completeness", 0)))) if scores.get("completeness") else 0,
            "usefulness": min(5, max(1, int(scores.get("usefulness", 0)))) if scores.get("usefulness") else 0,
            "reasoning": scores.get("reasoning", "Evaluation failed")
        }

    def generate_response(self, query: str, products: list) -> str:
        """Generate an LLM response from retrieved products (for fair comparison)"""
        if not products:
            return "No products found matching your query."

        context = "\n\n".join([
            f"{p.get('name', '')} - {p.get('price', '')}\n{p.get('full_text', p.get('text', ''))[:200]}"
            for p in products[:5]
        ])

        prompt = f"""Based on these products:

{context}

Answer this shopping query: {query}

Provide a helpful, concise response recommending relevant products."""

        try:
            completion = self.client.chat.completions.create(
                model="asi1-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            return completion.choices[0].message.content
        except:
            return f"Found {len(products)} matching products."


# =============================================================================
# AGENTFABRIC TESTER - Hybrid RAG (MeTTa + Vector)
# =============================================================================

class AgentFabricTester:
    """Tests AgentFabric semantic search using Hybrid RAG (MeTTa + Vector)"""

    def __init__(self):
        self.rag_initialized = False
        self.pim_rag = None
        self.vector_store = None
        self.llm = None
        self.api_key = None

    def _init_rag(self):
        """Initialize RAG components directly"""
        if self.rag_initialized:
            return True

        try:
            # Add src to path
            src_path = Path(__file__).parent.parent / "src"
            if str(src_path) not in sys.path:
                sys.path.insert(0, str(src_path))

            from hyperon import MeTTa
            from pim_rag import PIMRAG
            from pim_knowledge import initialize_pim_knowledge_graph
            from vector_store import PIMVectorStore
            from pim_utils import LLM

            # Load environment variables
            env_path = Path(__file__).parent.parent / ".env"
            load_dotenv(env_path)
            self.api_key = os.getenv("ASI_ONE_API_KEY")

            if not self.api_key:
                raise ValueError("ASI_ONE_API_KEY not found in .env file")

            # Load product data
            data_path = Path(__file__).parent.parent / "data" / "updated_running_shoes_full_catalog.json"
            if not data_path.exists():
                data_path = Path(__file__).parent.parent / "data" / "Dummy_catalog_runningshoes.json"

            print("\n" + "="*50)
            print("Initializing Hybrid RAG (MeTTa + Vector)...")
            print("="*50)

            # Initialize MeTTa instance and knowledge graph
            print("  [1/5] Creating MeTTa instance...", end=" ", flush=True)
            metta = MeTTa()
            print("✓")

            print(f"  [2/5] Loading knowledge graph from {data_path.name}...", end=" ", flush=True)
            initialize_pim_knowledge_graph(metta, str(data_path))
            print("✓")

            # Initialize PIMRAG with MeTTa instance
            print("  [3/5] Initializing PIMRAG...", end=" ", flush=True)
            self.pim_rag = PIMRAG(metta)
            print("✓")

            # Load data for vector store
            print("  [4/5] Loading vector store (ChromaDB)...", end=" ", flush=True)
            with open(data_path, 'r') as f:
                pim_data = json.load(f)

            db_path = Path(__file__).parent / "chroma_db_benchmark"
            self.vector_store = PIMVectorStore(db_path=str(db_path))
            self.vector_store.ingest_pim_data(pim_data)
            print("✓")

            print("  [5/5] Initializing LLM client...", end=" ", flush=True)
            self.llm = LLM(self.api_key)
            print("✓")

            self.rag_initialized = True
            print("="*50)
            print("✓ Hybrid RAG initialized successfully!")
            print("="*50 + "\n")
            return True

        except Exception as e:
            print(f"✗ Failed to initialize RAG: {e}")
            import traceback
            traceback.print_exc()
            return False

    def search(self, query: str, timeout: int = 30) -> Dict:
        """
        Search using Hybrid RAG (Vector + MeTTa Knowledge Graph)

        Returns:
            {
                "query": str,
                "response": str,
                "products": List[Dict],
                "num_results": int,
                "latency_ms": int,
                "success": bool,
                "error": Optional[str]
            }
        """
        start_time = time.time()

        try:
            # Initialize RAG if needed
            if not self._init_rag():
                return {
                    "query": query,
                    "response": "",
                    "products": [],
                    "num_results": 0,
                    "latency_ms": -1,
                    "success": False,
                    "error": "Failed to initialize RAG components"
                }

            # Perform vector search
            search_results = self.vector_store.search(query, k=10)

            # Build context from results using MeTTa knowledge graph
            context_parts = []
            products = []

            for result in search_results:
                uuid = result.get("uuid", "")

                # Get full context from MeTTa knowledge graph (HYBRID RAG)
                full_context = self.pim_rag.get_full_product_context(uuid)
                context_parts.append(full_context)

                # Extract product info for structured response
                products.append({
                    "uuid": uuid,
                    "text": result.get("text", ""),
                    "name": result.get("text", "").split(" - ")[0] if result.get("text") else "",
                    "score": result.get("score", 0),
                    "context": full_context
                })

            context = "\n\n".join(context_parts)

            # Generate LLM response
            system_prompt = """You are a helpful product assistant for a running shoe store.
Use the provided product context to answer customer questions accurately.
If the information is not in the context, say so honestly."""

            user_prompt = f"""Based on the following product information:

{context}

Please answer this question: {query}"""

            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response_text = self.llm.create_completion(full_prompt, max_tokens=500)

            latency_ms = int((time.time() - start_time) * 1000)

            return {
                "query": query,
                "response": response_text,
                "products": products,
                "num_results": len(products),
                "context_length": len(context),
                "latency_ms": latency_ms,
                "success": True,
                "error": None,
                "search_type": "hybrid_rag"
            }

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "query": query,
                "response": "",
                "products": [],
                "num_results": 0,
                "latency_ms": latency_ms,
                "success": False,
                "error": str(e),
                "search_type": "hybrid_rag"
            }


# =============================================================================
# KEYWORD SEARCH TESTER - Website Scraping + Keyword Matching
# =============================================================================

class KeywordSearchTester:
    """Tests keyword search by scraping website and matching keywords"""

    def __init__(self, website_url: str = "https://dash-stride-shop.lovable.app/"):
        self.website_url = website_url
        self.products_url = website_url.rstrip('/') + "/products"
        self.driver = None

        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium is required for website testing")

    def setup(self):
        """Initialize Selenium WebDriver"""
        print("Setting up Chrome WebDriver...")
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            print("✓ Chrome WebDriver ready")
        except Exception as e:
            print(f"✗ Chrome WebDriver failed: {e}")
            print("  Hint: Install Chrome with: wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && sudo dpkg -i google-chrome-stable_current_amd64.deb && sudo apt-get install -f -y")
            raise

    def teardown(self):
        """Close WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def search(self, query: str, timeout: int = 15) -> Dict:
        """Perform keyword search by scraping website and matching keywords"""
        if not self.driver:
            self.setup()

        start_time = time.time()

        try:
            # Navigate to products page
            self.driver.get(self.products_url)
            time.sleep(2)  # Wait for page load

            # Scrape all visible products
            all_page_products = []

            # Category/navigation words and UI elements to filter out
            nav_words = {'all shoes', 'trail running', 'road running', 'running shoes',
                        'shop all', 'view all', 'categories', 'filter', 'sort', 'sort by:',
                        'home', 'about', 'contact', 'cart', 'checkout', 'menu', 'featured',
                        'trail', 'road', 'road/trail', 'road/gym', 'road fast', 'showing',
                        'price', 'rating', 'newest', 'best sellers', 'new arrivals'}

            # Try multiple selectors for product cards
            product_selectors = [
                # More specific product card selectors
                "[class*='product-card']",
                "[class*='ProductCard']",
                ".grid > div",  # Grid children (product cards)
                "[class*='card'] > a",  # Cards with links
                "a[href*='/products/'][href*='-']",  # Product links with slugs (have hyphens)
            ]

            for selector in product_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if not elements:
                        continue

                    for elem in elements[:50]:
                        try:
                            text = elem.text.strip()
                            if not text or len(text) < 10:
                                continue

                            lines = [l.strip() for l in text.split('\n') if l.strip()]
                            if not lines:
                                continue

                            # Extract price first
                            price = ""
                            for line in lines:
                                if '$' in line or '£' in line:
                                    price = line.strip()
                                    break

                            # Smart name extraction: skip category/rating lines to find brand + product
                            # Typical pattern: Category\nRating\nBRAND\nProduct Name\nDescription\nPrice
                            name = ""
                            brand = ""
                            product_name = ""

                            for i, line in enumerate(lines):
                                line_lower = line.lower()
                                # Skip navigation words, ratings (pure numbers), and short items
                                if line_lower in nav_words or len(line) < 3:
                                    continue
                                # Skip lines that are just ratings like "4.9" or "(2,555)"
                                if re.match(r'^[\d.]+$', line) or re.match(r'^\([\d,]+\)$', line):
                                    continue
                                # Skip price lines
                                if '$' in line or '£' in line:
                                    continue

                                # First valid line is likely brand (often uppercase)
                                if not brand:
                                    brand = line
                                # Second valid line is likely product name
                                elif not product_name:
                                    product_name = line
                                    break

                            # Construct name from brand + product
                            if brand and product_name:
                                name = f"{brand} {product_name}"
                            elif brand:
                                name = brand
                            else:
                                name = lines[0].strip()

                            # Skip if name is still a nav word
                            if name.lower() in nav_words or len(name) < 5:
                                continue

                            # Prefer entries with prices (real products usually have prices)
                            if price or len(text) > 80:
                                all_page_products.append({
                                    "name": name,
                                    "price": price,
                                    "full_text": text[:300],
                                    "has_price": bool(price)
                                })
                        except Exception:
                            continue

                    # If we found products with prices, we're done
                    products_with_prices = [p for p in all_page_products if p.get('has_price')]
                    if len(products_with_prices) >= 3:
                        all_page_products = products_with_prices
                        break
                except Exception:
                    continue

            # Remove duplicates by name
            seen_names = set()
            unique_products = []
            for p in all_page_products:
                if p['name'].lower() not in seen_names:
                    seen_names.add(p['name'].lower())
                    p.pop('has_price', None)
                    unique_products.append(p)
            all_page_products = unique_products

            # Keyword matching on scraped products
            products = []
            query_lower = query.lower()
            query_terms = [term for term in query_lower.split() if len(term) > 2]

            for product in all_page_products:
                product_text = (
                    product.get("name", "") + " " +
                    product.get("full_text", "")
                ).lower()

                matches = sum(1 for term in query_terms if term in product_text)

                if matches > 0:
                    products.append({
                        "name": product["name"],
                        "price": product.get("price", ""),
                        "full_text": product.get("full_text", ""),
                        "match_score": matches
                    })

            # Sort by match score and take top 10
            products.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            products = products[:10]

            # Remove match_score from output
            for p in products:
                p.pop("match_score", None)

            latency_ms = int((time.time() - start_time) * 1000)

            return {
                "query": query,
                "response": f"Found {len(products)} products (keyword match)",
                "products": products,
                "num_results": len(products),
                "latency_ms": latency_ms,
                "success": True,
                "error": None,
                "search_type": "keyword"
            }

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "query": query,
                "response": "",
                "products": [],
                "num_results": 0,
                "latency_ms": latency_ms,
                "success": False,
                "error": str(e),
                "search_type": "keyword"
            }


# =============================================================================
# BENCHMARK RUNNER
# =============================================================================

class BenchmarkRunner:
    """Orchestrates benchmark execution with dual evaluation"""

    def __init__(self, queries_file: str = None, question_file: str = None):
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)

        # Load queries from file or use defaults
        self.queries = []
        self.metadata = {}
        self.source = "default"

        if question_file and PANDAS_AVAILABLE:
            self._load_excel_queries(question_file)
        elif queries_file:
            self._load_json_queries(queries_file)
        else:
            default_file = Path(__file__).parent / "queries.json"
            if default_file.exists():
                self._load_json_queries(str(default_file))
            else:
                self._load_default_queries()

        # Testers (initialized lazily)
        self.semantic_tester = None
        self.keyword_tester = None
        self.evaluator = None

    def _load_json_queries(self, filepath: str):
        """Load queries from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
            self.queries = data.get("queries", [])
            self.metadata = data.get("metadata", {})
            self.source = f"JSON: {Path(filepath).name}"
        print(f"Loaded {len(self.queries)} queries from {filepath}")

    def _load_excel_queries(self, filepath: str):
        """Load queries from Excel file"""
        df = pd.read_excel(filepath)
        question_col = None
        for col in df.columns:
            if 'question' in col.lower() or 'query' in col.lower():
                question_col = col
                break
        if not question_col:
            question_col = df.columns[0]

        self.queries = []

        # Check if column header itself looks like a question (common Excel format issue)
        # If the header is long and contains question marks or question words, treat it as data
        header_text = str(question_col)
        if len(header_text) > 30 or '?' in header_text or any(
            word in header_text.lower() for word in ['what', 'which', 'how', 'recommend', 'best', 'find']
        ):
            self.queries.append({"id": "Q001", "query": header_text, "category": "custom"})
            start_id = 2
        else:
            start_id = 1

        # Add remaining queries from rows
        for i, row in df.iterrows():
            if pd.notna(row[question_col]):
                self.queries.append({
                    "id": f"Q{i + start_id:03d}",
                    "query": str(row[question_col]),
                    "category": "custom"
                })

        self.source = f"Excel: {Path(filepath).name}"
        print(f"Loaded {len(self.queries)} queries from Excel")

    def _load_default_queries(self):
        """Load default test queries"""
        self.queries = [
            {"id": "Q001", "query": "waterproof trail running shoes", "category": "attribute_based"},
            {"id": "Q002", "query": "lightweight marathon shoes", "category": "attribute_based"},
            {"id": "Q003", "query": "cushioned shoes for long distance", "category": "attribute_based"},
            {"id": "Q004", "query": "trail shoes under $150", "category": "budget_constrained"},
            {"id": "Q005", "query": "best running shoes for beginners", "category": "conversational"},
        ]
        self.source = "default queries"
        print(f"Using {len(self.queries)} default queries")

    def initialize_testers(self):
        """Initialize testers lazily"""
        if not self.semantic_tester:
            self.semantic_tester = AgentFabricTester()

        if not self.keyword_tester and SELENIUM_AVAILABLE:
            try:
                self.keyword_tester = KeywordSearchTester()
            except Exception as e:
                print(f"Warning: Could not initialize keyword tester: {e}")

    def run_comparison(self, sample_size: int = None, evaluate: bool = False,
                       include_keyword: bool = True):
        """Run comparison benchmark with dual evaluation"""
        from tqdm import tqdm

        # Initialize testers
        self.initialize_testers()

        # Initialize evaluator if requested
        if evaluate:
            env_path = Path(__file__).parent.parent / ".env"
            load_dotenv(env_path)
            api_key = os.getenv("ASI_ONE_API_KEY")
            if api_key:
                self.evaluator = LLMEvaluator(api_key)
                print("✓ LLM Evaluator enabled for dual evaluation")
            else:
                print("Warning: ASI_ONE_API_KEY not found, skipping evaluation")

        queries_to_test = self.queries[:sample_size] if sample_size else self.queries
        total = len(queries_to_test)

        print(f"\n{'='*70}")
        print(f"RUNNING BENCHMARK: {total} queries")
        print(f"Source: {self.source}")
        print(f"Semantic Search: Hybrid RAG (MeTTa + Vector)")
        print(f"Keyword Search: {'Enabled' if include_keyword and self.keyword_tester else 'Disabled'}")
        print(f"Evaluation: {'Dual (Retrieval + Response)' if self.evaluator else 'Disabled'}")
        print(f"{'='*70}\n")

        results = []
        semantic_stats = {"success": 0, "failed": 0, "total_latency": 0, "total_results": 0}
        keyword_stats = {"success": 0, "failed": 0, "total_latency": 0, "total_results": 0}

        # Evaluation stats
        semantic_retrieval_stats = {"relevance": [], "coverage": [], "precision": []}
        semantic_response_stats = {"accuracy": [], "hallucination": [], "helpfulness": [], "completeness": [], "usefulness": []}
        keyword_retrieval_stats = {"relevance": [], "coverage": [], "precision": []}
        keyword_response_stats = {"accuracy": [], "hallucination": [], "helpfulness": [], "completeness": [], "usefulness": []}

        pbar = tqdm(queries_to_test, desc="Benchmarking", unit="query")

        for query_obj in pbar:
            query_text = query_obj["query"]

            # ============ SEMANTIC SEARCH (Hybrid RAG) ============
            semantic_result = self.semantic_tester.search(query_text)

            if self.evaluator and semantic_result["success"]:
                # Evaluate retrieval quality
                retrieval_eval = self.evaluator.evaluate_retrieval(
                    query_text,
                    semantic_result.get("products", [])
                )
                semantic_result["retrieval_evaluation"] = retrieval_eval
                for key in ["relevance", "coverage", "precision"]:
                    if retrieval_eval.get(key, 0) > 0:
                        semantic_retrieval_stats[key].append(retrieval_eval[key])

                # Evaluate response quality
                response_eval = self.evaluator.evaluate_response(
                    query_text,
                    semantic_result.get("response", ""),
                    semantic_result.get("products", [])
                )
                semantic_result["response_evaluation"] = response_eval
                for key in ["accuracy", "hallucination", "helpfulness", "completeness", "usefulness"]:
                    if response_eval.get(key, 0) > 0:
                        semantic_response_stats[key].append(response_eval[key])

            if semantic_result["success"]:
                semantic_stats["success"] += 1
                semantic_stats["total_latency"] += semantic_result["latency_ms"]
                semantic_stats["total_results"] += semantic_result["num_results"]
            else:
                semantic_stats["failed"] += 1

            # ============ KEYWORD SEARCH ============
            keyword_result = {"success": False, "products": [], "num_results": 0}

            if include_keyword and self.keyword_tester:
                try:
                    keyword_result = self.keyword_tester.search(query_text)
                except Exception as e:
                    if "Chrome" in str(e) or "chromedriver" in str(e).lower():
                        print(f"\n⚠ Chrome not available - skipping keyword search")
                        print("  Run with --no-keyword or install Chrome in WSL")
                        include_keyword = False  # Disable for remaining queries
                        self.keyword_tester = None
                    else:
                        print(f"\n⚠ Keyword search error: {e}")
                        keyword_result = {"success": False, "error": str(e), "products": [], "num_results": 0}

                if self.evaluator and keyword_result["success"]:
                    # Evaluate retrieval quality
                    retrieval_eval = self.evaluator.evaluate_retrieval(
                        query_text,
                        keyword_result.get("products", [])
                    )
                    keyword_result["retrieval_evaluation"] = retrieval_eval
                    for key in ["relevance", "coverage", "precision"]:
                        if retrieval_eval.get(key, 0) > 0:
                            keyword_retrieval_stats[key].append(retrieval_eval[key])

                    # Generate LLM response (fair comparison - same LLM)
                    llm_response = self.evaluator.generate_response(
                        query_text,
                        keyword_result.get("products", [])
                    )
                    keyword_result["llm_response"] = llm_response

                    # Evaluate response quality
                    response_eval = self.evaluator.evaluate_response(
                        query_text,
                        llm_response,
                        keyword_result.get("products", [])
                    )
                    keyword_result["response_evaluation"] = response_eval
                    for key in ["accuracy", "hallucination", "helpfulness", "completeness", "usefulness"]:
                        if response_eval.get(key, 0) > 0:
                            keyword_response_stats[key].append(response_eval[key])

                if keyword_result["success"]:
                    keyword_stats["success"] += 1
                    keyword_stats["total_latency"] += keyword_result["latency_ms"]
                    keyword_stats["total_results"] += keyword_result["num_results"]
                else:
                    keyword_stats["failed"] += 1

            results.append({
                "query_id": query_obj.get("id", ""),
                "query": query_text,
                "category": query_obj.get("category", "unknown"),
                "semantic": semantic_result,
                "keyword": keyword_result
            })

            pbar.set_postfix({
                "Sem": f"{semantic_stats['success']}/{semantic_stats['success']+semantic_stats['failed']}",
                "Key": f"{keyword_stats['success']}/{keyword_stats['success']+keyword_stats['failed']}"
            })

            time.sleep(0.5)  # Rate limiting

        pbar.close()

        if self.keyword_tester:
            self.keyword_tester.teardown()

        # Calculate averages
        semantic_avg_latency = semantic_stats["total_latency"] / max(semantic_stats["success"], 1)
        keyword_avg_latency = keyword_stats["total_latency"] / max(keyword_stats["success"], 1)
        semantic_avg_results = semantic_stats["total_results"] / max(semantic_stats["success"], 1)
        keyword_avg_results = keyword_stats["total_results"] / max(keyword_stats["success"], 1)

        def calc_avg(stats_dict):
            return {k: sum(v)/len(v) if v else 0 for k, v in stats_dict.items()}

        semantic_retrieval_avg = calc_avg(semantic_retrieval_stats)
        semantic_response_avg = calc_avg(semantic_response_stats)
        keyword_retrieval_avg = calc_avg(keyword_retrieval_stats)
        keyword_response_avg = calc_avg(keyword_response_stats)

        # ============ PRINT RESULTS ============
        print(f"\n{'='*70}")
        print("BENCHMARK RESULTS")
        print(f"{'='*70}")

        print(f"\n{'='*70}")
        print("1. PERFORMANCE COMPARISON")
        print(f"{'='*70}")
        print(f"\n{'Metric':<25} {'Semantic (Hybrid RAG)':<22} {'Keyword Search':<20}")
        print(f"{'-'*67}")
        print(f"{'Success Rate':<25} {semantic_stats['success']}/{total} ({semantic_stats['success']/total*100:.1f}%){'':<5} {keyword_stats['success']}/{total} ({keyword_stats['success']/total*100:.1f}%)")
        print(f"{'Avg Latency':<25} {semantic_avg_latency:.0f}ms{'':<15} {keyword_avg_latency:.0f}ms")
        print(f"{'Avg Results':<25} {semantic_avg_results:.1f}{'':<17} {keyword_avg_results:.1f}")

        if semantic_retrieval_avg.get("relevance", 0) > 0:
            print(f"\n{'='*70}")
            print("2. RETRIEVAL QUALITY COMPARISON")
            print(f"{'='*70}")
            print(f"\n{'Metric':<20} {'Semantic':<15} {'Keyword':<15} {'Winner':<15}")
            print(f"{'-'*65}")
            for metric in ["relevance", "coverage", "precision"]:
                sem_val = semantic_retrieval_avg.get(metric, 0)
                key_val = keyword_retrieval_avg.get(metric, 0)
                winner = "Semantic" if sem_val > key_val else ("Keyword" if key_val > sem_val else "Tie")
                print(f"{metric.capitalize():<20} {sem_val:.2f}/5{'':<8} {key_val:.2f}/5{'':<8} {winner}")

        if semantic_response_avg.get("accuracy", 0) > 0:
            print(f"\n{'='*70}")
            print("3. RESPONSE QUALITY COMPARISON")
            print(f"{'='*70}")
            print(f"\n{'Metric':<20} {'Semantic':<15} {'Keyword':<15} {'Winner':<15}")
            print(f"{'-'*65}")
            for metric in ["accuracy", "hallucination", "helpfulness", "completeness", "usefulness"]:
                sem_val = semantic_response_avg.get(metric, 0)
                key_val = keyword_response_avg.get(metric, 0)
                winner = "Semantic" if sem_val > key_val else ("Keyword" if key_val > sem_val else "Tie")
                label = "No Hallucination" if metric == "hallucination" else metric.capitalize()
                print(f"{label:<20} {sem_val:.2f}/5{'':<8} {key_val:.2f}/5{'':<8} {winner}")

        # Count wins
        semantic_wins = 0
        keyword_wins = 0

        if semantic_avg_results > keyword_avg_results:
            semantic_wins += 1
        elif keyword_avg_results > semantic_avg_results:
            keyword_wins += 1

        if keyword_avg_latency > 0 and semantic_avg_latency < keyword_avg_latency:
            semantic_wins += 1
        elif semantic_avg_latency > keyword_avg_latency:
            keyword_wins += 1

        for metric in ["relevance", "coverage", "precision"]:
            if semantic_retrieval_avg.get(metric, 0) > keyword_retrieval_avg.get(metric, 0):
                semantic_wins += 1
            elif keyword_retrieval_avg.get(metric, 0) > semantic_retrieval_avg.get(metric, 0):
                keyword_wins += 1

        for metric in ["accuracy", "hallucination", "helpfulness", "completeness", "usefulness"]:
            if semantic_response_avg.get(metric, 0) > keyword_response_avg.get(metric, 0):
                semantic_wins += 1
            elif keyword_response_avg.get(metric, 0) > semantic_response_avg.get(metric, 0):
                keyword_wins += 1

        print(f"\n{'='*70}")
        print("4. OVERALL WINNER")
        print(f"{'='*70}")
        print(f"\nScore: Semantic {semantic_wins} - {keyword_wins} Keyword")
        if semantic_wins > keyword_wins:
            print("★ WINNER: Semantic Search (Hybrid RAG - MeTTa + Vector)")
        elif keyword_wins > semantic_wins:
            print("★ WINNER: Keyword Search")
        else:
            print("★ TIE")

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.results_dir / f"benchmark_{timestamp}.json"

        output_data = {
            "benchmark_type": "hybrid_rag_comparison",
            "timestamp": datetime.now().isoformat(),
            "source": self.source,
            "total_queries": total,
            "summary": {
                "semantic_search": {
                    "type": "hybrid_rag",
                    "success": semantic_stats["success"],
                    "failed": semantic_stats["failed"],
                    "avg_latency_ms": semantic_avg_latency,
                    "avg_results": semantic_avg_results,
                    "retrieval_quality": semantic_retrieval_avg,
                    "response_quality": semantic_response_avg
                },
                "keyword_search": {
                    "type": "keyword",
                    "success": keyword_stats["success"],
                    "failed": keyword_stats["failed"],
                    "avg_latency_ms": keyword_avg_latency,
                    "avg_results": keyword_avg_results,
                    "retrieval_quality": keyword_retrieval_avg,
                    "response_quality": keyword_response_avg
                },
                "winner": {
                    "semantic_wins": semantic_wins,
                    "keyword_wins": keyword_wins,
                    "overall": "semantic" if semantic_wins > keyword_wins else ("keyword" if keyword_wins > semantic_wins else "tie")
                }
            },
            "results": results
        }

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\n{'='*70}")
        print(f"Results saved to: {output_file}")
        print(f"{'='*70}")

        return output_data

    def run_category(self, category: str, evaluate: bool = False):
        """Run queries in a specific category"""
        category_queries = [q for q in self.queries if q.get("category") == category]

        if not category_queries:
            print(f"Error: No queries found for category '{category}'")
            if self.metadata.get("categories"):
                print(f"Available categories: {list(self.metadata['categories'].keys())}")
            return

        # Temporarily filter queries
        original_queries = self.queries
        self.queries = category_queries
        self.source = f"Category: {category}"

        result = self.run_comparison(evaluate=evaluate)

        self.queries = original_queries
        return result

    def run_single_query(self, query_text: str, compare: bool = True, evaluate: bool = False):
        """Run a single query"""
        self.queries = [{"id": "Q001", "query": query_text, "category": "single"}]
        self.source = "Single query"

        return self.run_comparison(evaluate=evaluate, include_keyword=compare)


def main():
    parser = argparse.ArgumentParser(description="Benchmark AgentFabric Hybrid RAG vs Keyword Search")
    parser.add_argument("--full", action="store_true", help="Run all queries")
    parser.add_argument("--sample", type=int, help="Run N sample queries")
    parser.add_argument("--category", type=str, help="Run queries in specific category")
    parser.add_argument("--query", type=str, help="Run a single query")
    parser.add_argument("--question_file", type=str, help="Path to Excel file with questions")
    parser.add_argument("--evaluate", action="store_true", help="Enable dual LLM evaluation")
    parser.add_argument("--no-keyword", action="store_true", help="Skip keyword search (semantic only)")

    args = parser.parse_args()

    # Create runner
    runner = BenchmarkRunner(question_file=args.question_file)

    # Execute based on arguments
    if args.query:
        runner.run_single_query(args.query, compare=not args.no_keyword, evaluate=args.evaluate)
    elif args.category:
        runner.run_category(args.category, evaluate=args.evaluate)
    elif args.full or args.question_file or args.sample:
        # Pass sample_size regardless of source (works with --full, --question_file, or --sample alone)
        runner.run_comparison(sample_size=args.sample, evaluate=args.evaluate,
                             include_keyword=not args.no_keyword)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python benchmark_runner.py --sample 5 --evaluate")
        print("  python benchmark_runner.py --full --evaluate")
        print("  python benchmark_runner.py --category attribute_based")
        print("  python benchmark_runner.py --query 'waterproof trail shoes' --evaluate")
        print("  python benchmark_runner.py --question_file questions.xlsx --evaluate")


if __name__ == "__main__":
    main()
