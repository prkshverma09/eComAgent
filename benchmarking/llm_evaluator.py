#!/usr/bin/env python3
"""
LLM-based Response Evaluator

Uses an LLM to automatically score benchmark responses on:
- Accuracy: Does the response match the product data?
- Relevance: Are the returned products relevant to the query?
- Hallucination: Does the response invent facts not in the data?
- Completeness: Does it answer all aspects of the query?

Usage:
    python llm_evaluator.py benchmarking/results/full_benchmark_*.json
    python llm_evaluator.py benchmarking/results/full_benchmark_*.json --sample 10
"""

import json
import argparse
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class LLMEvaluator:
    """Evaluates benchmark responses using LLM-as-judge"""

    EVALUATION_PROMPT = """You are an expert evaluator for an e-commerce product search system.
Your task is to evaluate the quality of a search response.

## User Query
{query}

## System Response
{response}

## Product Data Retrieved (Context given to the system)
{product_context}

## Evaluation Criteria

Score each dimension from 1-5:

### 1. ACCURACY (1-5)
Does the response accurately represent the product data?
- 5: All facts match the product data exactly
- 4: Minor discrepancies that don't affect usefulness
- 3: Some inaccuracies but mostly correct
- 2: Multiple significant errors
- 1: Mostly incorrect or misleading

### 2. RELEVANCE (1-5)
Are the products and response relevant to what the user asked?
- 5: Perfectly addresses the user's needs
- 4: Highly relevant with minor gaps
- 3: Moderately relevant
- 2: Somewhat relevant but misses key aspects
- 1: Not relevant to the query

### 3. HALLUCINATION (1-5, where 5 = NO hallucination)
Does the response stick to facts from the product data?
- 5: No invented information, all facts verifiable
- 4: Very minor additions that are reasonable inferences
- 3: Some information not in the data but plausible
- 2: Notable invented details
- 1: Significant fabrication of facts

### 4. COMPLETENESS (1-5)
Does the response fully address the query?
- 5: Comprehensive answer covering all aspects
- 4: Good coverage with minor omissions
- 3: Addresses main points but misses some details
- 2: Partial answer, significant gaps
- 1: Fails to address the query adequately

### 5. HELPFULNESS (1-5)
How useful would this response be to a real shopper?
- 5: Extremely helpful, would lead to purchase decision
- 4: Very helpful, provides good guidance
- 3: Moderately helpful
- 2: Limited helpfulness
- 1: Not helpful at all

## Response Format
Respond ONLY with valid JSON in this exact format:
{{
    "accuracy": <1-5>,
    "relevance": <1-5>,
    "hallucination": <1-5>,
    "completeness": <1-5>,
    "helpfulness": <1-5>,
    "overall": <1-5>,
    "reasoning": "<brief explanation of scores>"
}}
"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ASI_ONE_API_KEY")
        if not self.api_key:
            raise ValueError("ASI_ONE_API_KEY not found in environment")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.asi1.ai/v1"
        )
        self.model = "asi1-mini"

    def evaluate_response(self, query: str, response: str, products: List[Dict],
                          max_retries: int = 3) -> Optional[Dict]:
        """Evaluate a single response using LLM"""

        # Build product context string
        product_context = self._format_product_context(products)

        # Build prompt
        prompt = self.EVALUATION_PROMPT.format(
            query=query,
            response=response,
            product_context=product_context
        )

        for attempt in range(max_retries):
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert evaluator. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,  # Low temperature for consistent scoring
                    max_tokens=500
                )

                result_text = completion.choices[0].message.content.strip()

                # Parse JSON from response
                # Handle potential markdown code blocks
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0]
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0]

                scores = json.loads(result_text)

                # Validate scores
                required_keys = ["accuracy", "relevance", "hallucination", "completeness", "helpfulness"]
                for key in required_keys:
                    if key not in scores:
                        scores[key] = 3  # Default to middle score if missing
                    scores[key] = max(1, min(5, int(scores[key])))  # Clamp to 1-5

                # Calculate overall if not provided
                if "overall" not in scores:
                    scores["overall"] = round(sum(scores[k] for k in required_keys) / len(required_keys), 1)

                return scores

            except json.JSONDecodeError as e:
                print(f"  JSON parse error (attempt {attempt + 1}): {e}")
                time.sleep(1)
            except Exception as e:
                print(f"  API error (attempt {attempt + 1}): {e}")
                time.sleep(2)

        return None

    def _format_product_context(self, products: List[Dict], max_products: int = 5) -> str:
        """Format product data for evaluation prompt"""
        if not products:
            return "No products retrieved"

        lines = []
        for i, product in enumerate(products[:max_products], 1):
            context = product.get("context", "")
            if context:
                lines.append(f"Product {i}:\n{context}\n")

        return "\n".join(lines) if lines else "No product context available"


class BenchmarkEvaluator:
    """Orchestrates evaluation of benchmark results"""

    def __init__(self, results_file: str):
        self.results_file = Path(results_file)

        with open(self.results_file, 'r') as f:
            self.data = json.load(f)

        self.results = self.data.get("results", [])
        self.evaluator = LLMEvaluator()
        self.scores = []

    def run_evaluation(self, sample_size: int = None, skip_existing: bool = True):
        """Run LLM evaluation on all results"""

        results_to_eval = self.results
        if sample_size:
            results_to_eval = self.results[:sample_size]

        total = len(results_to_eval)
        print(f"\n{'='*70}")
        print(f"STARTING LLM EVALUATION: {total} queries")
        print(f"{'='*70}\n")

        try:
            from tqdm import tqdm
            pbar = tqdm(results_to_eval, desc="Evaluating", unit="query")
        except ImportError:
            pbar = results_to_eval
            print("(Install tqdm for progress bar: pip install tqdm)")

        successful = 0
        failed = 0

        for i, result in enumerate(pbar):
            query = result.get("query", "")
            # Support both old (agentfabric) and new (semantic) formats
            af = result.get("semantic", result.get("agentfabric", {}))
            response = af.get("response", "")
            products = af.get("products", [])

            if not response:
                failed += 1
                continue

            # Update progress bar description
            if hasattr(pbar, 'set_postfix'):
                pbar.set_postfix({"success": successful, "failed": failed})

            # Evaluate
            scores = self.evaluator.evaluate_response(query, response, products)

            if scores:
                self.scores.append({
                    "query_id": f"q{i+1}",
                    "query": query,
                    "system": "semantic",
                    "latency_ms": af.get("latency_ms", 0),
                    **scores
                })
                successful += 1
            else:
                failed += 1
                self.scores.append({
                    "query_id": f"q{i+1}",
                    "query": query,
                    "system": "semantic",
                    "evaluation_failed": True
                })

            # Small delay to avoid rate limiting
            time.sleep(0.5)

        print(f"\n\nEvaluation complete: {successful} successful, {failed} failed")
        return self.scores

    def save_scores(self, output_file: str = None):
        """Save evaluation scores to JSON"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.results_file.parent / f"evaluation_{timestamp}.json"

        evaluation_data = {
            "source_file": str(self.results_file.name),
            "timestamp": datetime.now().isoformat(),
            "total_evaluated": len(self.scores),
            "scores": self.scores,
            "summary": self.calculate_summary()
        }

        with open(output_file, 'w') as f:
            json.dump(evaluation_data, f, indent=2)

        print(f"\nScores saved to: {output_file}")
        return output_file

    def calculate_summary(self) -> Dict:
        """Calculate summary statistics"""
        valid_scores = [s for s in self.scores if not s.get("evaluation_failed")]

        if not valid_scores:
            return {"error": "No valid scores"}

        metrics = ["accuracy", "relevance", "hallucination", "completeness", "helpfulness", "overall"]
        summary = {}

        for metric in metrics:
            values = [s[metric] for s in valid_scores if metric in s]
            if values:
                summary[metric] = {
                    "mean": round(sum(values) / len(values), 2),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }

        # Calculate percentages (out of 5)
        summary["percentages"] = {
            metric: round((summary[metric]["mean"] / 5) * 100, 1)
            for metric in metrics if metric in summary
        }

        return summary

    def print_summary(self):
        """Print evaluation summary to console"""
        summary = self.calculate_summary()

        print(f"\n{'='*70}")
        print("EVALUATION SUMMARY")
        print(f"{'='*70}")
        print(f"Total Evaluated: {len(self.scores)}")

        valid = [s for s in self.scores if not s.get("evaluation_failed")]
        failed = [s for s in self.scores if s.get("evaluation_failed")]
        print(f"Successful: {len(valid)}")
        print(f"Failed: {len(failed)}")

        if "percentages" in summary:
            print(f"\n{'─'*70}")
            print("QUALITY SCORES (out of 100%)")
            print(f"{'─'*70}")

            for metric, pct in summary["percentages"].items():
                bar_length = int(pct / 5)
                bar = "█" * bar_length + "░" * (20 - bar_length)
                print(f"  {metric.capitalize():<15} {bar} {pct}%")

        print(f"\n{'─'*70}")
        print("DETAILED SCORES (1-5 scale)")
        print(f"{'─'*70}")
        print(f"{'Metric':<15} {'Mean':>8} {'Min':>6} {'Max':>6}")
        print(f"{'-'*40}")

        for metric in ["accuracy", "relevance", "hallucination", "completeness", "helpfulness", "overall"]:
            if metric in summary:
                s = summary[metric]
                print(f"{metric.capitalize():<15} {s['mean']:>8.2f} {s['min']:>6} {s['max']:>6}")

        # Interpretation
        print(f"\n{'─'*70}")
        print("INTERPRETATION")
        print(f"{'─'*70}")

        if "hallucination" in summary:
            hall_score = summary["hallucination"]["mean"]
            if hall_score >= 4.5:
                print("  Hallucination: EXCELLENT - System sticks to facts")
            elif hall_score >= 3.5:
                print("  Hallucination: GOOD - Minor invented details")
            elif hall_score >= 2.5:
                print("  Hallucination: MODERATE - Some fabrication detected")
            else:
                print("  Hallucination: POOR - Significant fabrication issues")

        if "accuracy" in summary:
            acc_score = summary["accuracy"]["mean"]
            if acc_score >= 4.5:
                print("  Accuracy: EXCELLENT - Highly accurate responses")
            elif acc_score >= 3.5:
                print("  Accuracy: GOOD - Generally accurate")
            elif acc_score >= 2.5:
                print("  Accuracy: MODERATE - Some inaccuracies")
            else:
                print("  Accuracy: POOR - Many errors detected")

        if "relevance" in summary:
            rel_score = summary["relevance"]["mean"]
            if rel_score >= 4.5:
                print("  Relevance: EXCELLENT - Highly relevant results")
            elif rel_score >= 3.5:
                print("  Relevance: GOOD - Mostly relevant")
            elif rel_score >= 2.5:
                print("  Relevance: MODERATE - Partially relevant")
            else:
                print("  Relevance: POOR - Often irrelevant")


def main():
    parser = argparse.ArgumentParser(description="Evaluate benchmark results using LLM")
    parser.add_argument("results_file", help="Path to benchmark results JSON")
    parser.add_argument("--sample", "-s", type=int, help="Only evaluate first N results")
    parser.add_argument("--output", "-o", help="Output file for scores")

    args = parser.parse_args()

    evaluator = BenchmarkEvaluator(args.results_file)
    evaluator.run_evaluation(sample_size=args.sample)
    evaluator.print_summary()
    evaluator.save_scores(args.output)


if __name__ == "__main__":
    main()
