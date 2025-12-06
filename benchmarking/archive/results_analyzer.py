#!/usr/bin/env python3
"""
ARCHIVED: 2024-12-06

This file has been moved to archive/ because it is no longer needed.

REASON FOR ARCHIVAL:
--------------------
This was designed to analyze output from the old evaluator.py script. Since
evaluator.py has been archived, this analyzer is also no longer needed.

It has been superseded by:

1. benchmark_runner.py - Now outputs comprehensive results including:
   - Performance metrics (latency, success rate, results count)
   - Retrieval quality scores (relevance, coverage, precision)
   - Response quality scores (accuracy, hallucination, helpfulness, completeness)
   - Winner determination with detailed comparison

2. comparison_report.py - Generates markdown reports from benchmark results with:
   - Executive summary
   - Performance comparison tables
   - Retrieval and response quality visualizations
   - Sample query analysis

This file used:
- Old evaluation format from evaluator.py
- "agentfabric" and "website" terminology (now "semantic" and "keyword")
- Separate analysis step (now integrated into benchmark outputs)

To generate reports, use:
    python benchmarking/comparison_report.py benchmarking/results/benchmark_*.json

Original Description:
--------------------
Results Analyzer: Generates reports and visualizations from benchmark evaluations

Usage:
    python results_analyzer.py evaluation_full_benchmark_20251205.json --summary
    python results_analyzer.py evaluation_*.json --report --output report.md
    python results_analyzer.py evaluation_*.json --visualize
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import statistics


class ResultsAnalyzer:
    """Analyzes evaluation scores and generates reports"""

    def __init__(self, evaluation_file: str):
        self.evaluation_file = Path(evaluation_file)

        with open(self.evaluation_file, 'r') as f:
            self.data = json.load(f)

        self.scores = self.data.get("scores", [])
        self.agentfabric_scores = [s for s in self.scores if s["system"] == "agentfabric"]
        self.website_scores = [s for s in self.scores if s["system"] == "website"]

    def calculate_statistics(self, values: List[float]) -> Dict:
        """Calculate statistical measures"""
        if not values:
            return {
                "mean": 0.0,
                "median": 0.0,
                "std_dev": 0.0,
                "min": 0.0,
                "max": 0.0
            }

        return {
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "min": min(values),
            "max": max(values)
        }

    def get_metric_stats(self, system_scores: List[Dict], metric: str) -> Dict:
        """Get statistics for a specific metric"""
        values = [s[metric] for s in system_scores if s.get(metric) is not None]
        return self.calculate_statistics(values)

    def print_summary(self):
        """Print summary statistics to console"""
        print(f"\n{'='*80}")
        print(f"BENCHMARK RESULTS SUMMARY")
        print(f"{'='*80}")
        print(f"Evaluation file: {self.evaluation_file.name}")
        print(f"Total evaluations: {len(self.scores)}")
        print(f"  AgentFabric: {len(self.agentfabric_scores)}")
        print(f"  Website: {len(self.website_scores)}")

        # AgentFabric statistics
        if self.agentfabric_scores:
            print(f"\n{'─'*80}")
            print("AgentFabric Semantic Search")
            print(f"{'─'*80}")
            self._print_system_stats(self.agentfabric_scores)

        # Website statistics
        if self.website_scores:
            print(f"\n{'─'*80}")
            print("Traditional Website Search")
            print(f"{'─'*80}")
            self._print_system_stats(self.website_scores)

        # Comparison
        if self.agentfabric_scores and self.website_scores:
            print(f"\n{'─'*80}")
            print("Comparison (AgentFabric vs Website)")
            print(f"{'─'*80}")
            self._print_comparison()

    def _print_system_stats(self, scores: List[Dict]):
        """Print statistics for a system"""

        # Hallucination Rate
        hallucination_stats = self.get_metric_stats(scores, "hallucination_score")
        hallucination_rate = (hallucination_stats["mean"] / 3.0) * 100
        print(f"\nHallucination Rate: {hallucination_rate:.1f}%")
        print(f"  Mean score: {hallucination_stats['mean']:.2f}/3")
        print(f"  Range: {hallucination_stats['min']:.1f} - {hallucination_stats['max']:.1f}")

        # Accuracy
        accuracy_stats = self.get_metric_stats(scores, "accuracy_score")
        accuracy_pct = (accuracy_stats["mean"] / 5.0) * 100
        print(f"\nAccuracy: {accuracy_pct:.1f}%")
        print(f"  Mean score: {accuracy_stats['mean']:.2f}/5")
        print(f"  Range: {accuracy_stats['min']:.1f} - {accuracy_stats['max']:.1f}")
        print(f"  Std Dev: {accuracy_stats['std_dev']:.2f}")

        # Relevance
        relevance_stats = self.get_metric_stats(scores, "relevance_score")
        relevance_pct = (relevance_stats["mean"] / 5.0) * 100
        print(f"\nRelevance: {relevance_pct:.1f}%")
        print(f"  Mean score: {relevance_stats['mean']:.2f}/5")
        print(f"  Range: {relevance_stats['min']:.1f} - {relevance_stats['max']:.1f}")

        # Completeness
        completeness_stats = self.get_metric_stats(scores, "completeness_score")
        print(f"\nCompleteness: {completeness_stats['mean']*100:.1f}%")
        print(f"  Mean score: {completeness_stats['mean']:.2f}")

        # Precision@5
        precision_stats = self.get_metric_stats(scores, "precision_at_5")
        print(f"\nPrecision@5: {precision_stats['mean']*100:.1f}%")
        print(f"  Mean score: {precision_stats['mean']:.2f}")

        # Latency
        latency_stats = self.get_metric_stats(scores, "latency_ms")
        print(f"\nLatency: {latency_stats['mean']:.0f}ms (avg)")
        print(f"  Range: {latency_stats['min']:.0f}ms - {latency_stats['max']:.0f}ms")

    def _print_comparison(self):
        """Print side-by-side comparison"""

        metrics = [
            ("Hallucination Rate", "hallucination_score", lambda x: (x/3)*100, "%", True),  # Lower is better
            ("Accuracy", "accuracy_score", lambda x: (x/5)*100, "%", False),
            ("Relevance", "relevance_score", lambda x: (x/5)*100, "%", False),
            ("Completeness", "completeness_score", lambda x: x*100, "%", False),
            ("Precision@5", "precision_at_5", lambda x: x*100, "%", False),
            ("Latency", "latency_ms", lambda x: x, "ms", True)  # Lower is better
        ]

        print(f"\n{'Metric':<20} {'AgentFabric':<15} {'Website':<15} {'Winner':<15}")
        print(f"{'-'*65}")

        for metric_name, metric_key, transform, unit, lower_is_better in metrics:
            af_stats = self.get_metric_stats(self.agentfabric_scores, metric_key)
            ws_stats = self.get_metric_stats(self.website_scores, metric_key)

            af_value = transform(af_stats["mean"])
            ws_value = transform(ws_stats["mean"])

            # Determine winner
            if lower_is_better:
                winner = "AgentFabric" if af_value < ws_value else "Website"
                winner_symbol = "🏆 " if af_value < ws_value else "   "
            else:
                winner = "AgentFabric" if af_value > ws_value else "Website"
                winner_symbol = "🏆 " if af_value > ws_value else "   "

            # Format values
            if unit == "ms":
                af_str = f"{af_value:.0f}{unit}"
                ws_str = f"{ws_value:.0f}{unit}"
            else:
                af_str = f"{af_value:.1f}{unit}"
                ws_str = f"{ws_value:.1f}{unit}"

            print(f"{metric_name:<20} {af_str:<15} {ws_str:<15} {winner_symbol}{winner}")

    def generate_markdown_report(self, output_file: str):
        """Generate detailed markdown report"""

        report_lines = []

        # Header
        report_lines.append("# AgentFabric vs Traditional Search: Benchmark Report\n")
        report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report_lines.append(f"**Source:** {self.evaluation_file.name}\n")

        # Executive Summary
        report_lines.append("## Executive Summary\n")

        if self.agentfabric_scores and self.website_scores:
            # Calculate overall scores
            af_accuracy = (self.get_metric_stats(self.agentfabric_scores, "accuracy_score")["mean"] / 5.0) * 100
            ws_accuracy = (self.get_metric_stats(self.website_scores, "accuracy_score")["mean"] / 5.0) * 100

            af_hallucination = (self.get_metric_stats(self.agentfabric_scores, "hallucination_score")["mean"] / 3.0) * 100
            ws_hallucination = (self.get_metric_stats(self.website_scores, "hallucination_score")["mean"] / 3.0) * 100

            winner = "AgentFabric" if af_accuracy > ws_accuracy else "Website"

            report_lines.append(f"**Overall Winner:** {winner}\n")
            report_lines.append("\n**Key Findings:**\n")
            report_lines.append(f"- AgentFabric achieved {af_accuracy:.1f}% accuracy vs {ws_accuracy:.1f}% for traditional search\n")
            report_lines.append(f"- Hallucination rate: AgentFabric {af_hallucination:.1f}% vs Website {ws_hallucination:.1f}%\n")
            report_lines.append(f"- Total queries evaluated: {len(self.agentfabric_scores)}\n")

        # Metrics Comparison Table
        report_lines.append("\n## Overall Metrics Comparison\n")
        report_lines.append("\n| Metric | AgentFabric | Traditional | Winner |\n")
        report_lines.append("|--------|-------------|-------------|--------|\n")

        metrics = [
            ("Accuracy", "accuracy_score", lambda x: (x/5)*100),
            ("Hallucination Rate", "hallucination_score", lambda x: (x/3)*100),
            ("Relevance", "relevance_score", lambda x: (x/5)*100),
            ("Precision@5", "precision_at_5", lambda x: x*100),
            ("Avg Latency", "latency_ms", lambda x: x)
        ]

        for metric_name, metric_key, transform in metrics:
            if not self.agentfabric_scores or not self.website_scores:
                continue

            af_value = transform(self.get_metric_stats(self.agentfabric_scores, metric_key)["mean"])
            ws_value = transform(self.get_metric_stats(self.website_scores, metric_key)["mean"])

            # Determine winner (lower is better for hallucination and latency)
            if metric_name in ["Hallucination Rate", "Avg Latency"]:
                winner = "AgentFabric" if af_value < ws_value else "Traditional"
            else:
                winner = "AgentFabric" if af_value > ws_value else "Traditional"

            # Format values
            if metric_name == "Avg Latency":
                af_str = f"{af_value:.0f}ms"
                ws_str = f"{ws_value:.0f}ms"
            else:
                af_str = f"{af_value:.1f}%"
                ws_str = f"{ws_value:.1f}%"

            report_lines.append(f"| {metric_name} | {af_str} | {ws_str} | {winner} |\n")

        # Detailed Statistics
        report_lines.append("\n## Detailed Statistics\n")

        if self.agentfabric_scores:
            report_lines.append("\n### AgentFabric Semantic Search\n")
            report_lines.extend(self._generate_system_stats_markdown(self.agentfabric_scores))

        if self.website_scores:
            report_lines.append("\n### Traditional Website Search\n")
            report_lines.extend(self._generate_system_stats_markdown(self.website_scores))

        # Hallucination Examples
        report_lines.append("\n## Hallucination Analysis\n")
        hallucinated_responses = [
            s for s in self.agentfabric_scores
            if s.get("hallucination_score", 0) > 0
        ]

        if hallucinated_responses:
            report_lines.append(f"\n**Total hallucinations detected:** {len(hallucinated_responses)}\n")
            report_lines.append("\n**Examples:**\n")

            for i, response in enumerate(hallucinated_responses[:5], 1):
                report_lines.append(f"\n{i}. **{response['query_id']}:** {response['query']}\n")
                report_lines.append(f"   - Hallucination score: {response['hallucination_score']}/3\n")
                if response.get("hallucination_details"):
                    for detail in response["hallucination_details"]:
                        report_lines.append(f"   - {detail}\n")
        else:
            report_lines.append("\n✓ No hallucinations detected in evaluated responses.\n")

        # Recommendations
        report_lines.append("\n## Recommendations\n")
        report_lines.append("\nBased on the benchmark results:\n")

        if self.agentfabric_scores and self.website_scores:
            af_accuracy = (self.get_metric_stats(self.agentfabric_scores, "accuracy_score")["mean"] / 5.0) * 100
            ws_accuracy = (self.get_metric_stats(self.website_scores, "accuracy_score")["mean"] / 5.0) * 100

            if af_accuracy > ws_accuracy:
                report_lines.append("\n**Use AgentFabric for:**\n")
                report_lines.append("- Complex, multi-attribute queries\n")
                report_lines.append("- Natural language search\n")
                report_lines.append("- Intent-based product discovery\n")
                report_lines.append("\n**Use Traditional Search for:**\n")
                report_lines.append("- Simple keyword matching\n")
                report_lines.append("- When latency is critical (<200ms)\n")
            else:
                report_lines.append("\n**Traditional Search performs better for this dataset.**\n")

        # Write report
        with open(output_file, 'w') as f:
            f.writelines(report_lines)

        print(f"\n✓ Markdown report generated: {output_file}")

    def _generate_system_stats_markdown(self, scores: List[Dict]) -> List[str]:
        """Generate markdown statistics for a system"""

        lines = []

        metrics = [
            ("Hallucination Rate", "hallucination_score", lambda x: (x/3)*100, "%"),
            ("Accuracy", "accuracy_score", lambda x: (x/5)*100, "%"),
            ("Relevance", "relevance_score", lambda x: (x/5)*100, "%"),
            ("Completeness", "completeness_score", lambda x: x*100, "%"),
            ("Precision@5", "precision_at_5", lambda x: x*100, "%"),
            ("Latency", "latency_ms", lambda x: x, "ms")
        ]

        for metric_name, metric_key, transform, unit in metrics:
            stats = self.get_metric_stats(scores, metric_key)
            value = transform(stats["mean"])

            if unit == "ms":
                lines.append(f"- **{metric_name}:** {value:.0f}{unit} (avg), range {transform(stats['min']):.0f}-{transform(stats['max']):.0f}{unit}\n")
            else:
                lines.append(f"- **{metric_name}:** {value:.1f}{unit} (mean: {stats['mean']:.2f})\n")

        return lines

    def show_hallucinations(self):
        """Display all hallucination cases"""

        print(f"\n{'='*80}")
        print("HALLUCINATION ANALYSIS")
        print(f"{'='*80}")

        hallucinated = [s for s in self.scores if s.get("hallucination_score", 0) > 0]

        if not hallucinated:
            print("\n✓ No hallucinations detected!")
            return

        print(f"\nTotal hallucinations: {len(hallucinated)}")
        print(f"\nBy system:")
        af_halluc = [s for s in hallucinated if s["system"] == "agentfabric"]
        ws_halluc = [s for s in hallucinated if s["system"] == "website"]
        print(f"  AgentFabric: {len(af_halluc)}")
        print(f"  Website: {len(ws_halluc)}")

        print(f"\n{'-'*80}")
        print("Detailed Cases:")
        print(f"{'-'*80}")

        for i, case in enumerate(hallucinated, 1):
            print(f"\n{i}. [{case['system'].upper()}] {case['query_id']}: {case['query']}")
            print(f"   Hallucination score: {case['hallucination_score']}/3")
            if case.get("hallucination_details"):
                print(f"   Details:")
                for detail in case["hallucination_details"]:
                    print(f"     - {detail}")
            if case.get("notes"):
                print(f"   Notes: {case['notes']}")


def main():
    parser = argparse.ArgumentParser(description="Analyze benchmark evaluation results")
    parser.add_argument("evaluation_file", help="Path to evaluation JSON file")
    parser.add_argument("--summary", action="store_true", help="Print summary statistics")
    parser.add_argument("--report", action="store_true", help="Generate markdown report")
    parser.add_argument("--output", "-o", help="Output file for report (default: auto-generated)")
    parser.add_argument("--hallucinations", action="store_true", help="Show hallucination cases")

    args = parser.parse_args()

    analyzer = ResultsAnalyzer(args.evaluation_file)

    if args.summary:
        analyzer.print_summary()

    if args.hallucinations:
        analyzer.show_hallucinations()

    if args.report:
        if not args.output:
            eval_path = Path(args.evaluation_file)
            output_file = eval_path.parent / f"report_{eval_path.stem}.md"
        else:
            output_file = args.output

        analyzer.generate_markdown_report(output_file)

    # If no action specified, show summary by default
    if not (args.summary or args.report or args.hallucinations):
        analyzer.print_summary()


if __name__ == "__main__":
    main()
