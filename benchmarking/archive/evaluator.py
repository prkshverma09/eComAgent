#!/usr/bin/env python3
"""
ARCHIVED: 2024-12-06

This file has been moved to archive/ because it is no longer needed.

REASON FOR ARCHIVAL:
--------------------
This was an early manual scoring evaluator that used hardcoded rules to evaluate
benchmark results. It has been superseded by:

1. benchmark_runner.py - Now includes built-in LLM-based evaluation using the
   LLMEvaluator class which provides:
   - Dual evaluation (Retrieval Quality + Response Quality)
   - LLM-as-judge scoring (more accurate than rule-based)
   - Fair comparison (same LLM evaluates both systems)

2. llm_evaluator.py - Standalone LLM evaluator for post-hoc evaluation

This file used:
- Manual rule-based scoring (less accurate)
- Old JSON format with "agentfabric" and "website" keys
- Separate evaluation step (now integrated into benchmark_runner.py)

To run benchmarks with evaluation, use:
    python benchmarking/benchmark_runner.py --sample 5 --evaluate

Original Description:
--------------------
Evaluator: Scores benchmark results for hallucinations, accuracy, and relevance

This script evaluates responses from both AgentFabric and traditional search,
scoring them on multiple metrics to determine which system performs better.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class EvaluationScore:
    """Scores for a single query response"""
    query_id: str
    query: str
    system: str  # "agentfabric" or "website"

    # Primary metrics
    hallucination_score: int  # 0-3 (0=none, 3=complete hallucination)
    accuracy_score: int  # 0-5 (5=perfect accuracy)
    relevance_score: int  # 0-5 (5=perfectly relevant)

    # Secondary metrics
    completeness_score: float  # 0.0-1.0
    precision_at_5: float  # 0.0-1.0
    latency_ms: int

    # Details
    notes: str = ""
    hallucination_details: List[str] = None
    missing_info: List[str] = None

    def __post_init__(self):
        if self.hallucination_details is None:
            self.hallucination_details = []
        if self.missing_info is None:
            self.missing_info = []

    @property
    def hallucination_rate(self) -> float:
        """Convert hallucination score to percentage"""
        return (self.hallucination_score / 3.0) * 100

    @property
    def accuracy_percentage(self) -> float:
        """Convert accuracy score to percentage"""
        return (self.accuracy_score / 5.0) * 100

    @property
    def relevance_percentage(self) -> float:
        """Convert relevance score to percentage"""
        return (self.relevance_score / 5.0) * 100


class ResponseEvaluator:
    """Evaluates search responses against ground truth"""

    def __init__(self, ground_truth_file: Optional[str] = None):
        """
        Initialize evaluator

        Args:
            ground_truth_file: Path to JSON file with expected products
        """
        self.ground_truth = {}

        if ground_truth_file and Path(ground_truth_file).exists():
            with open(ground_truth_file, 'r') as f:
                self.ground_truth = json.load(f)

    def evaluate_agentfabric_response(
        self,
        query: str,
        query_id: str,
        response_data: Dict,
        expected_products: Optional[List] = None
    ) -> EvaluationScore:
        """
        Evaluate an AgentFabric response

        Args:
            query: The user query
            query_id: Query identifier
            response_data: Response from AgentFabric
            expected_products: List of expected product matches

        Returns:
            EvaluationScore with all metrics
        """

        # Check if query was successful
        if not response_data.get("success"):
            return EvaluationScore(
                query_id=query_id,
                query=query,
                system="agentfabric",
                hallucination_score=0,
                accuracy_score=0,
                relevance_score=0,
                completeness_score=0.0,
                precision_at_5=0.0,
                latency_ms=response_data.get("latency_ms", -1),
                notes=f"Query failed: {response_data.get('error', 'Unknown error')}"
            )

        products = response_data.get("products", [])
        response_text = response_data.get("response", "")
        latency = response_data.get("latency_ms", -1)

        # Evaluate hallucinations (0-3 scale)
        hallucination_score, hallucination_details = self._detect_hallucinations(
            response_text, products, expected_products
        )

        # Evaluate accuracy (0-5 scale)
        accuracy_score = self._evaluate_accuracy(products, expected_products)

        # Evaluate relevance (0-5 scale)
        relevance_score = self._evaluate_relevance(query, products, response_text)

        # Evaluate completeness (0.0-1.0)
        completeness_score = self._evaluate_completeness(products, expected_products)

        # Calculate Precision@5
        precision_at_5 = self._calculate_precision_at_k(products, expected_products, k=5)

        return EvaluationScore(
            query_id=query_id,
            query=query,
            system="agentfabric",
            hallucination_score=hallucination_score,
            accuracy_score=accuracy_score,
            relevance_score=relevance_score,
            completeness_score=completeness_score,
            precision_at_5=precision_at_5,
            latency_ms=latency,
            hallucination_details=hallucination_details,
            notes="Manual review recommended" if hallucination_score > 0 else ""
        )

    def evaluate_website_response(
        self,
        query: str,
        query_id: str,
        response_data: Dict,
        expected_products: Optional[List] = None
    ) -> EvaluationScore:
        """
        Evaluate a traditional website search response

        Similar to evaluate_agentfabric_response but adapted for website results
        """

        if not response_data or not response_data.get("success"):
            return EvaluationScore(
                query_id=query_id,
                query=query,
                system="website",
                hallucination_score=0,
                accuracy_score=0,
                relevance_score=0,
                completeness_score=0.0,
                precision_at_5=0.0,
                latency_ms=response_data.get("latency_ms", -1) if response_data else -1,
                notes=f"Query failed: {response_data.get('error', 'Unknown error')}" if response_data else "No response data"
            )

        products = response_data.get("products", [])
        latency = response_data.get("latency_ms", -1)

        # Website search typically has lower hallucination risk (just shows products)
        # but can show irrelevant products
        hallucination_score = 0
        hallucination_details = []

        # Evaluate accuracy based on product relevance
        accuracy_score = self._evaluate_accuracy(products, expected_products)

        # Evaluate relevance
        relevance_score = self._evaluate_relevance(query, products, "")

        # Completeness
        completeness_score = self._evaluate_completeness(products, expected_products)

        # Precision@5
        precision_at_5 = self._calculate_precision_at_k(products, expected_products, k=5)

        return EvaluationScore(
            query_id=query_id,
            query=query,
            system="website",
            hallucination_score=hallucination_score,
            accuracy_score=accuracy_score,
            relevance_score=relevance_score,
            completeness_score=completeness_score,
            precision_at_5=precision_at_5,
            latency_ms=latency
        )

    def _detect_hallucinations(
        self,
        response_text: str,
        products: List,
        expected_products: Optional[List]
    ) -> tuple[int, List[str]]:
        """
        Detect hallucinations in the response

        Returns:
            (hallucination_score, details_list)
            Score: 0=none, 1=minor, 2=major, 3=complete
        """

        hallucinations = []

        # Check 1: Are products mentioned that don't exist?
        # (Would require ground truth product database)

        # Check 2: Are there factual claims without product support?
        # (This is a simplified heuristic - manual review is better)

        if not products and len(response_text) > 100:
            # Long response with no products might be hallucinating
            hallucinations.append("Detailed response provided but no products returned")

        # For now, return conservative score
        # In production, this would check against ground truth database
        if hallucinations:
            return (1, hallucinations)

        return (0, [])

    def _evaluate_accuracy(
        self,
        products: List,
        expected_products: Optional[List]
    ) -> int:
        """
        Evaluate accuracy of returned products (0-5 scale)

        Without expected products, use heuristics:
        - 5: Products returned
        - 3: Few products
        - 0: No products when expected
        """

        if expected_products:
            # Compare against ground truth
            # This would need actual product matching logic
            if not products:
                return 0
            # Placeholder: assume some accuracy if products returned
            return 3

        # Heuristic scoring
        if not products:
            return 0
        elif len(products) >= 3:
            return 4  # Good number of results
        elif len(products) >= 1:
            return 2  # Some results
        else:
            return 0

    def _evaluate_relevance(
        self,
        query: str,
        products: List,
        response_text: str
    ) -> int:
        """
        Evaluate relevance to user query (0-5 scale)

        Uses heuristics:
        - Check if key query terms appear in products
        - Check if response addresses query
        """

        if not products and not response_text:
            return 0

        # Extract key terms from query (simplified)
        query_lower = query.lower()
        key_terms = [
            "trail", "road", "waterproof", "lightweight", "cushioned",
            "carbon", "stability", "minimalist", "wide", "marathon"
        ]

        # Check if query terms appear in product names
        relevant_count = 0
        for product in products[:5]:  # Check top 5
            product_name = product.get("name", "").lower()
            if any(term in query_lower and term in product_name for term in key_terms):
                relevant_count += 1

        if relevant_count >= 4:
            return 5
        elif relevant_count >= 3:
            return 4
        elif relevant_count >= 2:
            return 3
        elif relevant_count >= 1:
            return 2
        elif products:
            return 1
        else:
            return 0

    def _evaluate_completeness(
        self,
        products: List,
        expected_products: Optional[List]
    ) -> float:
        """
        Evaluate completeness of response (0.0-1.0)

        Checks if all necessary information is provided
        """

        if not products:
            return 0.0

        # Check if products have essential fields
        complete_count = 0
        for product in products:
            has_name = bool(product.get("name"))
            has_price = bool(product.get("price"))

            if has_name and has_price:
                complete_count += 1

        if not products:
            return 0.0

        completeness = complete_count / len(products)
        return round(completeness, 2)

    def _calculate_precision_at_k(
        self,
        products: List,
        expected_products: Optional[List],
        k: int = 5
    ) -> float:
        """
        Calculate Precision@K

        Returns fraction of top-K products that are relevant
        """

        if not products:
            return 0.0

        top_k_products = products[:k]

        if not expected_products:
            # Without ground truth, assume all returned products are relevant
            return 1.0

        # With ground truth, check matches
        # (Placeholder - would need actual matching logic)
        relevant_count = len(top_k_products)  # Assume all relevant for now

        precision = relevant_count / min(k, len(top_k_products))
        return round(precision, 2)


def evaluate_benchmark_results(results_file: str, output_file: Optional[str] = None):
    """
    Evaluate a benchmark results file

    Args:
        results_file: Path to benchmark results JSON
        output_file: Path to save evaluation scores (optional)
    """

    print(f"Loading benchmark results from: {results_file}")

    with open(results_file, 'r') as f:
        data = json.load(f)

    results = data.get("results", [])
    evaluator = ResponseEvaluator()

    evaluated_scores = []

    print(f"\nEvaluating {len(results)} query results...")

    for i, result in enumerate(results, 1):
        query = result["query"]
        query_id = result.get("query_id", f"Q{i:03d}")

        print(f"  [{i}/{len(results)}] {query_id}: {query}")

        # Evaluate AgentFabric response
        if "agentfabric" in result:
            agentfabric_score = evaluator.evaluate_agentfabric_response(
                query=query,
                query_id=query_id,
                response_data=result["agentfabric"]
            )
            evaluated_scores.append(asdict(agentfabric_score))

        # Evaluate website response
        if "website" in result and result["website"]:
            website_score = evaluator.evaluate_website_response(
                query=query,
                query_id=query_id,
                response_data=result["website"]
            )
            evaluated_scores.append(asdict(website_score))

    # Save evaluation scores
    if not output_file:
        results_path = Path(results_file)
        output_file = results_path.parent / f"evaluation_{results_path.stem}.json"

    evaluation_data = {
        "source_file": results_file,
        "evaluation_timestamp": datetime.now().isoformat(),
        "total_evaluations": len(evaluated_scores),
        "scores": evaluated_scores
    }

    with open(output_file, 'w') as f:
        json.dump(evaluation_data, f, indent=2)

    print(f"\n✓ Evaluation complete!")
    print(f"✓ Scores saved to: {output_file}")

    # Print summary statistics
    print_evaluation_summary(evaluated_scores)


def print_evaluation_summary(scores: List[Dict]):
    """Print summary statistics of evaluation scores"""

    agentfabric_scores = [s for s in scores if s["system"] == "agentfabric"]
    website_scores = [s for s in scores if s["system"] == "website"]

    print(f"\n{'='*80}")
    print("EVALUATION SUMMARY")
    print(f"{'='*80}")

    for system, system_scores in [("AgentFabric", agentfabric_scores), ("Website", website_scores)]:
        if not system_scores:
            continue

        print(f"\n{system}:")
        print(f"  Total evaluations: {len(system_scores)}")

        # Average metrics
        avg_hallucination = sum(s["hallucination_score"] for s in system_scores) / len(system_scores)
        avg_accuracy = sum(s["accuracy_score"] for s in system_scores) / len(system_scores)
        avg_relevance = sum(s["relevance_score"] for s in system_scores) / len(system_scores)
        avg_completeness = sum(s["completeness_score"] for s in system_scores) / len(system_scores)
        avg_precision = sum(s["precision_at_5"] for s in system_scores) / len(system_scores)
        avg_latency = sum(s["latency_ms"] for s in system_scores) / len(system_scores)

        print(f"  Avg Hallucination Score: {avg_hallucination:.2f}/3 ({avg_hallucination/3*100:.1f}%)")
        print(f"  Avg Accuracy Score: {avg_accuracy:.2f}/5 ({avg_accuracy/5*100:.1f}%)")
        print(f"  Avg Relevance Score: {avg_relevance:.2f}/5 ({avg_relevance/5*100:.1f}%)")
        print(f"  Avg Completeness: {avg_completeness:.2f}")
        print(f"  Avg Precision@5: {avg_precision:.2f}")
        print(f"  Avg Latency: {avg_latency:.0f}ms")


def main():
    parser = argparse.ArgumentParser(description="Evaluate benchmark results")
    parser.add_argument("results_file", help="Path to benchmark results JSON file")
    parser.add_argument("--output", "-o", help="Output file for evaluation scores")

    args = parser.parse_args()

    evaluate_benchmark_results(args.results_file, args.output)


if __name__ == "__main__":
    main()
