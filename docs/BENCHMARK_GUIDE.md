# AgentFabric Benchmark Guide

## Overview

The AgentFabric Benchmark Suite compares **Semantic Search (Hybrid RAG)** against **Keyword Search** to validate the hypothesis that AI-powered product search outperforms traditional keyword matching.

This guide explains how to run benchmarks, understand the results, and interpret the evaluation metrics.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [What the Benchmark Does](#what-the-benchmark-does)
3. [How It Works](#how-it-works)
4. [Running Benchmarks](#running-benchmarks)
5. [Understanding Results](#understanding-results)
6. [Evaluation Metrics](#evaluation-metrics)
7. [Output Files](#output-files)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

```bash
# 1. Open WSL terminal (required for MeTTa/Hyperon)
wsl

# 2. Navigate to project directory
cd /mnt/e/Hackathon/UK\ AI\ Agent\ Hackathon\ Ep3/eComAgent

# 3. Activate virtual environment
source venv/bin/activate

# 4. Ensure dependencies are installed
pip install selenium webdriver-manager pandas tqdm python-dotenv openai openpyxl

# 5. Verify ASI_ONE_API_KEY is set in .env file
cat .env | grep ASI_ONE_API_KEY
```

### Run Your First Benchmark

```bash
# Quick test with 5 queries
python benchmarking/benchmark_runner.py --sample 5 --evaluate

# Run with your Excel file (30 questions)
python benchmarking/benchmark_runner.py --question_file "../Sample Consumer Questions.xlsx" --evaluate
```

---

## What the Benchmark Does

The benchmark answers the hackathon task: **"Benchmarking semantic search VS website search (hallucination rate etc)"**

### Systems Being Compared

| System | Technology | How It Works |
|--------|------------|--------------|
| **Semantic Search** | Hybrid RAG (MeTTa + ChromaDB) | Understands intent, finds semantically similar products |
| **Keyword Search** | Website scraping + keyword matching | Matches exact words in product text |

### What Gets Measured

1. **Performance**: Speed, success rate, number of results
2. **Retrieval Quality**: How relevant are the products found?
3. **Response Quality**: How accurate and helpful is the LLM response?
4. **Hallucination Rate**: Does the system invent facts?

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BENCHMARK RUNNER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌──────────────────────────────────────────┐   │
│  │   Query     │    │         SEMANTIC SEARCH                   │   │
│  │  "trail     │───▶│  1. Vector embedding (ChromaDB)          │   │
│  │   shoes     │    │  2. Similarity search (top 10)           │   │
│  │   under     │    │  3. MeTTa knowledge graph enrichment     │   │
│  │   $200"     │    │  4. LLM response generation              │   │
│  └─────────────┘    └──────────────────────────────────────────┘   │
│         │                           │                                │
│         │                           ▼                                │
│         │           ┌──────────────────────────────────────────┐   │
│         │           │         LLM EVALUATOR                     │   │
│         │           │  • Retrieval Quality (relevance, etc.)   │   │
│         │           │  • Response Quality (accuracy, etc.)     │   │
│         │           └──────────────────────────────────────────┘   │
│         │                           │                                │
│         │           ┌──────────────────────────────────────────┐   │
│         └──────────▶│         KEYWORD SEARCH                    │   │
│                     │  1. Scrape website products page         │   │
│                     │  2. Extract product cards                │   │
│                     │  3. Keyword matching on text             │   │
│                     │  4. SAME LLM response generation         │   │
│                     └──────────────────────────────────────────┘   │
│                                     │                                │
│                                     ▼                                │
│                     ┌──────────────────────────────────────────┐   │
│                     │         LLM EVALUATOR                     │   │
│                     │  (Same evaluation for fair comparison)   │   │
│                     └──────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Step-by-Step Process

#### 1. Query Loading
- Loads queries from JSON, Excel, or uses defaults
- Each query represents a real customer shopping question

#### 2. Semantic Search (Hybrid RAG)
```python
# Step 2a: Vector Search
query_embedding = embed("trail shoes under $200")
similar_products = chromadb.search(query_embedding, k=10)

# Step 2b: Knowledge Graph Enrichment (MeTTa)
for product in similar_products:
    full_context = metta.get_full_product_context(product.uuid)
    # Returns: brand, name, price, features, materials, etc.

# Step 2c: LLM Response Generation
response = llm.generate(
    context=full_context,
    query="trail shoes under $200"
)
```

#### 3. Keyword Search
```python
# Step 3a: Scrape Website
driver.get("https://dash-stride-shop.lovable.app/products")
products = scrape_all_product_cards()

# Step 3b: Keyword Matching
query_terms = ["trail", "shoes", "under", "$200"]
matching_products = []
for product in products:
    if any(term in product.text.lower() for term in query_terms):
        matching_products.append(product)

# Step 3c: SAME LLM Response Generation (Fair Comparison)
response = llm.generate(
    context=matching_products,
    query="trail shoes under $200"
)
```

#### 4. Dual Evaluation (LLM-as-Judge)
Both systems are evaluated by the same LLM evaluator:

```python
# Retrieval Evaluation
retrieval_scores = evaluator.evaluate_retrieval(query, products)
# Returns: relevance, coverage, precision (1-5 scale)

# Response Evaluation
response_scores = evaluator.evaluate_response(query, response, products)
# Returns: accuracy, hallucination, helpfulness, completeness (1-5 scale)
```

#### 5. Results Aggregation
- Calculate averages across all queries
- Determine winner for each metric
- Generate overall winner based on total wins

---

## Running Benchmarks

### Command-Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--full` | Run all queries from queries.json | `--full` |
| `--sample N` | Run first N queries (quick testing) | `--sample 5` |
| `--question_file FILE` | Load queries from Excel file | `--question_file "questions.xlsx"` |
| `--category CAT` | Run queries in specific category | `--category attribute_based` |
| `--query "text"` | Run a single query | `--query "waterproof shoes"` |
| `--evaluate` | Enable LLM evaluation | `--evaluate` |
| `--no-keyword` | Skip keyword search (semantic only) | `--no-keyword` |

### Example Commands

```bash
# Quick test (5 queries, with evaluation)
python benchmarking/benchmark_runner.py --sample 5 --evaluate

# Full benchmark with all default queries
python benchmarking/benchmark_runner.py --full --evaluate

# Run with Excel file
python benchmarking/benchmark_runner.py --question_file "../Sample Consumer Questions.xlsx" --evaluate

# Run specific category
python benchmarking/benchmark_runner.py --category attribute_based --evaluate

# Single query test
python benchmarking/benchmark_runner.py --query "best trail running shoes for beginners" --evaluate

# Semantic search only (no keyword comparison)
python benchmarking/benchmark_runner.py --sample 10 --evaluate --no-keyword
```

### Running with Sample Consumer Questions

To run the benchmark with your Excel file containing 30 consumer questions:

```bash
cd /mnt/e/Hackathon/UK\ AI\ Agent\ Hackathon\ Ep3/eComAgent

source venv/bin/activate

python benchmarking/benchmark_runner.py \
    --question_file "../Sample Consumer Questions.xlsx" \
    --evaluate
```

This will:
1. Load all 30 questions from the Excel file
2. Run each query through both search systems
3. Evaluate retrieval and response quality
4. Save results to `benchmarking/results/benchmark_YYYYMMDD_HHMMSS.json`

---

## Understanding Results

### Console Output

When you run the benchmark, you'll see output like this:

```
======================================================================
BENCHMARK RESULTS
======================================================================

======================================================================
1. PERFORMANCE COMPARISON
======================================================================

Metric                    Semantic (Hybrid RAG)  Keyword Search
-------------------------------------------------------------------
Success Rate              30/30 (100.0%)         30/30 (100.0%)
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

### Interpreting the Scores

| Score | Meaning |
|-------|---------|
| 5.0/5 | Excellent - Perfect performance |
| 4.0-4.9/5 | Good - Minor issues |
| 3.0-3.9/5 | Moderate - Some problems |
| 2.0-2.9/5 | Poor - Significant issues |
| 1.0-1.9/5 | Very Poor - Major failures |

---

## Evaluation Metrics

### Retrieval Quality Metrics

| Metric | What It Measures | Example |
|--------|------------------|---------|
| **Relevance** | Are products relevant to the query? | Query: "waterproof shoes" → Are returned shoes actually waterproof? |
| **Coverage** | Do results cover user's needs? | Does it show variety (different brands, price points)? |
| **Precision** | Are ALL results relevant? | If 10 results returned, are all 10 relevant or are some irrelevant? |

### Response Quality Metrics

| Metric | What It Measures | Example |
|--------|------------------|---------|
| **Accuracy** | Does response match product data? | If response says "$150", is that the actual price? |
| **Hallucination** | Does it invent facts? | Does it claim features not in the product data? (5 = no hallucination) |
| **Helpfulness** | Would this help a real shopper? | Does it answer the question and guide purchase decision? |
| **Completeness** | Does it fully answer the query? | If asked for "under $200", does it mention prices? |

### Why Hallucination Matters

Hallucination is critical for e-commerce because:
- **False product claims** → Customer complaints, returns
- **Wrong prices** → Lost trust, legal issues
- **Incorrect availability** → Frustrated customers
- **Made-up features** → Product liability concerns

A score of 5/5 on hallucination means the system sticks to facts from the product database.

---

## Output Files

### Results Location

All results are saved to: `benchmarking/results/`

### File Format

Results are saved as JSON with this structure:

```json
{
  "benchmark_type": "hybrid_rag_comparison",
  "timestamp": "2024-12-06T12:00:00",
  "source": "Excel: Sample Consumer Questions.xlsx",
  "total_queries": 30,
  "summary": {
    "semantic_search": {
      "type": "hybrid_rag",
      "success": 30,
      "failed": 0,
      "avg_latency_ms": 2450,
      "avg_results": 10.0,
      "retrieval_quality": {
        "relevance": 4.6,
        "coverage": 4.4,
        "precision": 4.2
      },
      "response_quality": {
        "accuracy": 4.4,
        "hallucination": 4.6,
        "helpfulness": 4.2,
        "completeness": 4.4
      }
    },
    "keyword_search": {
      "type": "keyword",
      "success": 30,
      "failed": 0,
      "avg_latency_ms": 1200,
      "avg_results": 4.2,
      "retrieval_quality": {
        "relevance": 3.2,
        "coverage": 2.8,
        "precision": 3.0
      },
      "response_quality": {
        "accuracy": 3.6,
        "hallucination": 3.8,
        "helpfulness": 3.4,
        "completeness": 3.2
      }
    },
    "winner": {
      "semantic_wins": 9,
      "keyword_wins": 0,
      "overall": "semantic"
    }
  },
  "results": [
    {
      "query_id": "Q001",
      "query": "What are the best trail running shoes under $200?",
      "category": "custom",
      "semantic": { ... },
      "keyword": { ... }
    }
  ]
}
```

### Generating Reports

To generate a markdown report from results:

```bash
python benchmarking/comparison_report.py benchmarking/results/benchmark_*.json
```

This creates a `comparison_report_YYYYMMDD_HHMMSS.md` file with:
- Executive summary
- Performance comparison tables
- Visual bar charts
- Sample query analysis
- Conclusions

---

## Troubleshooting

### Common Issues

#### 1. "No module named 'hyperon'"

```
ModuleNotFoundError: No module named 'hyperon'
```

**Cause**: Hyperon/MeTTa doesn't have Windows binaries.

**Solution**: Run from WSL:
```bash
wsl
cd /mnt/e/Hackathon/UK\ AI\ Agent\ Hackathon\ Ep3/eComAgent
source venv/bin/activate
```

#### 2. "ASI_ONE_API_KEY not found"

```
ValueError: ASI_ONE_API_KEY not found in .env file
```

**Solution**: Create or update `.env` file:
```bash
echo "ASI_ONE_API_KEY=your_key_here" >> .env
```

#### 3. "ChromeDriver not found"

```
WebDriverException: ChromeDriver not found
```

**Solution**: Install Chrome and webdriver-manager:
```bash
pip install webdriver-manager
# Also ensure Google Chrome is installed on your system
```

#### 4. "No results from keyword search"

**Cause**: Website structure may have changed or Selenium can't find products.

**Solution**: Run debug script:
```bash
python benchmarking/debug_website.py
```

#### 5. Excel file not loading correctly

**Cause**: Column header format issue.

**Solution**: The benchmark auto-detects if the first row is a question. Ensure your Excel file has questions in the first column.

### Getting Help

If you encounter issues:
1. Check the console output for specific error messages
2. Review the results JSON file for failed queries
3. Run with `--sample 1` to test a single query first
4. Check that all dependencies are installed

---

## Summary

The AgentFabric Benchmark Suite provides a comprehensive, fair comparison between semantic search and keyword search. By using:

- **Hybrid RAG** (MeTTa + ChromaDB) for semantic understanding
- **LLM-as-Judge** for unbiased evaluation
- **Same LLM** for response generation in both systems

The benchmark validates that AI-powered semantic search delivers:
- Higher relevance scores
- Lower hallucination rates
- Better customer experience
- More helpful product recommendations

This directly supports the hackathon goal of demonstrating that LLM-ready product data improves e-commerce search quality.
