"""
DuckDB database manager for sales data
"""
import duckdb
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Any
from src.config import Config
from src.utils.logger import logger


class DuckDBManager:
    """Manages DuckDB connection and operations"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or Config.DUCKDB_PATH
        self.conn: Optional[duckdb.DuckDBPyConnection] = None
        self.schema: Optional[Dict[str, str]] = None

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = duckdb.connect(self.db_path)
            logger.info(f"Connected to DuckDB at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to DuckDB: {e}")
            raise

    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from DuckDB")

    def load_csv(self, csv_path: str, table_name: str = "sales") -> bool:
        """
        Load CSV file into DuckDB table

        Args:
            csv_path: Path to CSV file
            table_name: Name of table to create

        Returns:
            bool: Success status
        """
        try:
            if not self.conn:
                self.connect()

            logger.info(f"Loading CSV from {csv_path} into table '{table_name}'")

            # Read CSV with pandas first to handle data types
            df = pd.read_csv(csv_path, low_memory=False)

            # Clean column names (remove spaces, special chars)
            df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('-', '_')

            # Drop the index column if it exists
            if 'index' in df.columns:
                df = df.drop('index', axis=1)

            # Register dataframe as table
            self.conn.register(table_name, df)

            # Create persistent table
            self.conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM {table_name}")

            row_count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            logger.info(f"Loaded {row_count} rows into table '{table_name}'")

            # Cache schema
            self.schema = self.get_schema(table_name)

            return True

        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            return False

    def get_schema(self, table_name: str = "sales") -> Dict[str, str]:
        """
        Get table schema

        Returns:
            Dict mapping column names to types
        """
        try:
            if not self.conn:
                self.connect()

            result = self.conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
            schema = {row[1]: row[2] for row in result}  # column_name: type

            logger.info(f"Retrieved schema for table '{table_name}': {len(schema)} columns")
            return schema

        except Exception as e:
            logger.error(f"Failed to get schema: {e}")
            return {}

    def execute_query(
        self,
        sql_query: str,
        params: Optional[Dict] = None,
        timeout: int = Config.MAX_QUERY_TIMEOUT
    ) -> tuple[bool, Optional[List[Dict]], Optional[str]]:
        """
        Execute SQL query with timeout and error handling

        Args:
            sql_query: SQL query to execute
            params: Optional query parameters
            timeout: Query timeout in seconds

        Returns:
            tuple: (success, results, error_message)
        """
        try:
            if not self.conn:
                self.connect()

            logger.info(f"Executing query: {sql_query[:100]}...")

            # Execute query
            result = self.conn.execute(sql_query).fetchall()
            columns = [desc[0] for desc in self.conn.description]

            # Convert to list of dicts
            results = [dict(zip(columns, row)) for row in result]

            logger.info(f"Query returned {len(results)} rows")

            return True, results, None

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Query execution failed: {error_msg}")
            return False, None, error_msg

    def get_table_stats(self, table_name: str = "sales") -> Dict[str, Any]:
        """
        Get basic statistics about the table

        Returns:
            Dictionary with table statistics
        """
        try:
            if not self.conn:
                self.connect()

            stats = {}

            # Row count
            stats['total_rows'] = self.conn.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).fetchone()[0]

            # Date range (if Date column exists)
            if 'Date' in (self.schema or {}):
                date_range = self.conn.execute(
                    f"SELECT MIN(Date) as min_date, MAX(Date) as max_date FROM {table_name}"
                ).fetchone()
                stats['date_range'] = {
                    'min': str(date_range[0]) if date_range[0] else None,
                    'max': str(date_range[1]) if date_range[1] else None
                }

            # Column count
            stats['column_count'] = len(self.schema or {})

            return stats

        except Exception as e:
            logger.error(f"Failed to get table stats: {e}")
            return {}

    def get_sample_data(self, table_name: str = "sales", limit: int = 5) -> List[Dict]:
        """Get sample rows from table"""
        try:
            if not self.conn:
                self.connect()

            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            success, results, _ = self.execute_query(query)

            return results if success else []

        except Exception as e:
            logger.error(f"Failed to get sample data: {e}")
            return []


# Global database manager instance
db_manager = DuckDBManager()

__all__ = ['DuckDBManager', 'db_manager']
