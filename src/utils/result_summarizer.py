"""
Result Summarization Engine
Converts raw query results to statistical summaries (BigQuery AI style)
This ensures LLM never sees individual records, only aggregates
"""
from typing import Dict, List, Any, Optional
from src.utils.pii_detector import PIIDetector
from src.utils.logger import logger


class ResultSummarizer:
    """
    Summarizes query results to protect PII
    Based on BigQuery AI security model
    """

    @staticmethod
    def summarize(
        results: List[Dict],
        query_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create statistical summary of query results

        Args:
            results: Raw query results
            query_metadata: Optional metadata about the query

        Returns:
            Statistical summary safe for LLM consumption
        """
        if not results:
            return {
                "status": "no_results",
                "message": "Query returned no results"
            }

        # Detect if results are already aggregated
        is_aggregated = ResultSummarizer._is_aggregated_result(results)

        summary = {
            "total_rows": len(results),
            "columns": list(results[0].keys()),
            "data_type": "aggregated" if is_aggregated else "detailed",
        }

        if is_aggregated:
            # Safe to show aggregated results (top entries)
            summary["analysis_type"] = "aggregated_query"
            summary["top_entries"] = ResultSummarizer._get_top_entries(results)
            summary["value_ranges"] = ResultSummarizer._calculate_ranges(results)
            summary["total_values"] = ResultSummarizer._calculate_totals(results)

        else:
            # Detailed results - only send statistics, NOT raw values
            summary["analysis_type"] = "detailed_query"
            summary["statistics"] = ResultSummarizer._extract_statistics(results)
            summary["distributions"] = ResultSummarizer._calculate_distributions(results)
            # ❌ Individual row values NOT included for privacy

        logger.info(
            f"Summarized {len(results)} rows into {summary['data_type']} summary"
        )

        return summary

    @staticmethod
    def _is_aggregated_result(results: List[Dict]) -> bool:
        """
        Detect if results are aggregated (GROUP BY with aggregations)

        Indicators of aggregation:
        - Small result set (< 1000 rows)
        - Columns with aggregate names (count, sum, avg, total, revenue)
        - No PII columns in results
        """
        if len(results) > 1000:
            return False  # Likely detailed results

        # Check for aggregate function names in columns
        aggregate_indicators = [
            'count', 'sum', 'avg', 'total', 'revenue', 'amount',
            'percentage', 'pct', 'min', 'max', 'orders'
        ]

        columns = results[0].keys()
        has_aggregate_columns = any(
            any(indicator in col.lower() for indicator in aggregate_indicators)
            for col in columns
        )

        # Check if results contain PII columns
        has_pii = any(
            PIIDetector.classify_column(col) in ["critical", "sensitive"]
            for col in columns
        )

        # Aggregated if has aggregate columns and no raw PII
        return has_aggregate_columns and not has_pii

    @staticmethod
    def _get_top_entries(results: List[Dict], max_entries: int = 5) -> List[Dict]:
        """Get top N entries from aggregated results"""
        return results[:max_entries]

    @staticmethod
    def _calculate_ranges(results: List[Dict]) -> Dict[str, Dict]:
        """Calculate min/max/avg for numeric columns"""
        ranges = {}

        if not results:
            return ranges

        numeric_columns = [
            col for col, val in results[0].items()
            if isinstance(val, (int, float))
        ]

        for col in numeric_columns:
            values = [r[col] for r in results if r.get(col) is not None]
            if values:
                ranges[col] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "count": len(values)
                }

        return ranges

    @staticmethod
    def _calculate_totals(results: List[Dict]) -> Dict[str, Any]:
        """Calculate totals for numeric columns"""
        totals = {}

        if not results:
            return totals

        numeric_columns = [
            col for col, val in results[0].items()
            if isinstance(val, (int, float))
        ]

        for col in numeric_columns:
            values = [r[col] for r in results if r.get(col) is not None]
            if values:
                totals[f"total_{col}"] = sum(values)

        return totals

    @staticmethod
    def _extract_statistics(results: List[Dict]) -> Dict[str, Any]:
        """
        Extract high-level statistics from detailed results
        WITHOUT exposing individual values
        """
        stats = {
            "record_count": len(results),
            "unique_value_counts": {},
            "sample_characteristics": {}
        }

        if not results:
            return stats

        # For each column, calculate unique count
        for col in results[0].keys():
            unique_values = set(r[col] for r in results if r.get(col) is not None)
            stats["unique_value_counts"][col] = len(unique_values)

            # For safe columns, include most common value
            if PIIDetector.classify_column(col) == "safe":
                # Count occurrences
                value_counts = {}
                for r in results:
                    val = r.get(col)
                    if val:
                        value_counts[val] = value_counts.get(val, 0) + 1

                if value_counts:
                    most_common = max(value_counts, key=value_counts.get)
                    stats["sample_characteristics"][col] = {
                        "most_common": most_common,
                        "frequency": value_counts[most_common],
                        "percentage": (value_counts[most_common] / len(results)) * 100
                    }

        return stats

    @staticmethod
    def _calculate_distributions(results: List[Dict]) -> Dict[str, Any]:
        """Calculate value distributions for safe columns"""
        distributions = {}

        if not results:
            return distributions

        safe_columns = [
            col for col in results[0].keys()
            if PIIDetector.classify_column(col) == "safe"
        ]

        for col in safe_columns:
            value_counts = {}
            for r in results:
                val = r.get(col)
                if val:
                    value_counts[val] = value_counts.get(val, 0) + 1

            # Get top 5 values
            top_values = sorted(
                value_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]

            distributions[col] = {
                "top_values": [
                    {"value": val, "count": count, "percentage": (count / len(results)) * 100}
                    for val, count in top_values
                ]
            }

        return distributions

    @staticmethod
    def format_for_llm(summary: Dict[str, Any]) -> str:
        """
        Format summary as text for LLM prompt

        This is what actually gets sent to the LLM - only statistics!
        """
        if summary.get("status") == "no_results":
            return summary.get("message", "No results")

        lines = [f"Query Result Summary ({summary['data_type']} data):"]
        lines.append(f"Total Records: {summary['total_rows']}")

        if summary["data_type"] == "aggregated":
            # Show top entries for aggregated data
            if "top_entries" in summary:
                lines.append("\nTop Results:")
                for i, entry in enumerate(summary["top_entries"], 1):
                    entry_str = ", ".join(f"{k}: {v}" for k, v in entry.items())
                    lines.append(f"  {i}. {entry_str}")

            if "value_ranges" in summary:
                lines.append("\nValue Ranges:")
                for col, ranges in summary["value_ranges"].items():
                    lines.append(
                        f"  {col}: {ranges['min']:.2f} to {ranges['max']:.2f} "
                        f"(avg: {ranges['avg']:.2f})"
                    )

        else:
            # Only statistics for detailed data (NO raw values!)
            if "statistics" in summary:
                stats = summary["statistics"]
                lines.append(f"\nUnique Value Counts:")
                for col, count in stats.get("unique_value_counts", {}).items():
                    lines.append(f"  {col}: {count} unique values")

                if "sample_characteristics" in stats:
                    lines.append(f"\nMost Common Values (safe columns only):")
                    for col, char in stats["sample_characteristics"].items():
                        lines.append(
                            f"  {col}: '{char['most_common']}' "
                            f"({char['percentage']:.1f}% of records)"
                        )

        return "\n".join(lines)


__all__ = ['ResultSummarizer']
