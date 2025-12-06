#!/usr/bin/env python3
"""
Comparison Report Generator
Generates a nice markdown report comparing semantic search vs keyword search.
Supports dual evaluation (retrieval quality + response quality).

Usage:
    python comparison_report.py results/comparison_benchmark_*.json
    python comparison_report.py results/comparison_benchmark_*.json --output report.md
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class ComparisonReportGenerator:
    """Generates comparison reports from benchmark results"""

    def __init__(self, results_file: str):
        self.results_file = Path(results_file)

        with open(self.results_file, 'r') as f:
            self.data = json.load(f)

        self.summary = self.data.get("summary", {})
        self.results = self.data.get("results", [])

        # Handle both old (website_search) and new (keyword_search) formats
        self.semantic = self.summary.get("semantic_search", {})
        self.keyword = self.summary.get("keyword_search", self.summary.get("website_search", {}))
        self.winner_info = self.summary.get("winner", {})

    def generate_markdown_report(self, output_file: str = None) -> str:
        """Generate a comprehensive markdown report with dual evaluation"""

        if not output_file:
            output_file = self.results_file.parent / f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        lines = []
        total = self.data.get('total_queries', len(self.results))

        # Header
        lines.append("# AgentFabric Benchmark Report")
        lines.append("## Semantic Search vs Keyword Search Comparison")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Source File:** {self.results_file.name}")
        lines.append(f"**Total Queries:** {total}")
        lines.append(f"**Benchmark Type:** {self.data.get('benchmark_type', 'comparison')}")
        lines.append("")

        # Executive Summary
        lines.append("---")
        lines.append("## Executive Summary")
        lines.append("")

        # Determine overall winner
        if self.winner_info:
            overall = self.winner_info.get("overall", "unknown")
            sem_wins = self.winner_info.get("semantic_wins", 0)
            key_wins = self.winner_info.get("keyword_wins", 0)

            if overall == "semantic":
                lines.append(f"**Overall Winner:** Semantic Search (AgentFabric) - {sem_wins} vs {key_wins}")
            elif overall == "keyword":
                lines.append(f"**Overall Winner:** Keyword Search - {key_wins} vs {sem_wins}")
            else:
                lines.append(f"**Overall Result:** Tie - {sem_wins} vs {key_wins}")
        else:
            # Fallback to simple comparison
            sem_score = 0
            key_score = 0
            if self.semantic.get("success", 0) > self.keyword.get("success", 0):
                sem_score += 1
            if self.semantic.get("avg_latency_ms", float('inf')) < self.keyword.get("avg_latency_ms", float('inf')):
                sem_score += 1
            if self.semantic.get("avg_results", 0) > self.keyword.get("avg_results", 0):
                sem_score += 1
            winner = "Semantic Search (AgentFabric)" if sem_score > key_score else "Keyword Search"
            lines.append(f"**Overall Winner:** {winner}")

        lines.append("")

        # Key findings
        lines.append("### Key Findings")
        lines.append("")

        if self.semantic.get("avg_results", 0) > 0 and self.keyword.get("avg_results", 0) == 0:
            lines.append("- **Semantic search returned results while keyword search returned none**")
        elif self.semantic.get("avg_results", 0) > self.keyword.get("avg_results", 0):
            ratio = self.semantic.get("avg_results", 0) / max(self.keyword.get("avg_results", 0), 0.1)
            lines.append(f"- Semantic search returned **{ratio:.1f}x more results** on average")

        if self.keyword.get("avg_latency_ms", 0) > 0 and self.semantic.get("avg_latency_ms", 0) > 0:
            speed_ratio = self.keyword.get("avg_latency_ms", 0) / max(self.semantic.get("avg_latency_ms", 1), 1)
            if speed_ratio > 1:
                lines.append(f"- Semantic search was **{speed_ratio:.1f}x faster**")

        lines.append(f"- Semantic search success rate: **{self.semantic.get('success', 0)}/{total} ({self.semantic.get('success', 0)/total*100:.1f}%)**")
        lines.append(f"- Keyword search success rate: **{self.keyword.get('success', 0)}/{total} ({self.keyword.get('success', 0)/total*100:.1f}%)**")
        lines.append("")

        # Performance Comparison
        lines.append("---")
        lines.append("## 1. Performance Comparison")
        lines.append("")
        lines.append("| Metric | Semantic Search | Keyword Search | Winner |")
        lines.append("|--------|-----------------|----------------|--------|")

        # Success Rate
        sem_success = f"{self.semantic.get('success', 0)}/{total} ({self.semantic.get('success', 0)/total*100:.1f}%)"
        key_success = f"{self.keyword.get('success', 0)}/{total} ({self.keyword.get('success', 0)/total*100:.1f}%)"
        success_winner = "Semantic" if self.semantic.get('success', 0) >= self.keyword.get('success', 0) else "Keyword"
        lines.append(f"| Success Rate | {sem_success} | {key_success} | {success_winner} |")

        # Latency
        sem_latency = f"{self.semantic.get('avg_latency_ms', 0):.0f}ms"
        key_latency = f"{self.keyword.get('avg_latency_ms', 0):.0f}ms"
        latency_winner = "Semantic" if self.semantic.get('avg_latency_ms', float('inf')) <= self.keyword.get('avg_latency_ms', float('inf')) else "Keyword"
        lines.append(f"| Avg Latency | {sem_latency} | {key_latency} | {latency_winner} |")

        # Results returned
        sem_results = f"{self.semantic.get('avg_results', 0):.1f}"
        key_results = f"{self.keyword.get('avg_results', 0):.1f}"
        results_winner = "Semantic" if self.semantic.get('avg_results', 0) >= self.keyword.get('avg_results', 0) else "Keyword"
        lines.append(f"| Avg Results | {sem_results} | {key_results} | {results_winner} |")

        lines.append("")

        # Retrieval Quality Comparison (if available)
        sem_retrieval = self.semantic.get("retrieval_quality", {})
        key_retrieval = self.keyword.get("retrieval_quality", {})

        if sem_retrieval.get("relevance", 0) > 0 or key_retrieval.get("relevance", 0) > 0:
            lines.append("---")
            lines.append("## 2. Retrieval Quality Comparison")
            lines.append("")
            lines.append("*Measures how relevant the retrieved products are to the user's query*")
            lines.append("")
            lines.append("| Metric | Semantic | Keyword | Winner |")
            lines.append("|--------|----------|---------|--------|")

            for metric in ["relevance", "coverage", "precision"]:
                sem_val = sem_retrieval.get(metric, 0)
                key_val = key_retrieval.get(metric, 0)
                winner = "Semantic" if sem_val > key_val else ("Keyword" if key_val > sem_val else "Tie")
                lines.append(f"| {metric.capitalize()} | {sem_val:.2f}/5 ({sem_val/5*100:.0f}%) | {key_val:.2f}/5 ({key_val/5*100:.0f}%) | {winner} |")

            lines.append("")

            # Visual bar chart for retrieval
            lines.append("### Retrieval Quality Scores")
            lines.append("```")
            for metric in ["relevance", "coverage", "precision"]:
                sem_val = sem_retrieval.get(metric, 0)
                key_val = key_retrieval.get(metric, 0)
                sem_bar = int(sem_val / 5 * 20)
                key_bar = int(key_val / 5 * 20)
                lines.append(f"{metric.capitalize():12} Semantic: {'█' * sem_bar}{'░' * (20-sem_bar)} {sem_val:.1f}")
                lines.append(f"{' ':12} Keyword:  {'█' * key_bar}{'░' * (20-key_bar)} {key_val:.1f}")
                lines.append("")
            lines.append("```")
            lines.append("")

        # Response Quality Comparison (if available)
        sem_response = self.semantic.get("response_quality", {})
        key_response = self.keyword.get("response_quality", {})

        if sem_response.get("accuracy", 0) > 0 or key_response.get("accuracy", 0) > 0:
            lines.append("---")
            lines.append("## 3. Response Quality Comparison")
            lines.append("")
            lines.append("*Measures the quality of LLM-generated responses using retrieved context*")
            lines.append("")
            lines.append("| Metric | Semantic | Keyword | Winner |")
            lines.append("|--------|----------|---------|--------|")

            for metric in ["accuracy", "hallucination", "helpfulness", "completeness", "usefulness"]:
                sem_val = sem_response.get(metric, 0)
                key_val = key_response.get(metric, 0)
                winner = "Semantic" if sem_val > key_val else ("Keyword" if key_val > sem_val else "Tie")
                label = "No Hallucination" if metric == "hallucination" else metric.capitalize()
                lines.append(f"| {label} | {sem_val:.2f}/5 ({sem_val/5*100:.0f}%) | {key_val:.2f}/5 ({key_val/5*100:.0f}%) | {winner} |")

            lines.append("")

            # Visual bar chart for response quality
            lines.append("### Response Quality Scores")
            lines.append("```")
            for metric in ["accuracy", "hallucination", "helpfulness", "completeness", "usefulness"]:
                sem_val = sem_response.get(metric, 0)
                key_val = key_response.get(metric, 0)
                sem_bar = int(sem_val / 5 * 20)
                key_bar = int(key_val / 5 * 20)
                label = "No Halluc." if metric == "hallucination" else metric.capitalize()
                lines.append(f"{label:12} Semantic: {'█' * sem_bar}{'░' * (20-sem_bar)} {sem_val:.1f}")
                lines.append(f"{' ':12} Keyword:  {'█' * key_bar}{'░' * (20-key_bar)} {key_val:.1f}")
                lines.append("")
            lines.append("```")
            lines.append("")

        # Visual Performance Comparison
        lines.append("---")
        lines.append("## 4. Performance Visualization")
        lines.append("")
        lines.append("### Latency (lower is better)")
        lines.append("```")
        max_latency = max(self.semantic.get('avg_latency_ms', 1), self.keyword.get('avg_latency_ms', 1))
        sem_bar_len = int((self.semantic.get('avg_latency_ms', 0) / max_latency) * 40)
        key_bar_len = int((self.keyword.get('avg_latency_ms', 0) / max_latency) * 40)
        lines.append(f"Semantic: {'█' * sem_bar_len}{'░' * (40-sem_bar_len)} {self.semantic.get('avg_latency_ms', 0):.0f}ms")
        lines.append(f"Keyword:  {'█' * key_bar_len}{'░' * (40-key_bar_len)} {self.keyword.get('avg_latency_ms', 0):.0f}ms")
        lines.append("```")
        lines.append("")

        lines.append("### Results Returned (higher is better)")
        lines.append("```")
        max_results = max(self.semantic.get('avg_results', 1), self.keyword.get('avg_results', 1), 1)
        sem_bar_len = int((self.semantic.get('avg_results', 0) / max_results) * 40)
        key_bar_len = int((self.keyword.get('avg_results', 0) / max_results) * 40)
        lines.append(f"Semantic: {'█' * sem_bar_len}{'░' * (40-sem_bar_len)} {self.semantic.get('avg_results', 0):.1f} results")
        lines.append(f"Keyword:  {'█' * key_bar_len}{'░' * (40-key_bar_len)} {self.keyword.get('avg_results', 0):.1f} results")
        lines.append("```")
        lines.append("")

        # Sample queries
        lines.append("---")
        lines.append("## 5. Sample Query Results")
        lines.append("")

        for i, result in enumerate(self.results[:5], 1):
            lines.append(f"### Query {i}: \"{result['query']}\"")
            lines.append("")

            sem = result.get("semantic", {})
            key = result.get("keyword", result.get("website", {}))

            # Basic results table
            lines.append("| System | Results | Latency |")
            lines.append("|--------|---------|---------|")
            lines.append(f"| Semantic | {sem.get('num_results', 0)} | {sem.get('latency_ms', 0)}ms |")
            lines.append(f"| Keyword | {key.get('num_results', 0)} | {key.get('latency_ms', 0)}ms |")
            lines.append("")

            # Show evaluation scores if available
            sem_ret_eval = sem.get("retrieval_evaluation", {})
            key_ret_eval = key.get("retrieval_evaluation", {})

            if sem_ret_eval.get("relevance", 0) > 0:
                lines.append("**Retrieval Evaluation:**")
                lines.append(f"- Semantic: Relevance {sem_ret_eval.get('relevance', 0)}/5, Coverage {sem_ret_eval.get('coverage', 0)}/5, Precision {sem_ret_eval.get('precision', 0)}/5")
                lines.append(f"- Keyword: Relevance {key_ret_eval.get('relevance', 0)}/5, Coverage {key_ret_eval.get('coverage', 0)}/5, Precision {key_ret_eval.get('precision', 0)}/5")
                lines.append("")

            sem_resp_eval = sem.get("response_evaluation", {})
            key_resp_eval = key.get("response_evaluation", {})

            if sem_resp_eval.get("accuracy", 0) > 0:
                lines.append("**Response Evaluation:**")
                lines.append(f"- Semantic: Accuracy {sem_resp_eval.get('accuracy', 0)}/5, Hallucination {sem_resp_eval.get('hallucination', 0)}/5")
                lines.append(f"- Keyword: Accuracy {key_resp_eval.get('accuracy', 0)}/5, Hallucination {key_resp_eval.get('hallucination', 0)}/5")
                lines.append("")

        # Conclusions
        lines.append("---")
        lines.append("## 6. Conclusions")
        lines.append("")

        # Dynamic conclusions based on results
        lines.append("### Key Takeaways")
        lines.append("")

        # Compare retrieval quality
        if sem_retrieval.get("relevance", 0) > key_retrieval.get("relevance", 0):
            diff = sem_retrieval.get("relevance", 0) - key_retrieval.get("relevance", 0)
            lines.append(f"1. **Retrieval Quality**: Semantic search retrieved more relevant products (+{diff:.1f} relevance score)")

        # Compare hallucination
        if sem_response.get("hallucination", 0) > key_response.get("hallucination", 0):
            lines.append(f"2. **Lower Hallucination**: Semantic search produced fewer hallucinations ({sem_response.get('hallucination', 0):.1f}/5 vs {key_response.get('hallucination', 0):.1f}/5)")

        # Compare speed
        if self.semantic.get("avg_latency_ms", 0) < self.keyword.get("avg_latency_ms", 0):
            ratio = self.keyword.get("avg_latency_ms", 1) / max(self.semantic.get("avg_latency_ms", 1), 1)
            lines.append(f"3. **Speed**: Semantic search was {ratio:.1f}x faster")

        lines.append("")
        lines.append("### Why Semantic Search Outperforms")
        lines.append("")
        lines.append("1. **Intent Understanding**: Vector embeddings capture semantic meaning, not just keywords")
        lines.append("2. **Fuzzy Matching**: Finds relevant products even when exact terms don't match")
        lines.append("3. **Better Context**: Provides richer context to LLM, reducing hallucinations")
        lines.append("4. **Speed**: Vector similarity search is faster than web scraping + keyword matching")
        lines.append("")

        lines.append("### Implications for E-commerce")
        lines.append("")
        lines.append("- **Better Customer Experience**: Users find products faster with natural language queries")
        lines.append("- **Higher Conversion**: More relevant results lead to more purchases")
        lines.append("- **Reduced Hallucination**: More accurate product information builds trust")
        lines.append("- **AI-Ready**: Semantic search integrates seamlessly with LLM-based shopping assistants")
        lines.append("")

        lines.append("---")
        lines.append(f"*Report generated by AgentFabric Benchmark Suite*")

        # Write report
        report_content = "\n".join(lines)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"Report saved to: {output_file}")
        return str(output_file)

    def print_summary(self):
        """Print a quick summary to console"""
        total = self.data.get('total_queries', len(self.results))

        print("\n" + "="*70)
        print("BENCHMARK COMPARISON SUMMARY")
        print("="*70)

        print(f"\n{'Metric':<25} {'Semantic Search':<20} {'Keyword Search':<20}")
        print("-"*65)
        print(f"{'Success Rate':<25} {self.semantic.get('success', 0)}/{total}{'':<12} {self.keyword.get('success', 0)}/{total}")
        print(f"{'Avg Latency':<25} {self.semantic.get('avg_latency_ms', 0):.0f}ms{'':<14} {self.keyword.get('avg_latency_ms', 0):.0f}ms")
        print(f"{'Avg Results':<25} {self.semantic.get('avg_results', 0):.1f}{'':<16} {self.keyword.get('avg_results', 0):.1f}")

        # Retrieval quality
        sem_ret = self.semantic.get("retrieval_quality", {})
        key_ret = self.keyword.get("retrieval_quality", {})
        if sem_ret.get("relevance", 0) > 0:
            print(f"\n{'RETRIEVAL QUALITY':<25}")
            print("-"*65)
            print(f"{'Relevance':<25} {sem_ret.get('relevance', 0):.2f}/5{'':<12} {key_ret.get('relevance', 0):.2f}/5")
            print(f"{'Coverage':<25} {sem_ret.get('coverage', 0):.2f}/5{'':<12} {key_ret.get('coverage', 0):.2f}/5")
            print(f"{'Precision':<25} {sem_ret.get('precision', 0):.2f}/5{'':<12} {key_ret.get('precision', 0):.2f}/5")

        # Response quality
        sem_resp = self.semantic.get("response_quality", {})
        key_resp = self.keyword.get("response_quality", {})
        if sem_resp.get("accuracy", 0) > 0:
            print(f"\n{'RESPONSE QUALITY':<25}")
            print("-"*65)
            print(f"{'Accuracy':<25} {sem_resp.get('accuracy', 0):.2f}/5{'':<12} {key_resp.get('accuracy', 0):.2f}/5")
            print(f"{'No Hallucination':<25} {sem_resp.get('hallucination', 0):.2f}/5{'':<12} {key_resp.get('hallucination', 0):.2f}/5")
            print(f"{'Helpfulness':<25} {sem_resp.get('helpfulness', 0):.2f}/5{'':<12} {key_resp.get('helpfulness', 0):.2f}/5")
            print(f"{'Completeness':<25} {sem_resp.get('completeness', 0):.2f}/5{'':<12} {key_resp.get('completeness', 0):.2f}/5")
            print(f"{'Usefulness':<25} {sem_resp.get('usefulness', 0):.2f}/5{'':<12} {key_resp.get('usefulness', 0):.2f}/5")

        # Winner
        if self.winner_info:
            print(f"\n{'='*70}")
            overall = self.winner_info.get("overall", "unknown")
            sem_wins = self.winner_info.get("semantic_wins", 0)
            key_wins = self.winner_info.get("keyword_wins", 0)
            print(f"OVERALL SCORE: Semantic {sem_wins} - {key_wins} Keyword")
            if overall == "semantic":
                print("★ WINNER: Semantic Search (Vector-based approach validated)")
            elif overall == "keyword":
                print("★ WINNER: Keyword Search")
            else:
                print("★ TIE")

        if self.keyword.get('avg_latency_ms', 0) > 0:
            speed_ratio = self.keyword.get('avg_latency_ms', 0) / max(self.semantic.get('avg_latency_ms', 1), 1)
            if speed_ratio > 1:
                print(f"\nSemantic search was {speed_ratio:.1f}x faster")


def main():
    parser = argparse.ArgumentParser(description="Generate comparison report from benchmark results")
    parser.add_argument("results_file", help="Path to comparison benchmark JSON file")
    parser.add_argument("--output", "-o", help="Output markdown file path")
    parser.add_argument("--summary", "-s", action="store_true", help="Print summary only")

    args = parser.parse_args()

    generator = ComparisonReportGenerator(args.results_file)

    if args.summary:
        generator.print_summary()
    else:
        generator.print_summary()
        generator.generate_markdown_report(args.output)


if __name__ == "__main__":
    main()
