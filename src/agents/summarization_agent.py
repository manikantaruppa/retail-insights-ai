"""
Summarization Agent: Generates automatic executive summaries

NEW: Universal version works with any CSV using dynamic column detection
OLD: Hardcoded version kept for backward compatibility (not used by default)
"""
from typing import Dict, List, Optional
from src.agents.base_agent import BaseAgent
from src.utils.duckdb_manager import db_manager
from src.utils.prompts import SUMMARIZATION_PROMPT
from src.utils.logger import logger


class SummarizationAgent(BaseAgent):
    """
    NEW Universal Summarization Agent
    Works with any CSV using dynamic column mappings
    """

    def __init__(self, column_mapping: Optional[Dict[str, str]] = None):
        """
        Initialize agent with column mapping

        Args:
            column_mapping: Dictionary mapping column types to actual column names
                           e.g., {'categorical': 'Category', 'numeric': 'Amount', 'location': 'ship_state'}
        """
        super().__init__("SummarizationAgent")
        self.column_mapping = column_mapping or {}

    def generate_summary(self) -> tuple[str, Dict]:
        """
        Generate comprehensive summary using dynamic column mapping

        Returns:
            tuple: (summary_text, token_usage)
        """
        try:
            logger.info("Generating dynamic summary with column mapping")

            # Check if we have column mapping
            if not self.column_mapping:
                raise ValueError("Column mapping required for summarization")

            # 1. Get table statistics
            stats = db_manager.get_table_stats()

            # 2. Build and run dynamic queries
            aggregated_data = self._run_dynamic_queries()

            # 3. Format data for prompt
            formatted_data = self._format_aggregated_data(aggregated_data, stats)

            # 4. Generate summary using LLM
            prompt = SUMMARIZATION_PROMPT.format(
                total_records=stats.get('total_rows', 'Unknown'),
                date_range=self._format_date_range(stats.get('date_range', {})),
                data_source="Sales Dataset",
                aggregated_metrics=formatted_data['metrics'],
                top_performers=formatted_data['top_performers'],
                trends=formatted_data['trends']
            )

            summary, token_usage = self.generate_response(
                prompt=prompt,
                temperature=0.4,
                max_tokens=4096  # Increased for comprehensive summaries
            )

            logger.info(f"Dynamic summary generated: {len(summary)} characters")

            return summary.strip(), token_usage

        except Exception as e:
            logger.error(f"Dynamic summary generation failed: {e}")
            raise

    def _run_dynamic_queries(self) -> Dict[str, List[Dict]]:
        """Build and execute queries using column mapping"""
        results = {}

        cat_col = self.column_mapping.get('categorical')
        num_col = self.column_mapping.get('numeric')
        loc_col = self.column_mapping.get('location')
        date_col = self.column_mapping.get('date')

        # Quote column names to handle special characters
        def quote_col(col):
            if col and col != '(None)':
                return f'"{col}"'
            return col

        cat_col_quoted = quote_col(cat_col)
        num_col_quoted = quote_col(num_col)
        loc_col_quoted = quote_col(loc_col)

        # Total revenue (if numeric column exists)
        if num_col and num_col != '(None)':
            query = f"SELECT SUM(TRY_CAST({num_col_quoted} AS DOUBLE)) as total_revenue FROM sales WHERE {num_col_quoted} IS NOT NULL"
            results['total_revenue'] = self._execute_safe(query, 'total_revenue')

        # Total orders
        query = "SELECT COUNT(*) as total_orders FROM sales"
        results['total_orders'] = self._execute_safe(query, 'total_orders')

        # Top categories (if categorical column exists)
        if cat_col and cat_col != '(None)' and num_col and num_col != '(None)':
            query = f"""
                SELECT {cat_col_quoted} as {cat_col},
                       COUNT(*) as orders,
                       SUM(TRY_CAST({num_col_quoted} AS DOUBLE)) as revenue
                FROM sales
                WHERE {cat_col_quoted} IS NOT NULL AND {num_col_quoted} IS NOT NULL
                GROUP BY {cat_col_quoted}
                ORDER BY revenue DESC
                LIMIT 5
            """
            results['top_categories'] = self._execute_safe(query, 'top_categories')

        # Top locations (if location column exists)
        if loc_col and loc_col != '(None)' and num_col and num_col != '(None)':
            query = f"""
                SELECT {loc_col_quoted} as region,
                       COUNT(*) as orders,
                       SUM(TRY_CAST({num_col_quoted} AS DOUBLE)) as revenue
                FROM sales
                WHERE {loc_col_quoted} IS NOT NULL AND {num_col_quoted} IS NOT NULL
                GROUP BY {loc_col_quoted}
                ORDER BY orders DESC
                LIMIT 5
            """
            results['top_regions'] = self._execute_safe(query, 'top_regions')

        # Category breakdown (if categorical exists)
        if cat_col and cat_col != '(None)':
            query = f"""
                SELECT {cat_col_quoted} as {cat_col},
                       COUNT(*) as count,
                       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
                FROM sales
                WHERE {cat_col_quoted} IS NOT NULL
                GROUP BY {cat_col_quoted}
                ORDER BY count DESC
                LIMIT 5
            """
            results['category_breakdown'] = self._execute_safe(query, 'category_breakdown')

        return results

    def _execute_safe(self, query: str, query_name: str) -> List[Dict]:
        """Execute query safely with error handling"""
        try:
            success, data, error = db_manager.execute_query(query)

            if success and data:
                return data
            else:
                logger.warning(f"Query '{query_name}' failed: {error}")
                return []

        except Exception as e:
            logger.error(f"Failed to execute {query_name}: {e}")
            return []

    def _format_aggregated_data(
        self,
        aggregated_data: Dict[str, List[Dict]],
        stats: Dict
    ) -> Dict[str, str]:
        """Format aggregated data for LLM prompt"""

        cat_col = self.column_mapping.get('categorical', 'Category')
        num_col = self.column_mapping.get('numeric', 'Amount')
        loc_col = self.column_mapping.get('location', 'Region')

        # Format metrics
        metrics_parts = []
        if aggregated_data.get('total_revenue'):
            revenue = aggregated_data['total_revenue'][0].get('total_revenue', 0) or 0
            if revenue:
                metrics_parts.append(f"- Total Revenue: ₹{revenue:,.2f}")

        if aggregated_data.get('total_orders'):
            orders = aggregated_data['total_orders'][0].get('total_orders', 0) or 0
            if orders:
                metrics_parts.append(f"- Total Orders: {orders:,}")

        metrics_str = "\n".join(metrics_parts) if metrics_parts else "Metrics unavailable"

        # Format top performers
        performers_parts = []

        if aggregated_data.get('top_categories'):
            performers_parts.append(f"Top {cat_col}s by Revenue:")
            for i, cat in enumerate(aggregated_data['top_categories'][:3], 1):
                name = cat.get(cat_col, 'Unknown')
                revenue = cat.get('revenue', 0) or 0
                orders = cat.get('orders', 0) or 0
                performers_parts.append(f"  {i}. {name}: ₹{revenue:,.0f} ({orders:,} orders)")

        if aggregated_data.get('top_regions'):
            performers_parts.append(f"\nTop {loc_col}s by Orders:")
            for i, region in enumerate(aggregated_data['top_regions'][:3], 1):
                name = region.get('region', 'Unknown')
                orders = region.get('orders', 0) or 0
                revenue = region.get('revenue', 0) or 0
                performers_parts.append(f"  {i}. {name}: {orders:,} orders (₹{revenue:,.0f})")

        performers_str = "\n".join(performers_parts) if performers_parts else "Data unavailable"

        # Format trends
        trends_parts = []

        if aggregated_data.get('category_breakdown'):
            trends_parts.append(f"{cat_col} Distribution:")
            for item in aggregated_data['category_breakdown'][:3]:
                name = item.get(cat_col, 'Unknown')
                count = item.get('count', 0)
                pct = item.get('percentage', 0)
                trends_parts.append(f"  - {name}: {count:,} ({pct:.1f}%)")

        trends_str = "\n".join(trends_parts) if trends_parts else "Trend data unavailable"

        return {
            'metrics': metrics_str,
            'top_performers': performers_str,
            'trends': trends_str
        }

    def _format_date_range(self, date_range: Dict) -> str:
        """Format date range for display"""
        if not date_range:
            return "Unknown"

        min_date = date_range.get('min', 'Unknown')
        max_date = date_range.get('max', 'Unknown')

        return f"{min_date} to {max_date}"


# ============================================================================
# HARDCODED VERSION (Kept for backward compatibility, not used by default)
# ============================================================================

class SummarizationAgent_Hardcoded(BaseAgent):
    """Generates automatic summaries of sales data"""

    # Standard queries for summarization
    STANDARD_QUERIES = {
        'total_revenue': "SELECT SUM(CAST(Amount AS FLOAT)) as total_revenue FROM sales WHERE Amount IS NOT NULL",
        'total_orders': "SELECT COUNT(*) as total_orders FROM sales",
        'order_status': """
            SELECT Status,
                   COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM sales
            GROUP BY Status
            ORDER BY count DESC
        """,
        'top_categories': """
            SELECT Category,
                   COUNT(*) as orders,
                   SUM(CAST(Amount AS FLOAT)) as revenue
            FROM sales
            WHERE Category IS NOT NULL AND Amount IS NOT NULL
            GROUP BY Category
            ORDER BY revenue DESC
            LIMIT 5
        """,
        'top_regions': """
            SELECT ship_state as region,
                   COUNT(*) as orders,
                   SUM(CAST(Amount AS FLOAT)) as revenue
            FROM sales
            WHERE ship_state IS NOT NULL AND Amount IS NOT NULL
            GROUP BY ship_state
            ORDER BY orders DESC
            LIMIT 5
        """,
        'fulfillment_breakdown': """
            SELECT Fulfilment,
                   COUNT(*) as count
            FROM sales
            WHERE Fulfilment IS NOT NULL
            GROUP BY Fulfilment
            ORDER BY count DESC
        """,
    }

    def __init__(self):
        super().__init__("SummarizationAgent")

    def generate_summary(self) -> tuple[str, Dict]:
        """
        Generate comprehensive summary of sales data

        Returns:
            tuple: (summary_text, token_usage)
        """
        try:
            logger.info("Generating automatic summary")

            # 1. Get table statistics
            stats = db_manager.get_table_stats()

            # 2. Run standard analytical queries
            aggregated_data = self._run_standard_queries()

            # 3. Format data for prompt
            formatted_data = self._format_aggregated_data(aggregated_data, stats)

            # 4. Generate summary using LLM
            prompt = SUMMARIZATION_PROMPT.format(
                total_records=stats.get('total_rows', 'Unknown'),
                date_range=self._format_date_range(stats.get('date_range', {})),
                data_source="Amazon Sales Dataset",
                aggregated_metrics=formatted_data['metrics'],
                top_performers=formatted_data['top_performers'],
                trends=formatted_data['trends']
            )

            summary, token_usage = self.generate_response(
                prompt=prompt,
                temperature=0.4,
                max_tokens=4096  # Increased for comprehensive summaries
            )

            logger.info(f"Summary generated: {len(summary)} characters")

            return summary.strip(), token_usage

        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            raise

    def _run_standard_queries(self) -> Dict[str, List[Dict]]:
        """Execute all standard queries"""
        results = {}

        for query_name, sql_query in self.STANDARD_QUERIES.items():
            try:
                success, data, error = db_manager.execute_query(sql_query)

                if success and data:
                    results[query_name] = data
                else:
                    logger.warning(f"Query '{query_name}' failed: {error}")
                    results[query_name] = []

            except Exception as e:
                logger.error(f"Failed to execute {query_name}: {e}")
                results[query_name] = []

        return results

    def _format_aggregated_data(
        self,
        aggregated_data: Dict[str, List[Dict]],
        stats: Dict
    ) -> Dict[str, str]:
        """Format aggregated data for LLM prompt"""

        # Format metrics
        metrics_parts = []
        if aggregated_data.get('total_revenue'):
            revenue = aggregated_data['total_revenue'][0].get('total_revenue', 0)
            metrics_parts.append(f"- Total Revenue: ₹{revenue:,.2f}")

        if aggregated_data.get('total_orders'):
            orders = aggregated_data['total_orders'][0].get('total_orders', 0)
            metrics_parts.append(f"- Total Orders: {orders:,}")

        metrics_str = "\n".join(metrics_parts) if metrics_parts else "Metrics unavailable"

        # Format top performers
        performers_parts = []

        if aggregated_data.get('top_categories'):
            performers_parts.append("Top Categories by Revenue:")
            for i, cat in enumerate(aggregated_data['top_categories'][:3], 1):
                name = cat.get('Category', 'Unknown')
                revenue = cat.get('revenue', 0)
                orders = cat.get('orders', 0)
                performers_parts.append(f"  {i}. {name}: ₹{revenue:,.0f} ({orders:,} orders)")

        if aggregated_data.get('top_regions'):
            performers_parts.append("\nTop Regions by Orders:")
            for i, region in enumerate(aggregated_data['top_regions'][:3], 1):
                name = region.get('region', 'Unknown')
                orders = region.get('orders', 0)
                revenue = region.get('revenue', 0)
                performers_parts.append(f"  {i}. {name}: {orders:,} orders (₹{revenue:,.0f})")

        performers_str = "\n".join(performers_parts) if performers_parts else "Data unavailable"

        # Format trends
        trends_parts = []

        if aggregated_data.get('order_status'):
            trends_parts.append("Order Status Distribution:")
            for status_data in aggregated_data['order_status'][:3]:
                status = status_data.get('Status', 'Unknown')
                count = status_data.get('count', 0)
                pct = status_data.get('percentage', 0)
                trends_parts.append(f"  - {status}: {count:,} ({pct:.1f}%)")

        if aggregated_data.get('fulfillment_breakdown'):
            trends_parts.append("\nFulfillment Methods:")
            for fulfillment in aggregated_data['fulfillment_breakdown'][:3]:
                method = fulfillment.get('Fulfilment', 'Unknown')
                count = fulfillment.get('count', 0)
                trends_parts.append(f"  - {method}: {count:,} orders")

        trends_str = "\n".join(trends_parts) if trends_parts else "Trend data unavailable"

        return {
            'metrics': metrics_str,
            'top_performers': performers_str,
            'trends': trends_str
        }

    def _format_date_range(self, date_range: Dict) -> str:
        """Format date range for display"""
        if not date_range:
            return "Unknown"

        min_date = date_range.get('min', 'Unknown')
        max_date = date_range.get('max', 'Unknown')

        return f"{min_date} to {max_date}"


__all__ = ['SummarizationAgent', 'SummarizationAgent_Hardcoded']
