# Semantic Search Benchmarking Framework

> **Detailed Guide**: For comprehensive documentation including architecture diagrams, step-by-step explanations, and troubleshooting, see [docs/BENCHMARK_GUIDE.md](../docs/BENCHMARK_GUIDE.md)

## Overview
This framework compares AgentFabric's **Hybrid RAG** (MeTTa knowledge graph + ChromaDB vector store) against traditional keyword-based website search to measure accuracy, relevance, and hallucination rates.

## Key Features

- **Dual Evaluation**: Measures both retrieval quality AND response quality
- **Fair Comparison**: Both systems use the same LLM for response generation
- **Hybrid RAG**: Full MeTTa + Vector search for semantic understanding
- **Flexible Input**: JSON queries, Excel files, single queries, or category tests
- **LLM-as-Judge**: Automated scoring using ASI:One API

## Systems Being Compared

**System A: AgentFabric Semantic Search (Hybrid RAG)**
- **Technology**: ChromaDB vector embeddings + MeTTa knowledge graph (Hybrid RAG)
- **Approach**: Natural language query understanding with intent-based matching
- **Process**: Query → Vector search → MeTTa enrichment → LLM response
- **Example Query**: "Waterproof trail running shoes durable under £200"
- **Returns**: Semantically relevant products with contextual responses

**System B: Keyword Search (Website Scraping)**
- **Platform**: DashStride Shop - https://dash-stride-shop.lovable.app/
- **Technology**: Website scraping + keyword matching
- **Approach**: Scrape products page, match query terms against product text
- **Returns**: Products matching keyword overlap

## Methodology

### 1. Dual Evaluation Framework

The benchmark uses **LLM-as-Judge** to evaluate both systems fairly across two dimensions:

#### A. Retrieval Quality (How good are the retrieved products?)

| Metric | Description | Scale |
|--------|-------------|-------|
| **Relevance** | How relevant are the products to the query? | 1-5 |
| **Coverage** | Do results cover the user's needs? | 1-5 |
| **Precision** | Are ALL returned products relevant? | 1-5 |

#### B. Response Quality (How good is the LLM response?)

| Metric | Description | Scale |
|--------|-------------|-------|
| **Accuracy** | Does response accurately reflect product data? | 1-5 |
| **Hallucination** | Does it invent facts NOT in the data? (5=none) | 1-5 |
| **Helpfulness** | How useful is this for a real shopper? | 1-5 |
| **Completeness** | Does it fully answer the question? | 1-5 |

#### Fair Comparison Methodology

To ensure fair comparison, **both systems use the same LLM** for response generation:

```
Semantic Search:    Query → Hybrid RAG → Products → LLM → Response → Evaluate
Keyword Search:     Query → Scrape → Keywords → Products → SAME LLM → Response → Evaluate
```

This ensures we're comparing the **retrieval quality** of each system, not just which one has an LLM.

### 2. Performance Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Success Rate** | % of queries that return results | >95% |
| **Avg Latency** | Time to return results (ms) | <1000ms |
| **Avg Results** | Number of products returned | 5-10 |

### 3. Test Query Dataset

We test across 6 categories for comprehensive coverage:

#### Category 1: Specific Product Queries (5 queries)
Tests exact product name matching and "not found" handling
```
- "Show me Nike Air Zoom Pegasus"
- "Do you have Adidas Ultraboost 22?"
- "AeroStride CloudTrail Pro"
- "Find me the NimbusPath Marathon Runner"
- "FleetStep TrailBlazer X3"
```
**Expected**: Exact product match if exists, or graceful "not found" response

#### Category 2: Attribute-Based Queries (10 queries)
Tests single and multi-attribute matching
```
- "Waterproof trail running shoes"
- "Lightweight shoes for marathon"
- "Cushioned shoes for overpronation"
- "Carbon plate racing shoes"
- "Stability shoes for flat feet"
- "Breathable summer running shoes"
- "Durable trail shoes"
- "Minimalist zero-drop shoes"
- "Wide fit running shoes"
- "High ankle support trail shoes"
```
**Expected**: Products matching specified attributes, ranked by relevance

#### Category 3: Budget-Constrained Queries (8 queries)
Tests price filtering and value matching
```
- "Trail running shoes under £200"
- "Best marathon shoes between £100-£150"
- "Affordable running shoes under £80"
- "Premium running shoes over £200"
- "Budget trail shoes"
- "Cheapest waterproof running shoes"
- "Running shoes under £50"
- "Mid-range cushioned shoes around £120"
```
**Expected**: Products within price range, sorted by value/relevance

#### Category 4: Comparison Queries (5 queries)
Tests ability to compare products
```
- "Compare Nike Pegasus vs Adidas Ultraboost"
- "What's better for trail running: Hoka vs Salomon?"
- "Difference between Pegasus 39 and Pegasus 40"
- "Brooks Ghost vs ASICS Gel-Nimbus"
- "Carbon plate shoes comparison"
```
**Expected**: Side-by-side comparison with factual differences

#### Category 5: Complex Multi-Attribute Queries (12 queries)
Tests AND logic and complex intent understanding
```
- "Waterproof trail shoes for wide feet under £200"
- "Lightweight carbon-plated racing shoes for marathon under £250"
- "Durable trail shoes with good grip for muddy conditions"
- "Cushioned shoes for long distance with wide toe box"
- "Trail running shoes for women under £150 waterproof"
- "Summer trail shoes breathable and lightweight under £180"
- "Stability shoes for overpronation carbon plate"
- "Trail shoes for beginners durable under £120"
- "Marathon shoes lightweight fast under £200"
- "Winter running shoes waterproof warm grip"
- "Recovery shoes cushioned wide under £100"
- "Trail shoes rocky terrain ankle support under £220"
```
**Expected**: Products matching ALL criteria (AND logic), ranked by best overall match

#### Category 6: Conversational/Vague Queries (10 queries)
Tests natural language understanding and recommendation ability
```
- "Good shoes for trail running"
- "Something durable"
- "What do you recommend for beginners?"
- "I need shoes for my first marathon"
- "Best shoes for rainy weather"
- "Comfortable daily trainer"
- "Shoes for rocky trails"
- "I run 50 miles per week, what should I get?"
- "Something for speed work"
- "Shoes that won't hurt my knees"
```
**Expected**: Reasonable recommendations with explanations

**Total Test Queries**: 50 queries across 6 categories

### 3. Ground Truth Dataset Format

For each test query, we define expected results:

```json
{
  "query_id": "Q001",
  "query": "Waterproof trail running shoes under £200",
  "category": "complex_multi_attribute",
  "expected_products": [
    {
      "uuid": "uuid-cloudtrail-waterproof",
      "brand": "CloudTrail",
      "name": "CloudTrail Waterproof Pro",
      "match_reason": "Exact match: waterproof, trail, £180"
    },
    {
      "uuid": "uuid-terraprint-aqua",
      "brand": "TerraSprint",
      "name": "TerraSprint AquaShield",
      "match_reason": "Waterproof, trail, £195"
    }
  ],
  "required_attributes": {
    "type": "trail",
    "waterproof": true,
    "max_price": 200
  },
  "unacceptable_results": [
    {
      "issue": "road_shoes",
      "reason": "Must be trail shoes, not road"
    },
    {
      "issue": "non_waterproof",
      "reason": "Waterproof is a required attribute"
    },
    {
      "issue": "over_budget",
      "reason": "Price must be under £200"
    }
  ],
  "min_expected_results": 2,
  "max_acceptable_results": 10
}
```

### 4. Quick Start

#### Prerequisites
```bash
# Ensure you're in WSL (hyperon/MeTTa requires Linux)
cd /mnt/e/Hackathon/UK\ AI\ Agent\ Hackathon\ Ep3/eComAgent

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install selenium webdriver-manager pandas tqdm python-dotenv openai openpyxl

# Ensure ASI_ONE_API_KEY is set in .env
```

#### Run Benchmark
```bash
# Quick test with 5 queries + dual evaluation
python benchmarking/benchmark_runner.py --sample 5 --evaluate

# Run with Sample Consumer Questions Excel file (30 questions)
python benchmarking/benchmark_runner.py --question_file "../Sample Consumer Questions.xlsx" --evaluate

# Full benchmark suite with default queries
python benchmarking/benchmark_runner.py --full --evaluate

# Run specific category
python benchmarking/benchmark_runner.py --category attribute_based --evaluate

# Single query test
python benchmarking/benchmark_runner.py --query "waterproof trail shoes" --evaluate

# Semantic search only (skip keyword search comparison)
python benchmarking/benchmark_runner.py --sample 5 --evaluate --no-keyword
```

#### Command-Line Options

| Option | Description |
|--------|-------------|
| `--full` | Run all queries from queries.json |
| `--sample N` | Run first N queries (quick testing) |
| `--category CAT` | Run queries in specific category |
| `--query "text"` | Run a single query |
| `--question_file FILE` | Load queries from Excel file |
| `--evaluate` | Enable dual LLM evaluation |
| `--no-keyword` | Skip keyword search (semantic only) |

#### Review Results
```bash
# Generate comparison report from results
python benchmarking/comparison_report.py benchmarking/results/benchmark_*.json

# View raw JSON results
cat benchmarking/results/benchmark_*.json | python -m json.tool
```

### 5. Hallucination Detection Methods

#### Automated Checks:
```python
def check_hallucinations(response, ground_truth_db):
    """
    Automated hallucination detection
    """
    hallucinations = []

    for product in response.products:
        # 1. Product Existence Check
        if not ground_truth_db.exists(product.uuid):
            hallucinations.append({
                "type": "non_existent_product",
                "claim": f"Product {product.name} (UUID: {product.uuid})",
                "severity": "critical"
            })

        # 2. Attribute Verification
        actual_product = ground_truth_db.get(product.uuid)
        if product.waterproof != actual_product.waterproof:
            hallucinations.append({
                "type": "incorrect_attribute",
                "claim": f"Waterproof={product.waterproof}",
                "actual": f"Waterproof={actual_product.waterproof}",
                "severity": "high"
            })

        # 3. Price Accuracy (within 5% tolerance)
        price_diff = abs(product.price - actual_product.price) / actual_product.price
        if price_diff > 0.05:
            hallucinations.append({
                "type": "incorrect_price",
                "claim": f"Price=£{product.price}",
                "actual": f"Price=£{actual_product.price}",
                "severity": "high"
            })

        # 4. Availability Check
        if product.in_stock != actual_product.in_stock:
            hallucinations.append({
                "type": "incorrect_availability",
                "claim": f"In Stock={product.in_stock}",
                "actual": f"In Stock={actual_product.in_stock}",
                "severity": "medium"
            })

        # 5. Size/Variant Check
        if hasattr(product, 'sizes'):
            invalid_sizes = [s for s in product.sizes if s not in actual_product.available_sizes]
            if invalid_sizes:
                hallucinations.append({
                    "type": "invalid_sizes",
                    "claim": f"Sizes available: {invalid_sizes}",
                    "actual": f"Actual sizes: {actual_product.available_sizes}",
                    "severity": "medium"
                })

    return hallucinations
```

#### Manual Review Checklist:
- [ ] Read the full response text
- [ ] Verify product names mentioned actually exist
- [ ] Check price claims against PIM data (Akeneo)
- [ ] Confirm attribute claims (waterproof, materials, etc.)
- [ ] Validate ratings/reviews if mentioned
- [ ] Check for contradictions within the response
- [ ] Flag any suspicious or too-good-to-be-true claims

### 6. Expected Results Format

The benchmark produces comprehensive output with dual evaluation:

```
======================================================================
BENCHMARK RESULTS
======================================================================

======================================================================
1. PERFORMANCE COMPARISON
======================================================================

Metric                    Semantic (Hybrid RAG)  Keyword Search
-------------------------------------------------------------------
Success Rate              5/5 (100.0%)           5/5 (100.0%)
Avg Latency               2450ms                 1200ms
Avg Results               10.0                   4.2

======================================================================
2. RETRIEVAL QUALITY COMPARISON
======================================================================

Metric               Semantic        Keyword         Winner
-----------------------------------------------------------------
Relevance            4.60/5          3.20/5          Semantic
Coverage             4.40/5          2.80/5          Semantic
Precision            4.20/5          3.00/5          Semantic

======================================================================
3. RESPONSE QUALITY COMPARISON
======================================================================

Metric               Semantic        Keyword         Winner
-----------------------------------------------------------------
Accuracy             4.40/5          3.60/5          Semantic
No Hallucination     4.60/5          3.80/5          Semantic
Helpfulness          4.20/5          3.40/5          Semantic
Completeness         4.40/5          3.20/5          Semantic

======================================================================
4. OVERALL WINNER
======================================================================

Score: Semantic 9 - 0 Keyword
★ WINNER: Semantic Search (Hybrid RAG - MeTTa + Vector)
```

### 7. Keyword Search Implementation

Since the DashStride website doesn't have a search box, we scrape the products page and perform keyword matching:

```python
# How KeywordSearchTester works:
class KeywordSearchTester:
    def search(self, query: str):
        # 1. Navigate to products page
        self.driver.get("https://dash-stride-shop.lovable.app/products")

        # 2. Scrape all visible products from the grid
        products = self._scrape_products()  # Gets name, price, text from product cards

        # 3. Keyword matching
        query_terms = query.lower().split()
        matching_products = []

        for product in products:
            product_text = product["name"] + " " + product["full_text"]
            matches = sum(1 for term in query_terms if term in product_text.lower())
            if matches > 0:
                product["match_score"] = matches
                matching_products.append(product)

        # 4. Sort by match score and return top 10
        return sorted(matching_products, key=lambda x: x["match_score"], reverse=True)[:10]
```

This simulates how a user would manually browse products and look for keywords.

### 8. Statistical Analysis

For each metric, calculate:
- **Mean**: Average across all queries
- **Median**: Middle value (less affected by outliers)
- **Standard Deviation**: Consistency of performance
- **Min/Max**: Best and worst cases

Run each query 3 times to account for variance, then use the median result.

### 9. Output Files

The benchmark produces JSON results files in `benchmarking/results/`:

```json
{
  "benchmark_type": "hybrid_rag_comparison",
  "timestamp": "2024-12-06T...",
  "source": "default queries",
  "total_queries": 5,
  "summary": {
    "semantic_search": {
      "type": "hybrid_rag",
      "success": 5,
      "failed": 0,
      "avg_latency_ms": 2450,
      "avg_results": 10,
      "retrieval_quality": {"relevance": 4.6, "coverage": 4.4, "precision": 4.2},
      "response_quality": {"accuracy": 4.4, "hallucination": 4.6, "helpfulness": 4.2, "completeness": 4.4}
    },
    "keyword_search": {
      "type": "keyword",
      "success": 5,
      "failed": 0,
      "avg_latency_ms": 1200,
      "avg_results": 4.2,
      "retrieval_quality": {"relevance": 3.2, "coverage": 2.8, "precision": 3.0},
      "response_quality": {"accuracy": 3.6, "hallucination": 3.8, "helpfulness": 3.4, "completeness": 3.2}
    },
    "winner": {
      "semantic_wins": 9,
      "keyword_wins": 0,
      "overall": "semantic"
    }
  },
  "results": [...]
}
```

### 10. Benchmarking Files

| File | Description |
|------|-------------|
| `benchmark_runner.py` | Main benchmark script with Hybrid RAG + dual evaluation |
| `comparison_report.py` | Generates formatted reports from JSON results |
| `llm_evaluator.py` | Standalone LLM evaluation script |
| `queries.json` | Default test queries (50 queries, 6 categories) |
| `results/` | Output directory for benchmark results |

### 11. Next Steps

1. **Quick test**: `python benchmarking/benchmark_runner.py --sample 5 --evaluate`
2. **Full benchmark**: `python benchmarking/benchmark_runner.py --full --evaluate`
3. **Generate report**: `python benchmarking/comparison_report.py benchmarking/results/benchmark_*.json`
4. **Document findings** for hackathon presentation

## Troubleshooting

### MeTTa/Hyperon not available
```
Error: No module named 'hyperon'
```
**Solution**: Run from WSL or Linux. Hyperon doesn't have Windows binaries.

### Selenium WebDriver issues
```
Error: ChromeDriver not found
```
**Solution**: `pip install webdriver-manager` and ensure Chrome is installed.

### ASI_ONE_API_KEY not found
```
Error: ASI_ONE_API_KEY not found in .env file
```
**Solution**: Create `.env` file with `ASI_ONE_API_KEY=your_key_here`
