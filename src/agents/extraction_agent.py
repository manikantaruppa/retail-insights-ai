"""
Extraction Agent: Executes SQL queries on DuckDB
"""
from typing import Dict, List, Optional
from src.utils.duckdb_manager import db_manager
from src.utils.logger import logger


class ExtractionAgent:
    """Executes validated SQL queries"""

    def __init__(self):
        self.agent_name = "ExtractionAgent"
        logger.info(f"Initialized {self.agent_name}")

    def execute_query(
        self,
        sql_query: str
    ) -> tuple[bool, Optional[List[Dict]], Optional[str], int]:
        """
        Execute SQL query on DuckDB

        Args:
            sql_query: Validated SQL query

        Returns:
            tuple: (success, results, error_message, rows_scanned)
        """
        try:
            logger.info(f"[{self.agent_name}] Executing SQL query")

            # Execute query using DuckDB manager
            success, results, error_msg = db_manager.execute_query(sql_query)

            rows_scanned = len(results) if results else 0

            if success:
                logger.info(f"Query executed successfully: {rows_scanned} rows returned")
            else:
                logger.error(f"Query execution failed: {error_msg}")

            return success, results, error_msg, rows_scanned

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Extraction failed: {error_msg}")
            return False, None, error_msg, 0

    def get_preview(
        self,
        results: List[Dict],
        max_rows: int = 100
    ) -> List[Dict]:
        """
        Get preview of results (limit rows)

        Args:
            results: Full result set
            max_rows: Maximum rows to return

        Returns:
            Limited result set
        """
        if not results:
            return []

        return results[:max_rows]


__all__ = ['ExtractionAgent']
