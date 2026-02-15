"""
Enhanced Validation Agent with PII Protection
Based on BigQuery AI security model
"""
import re
from typing import Dict, List, Optional, Tuple
from src.agents.validation_agent import ValidationAgent
from src.utils.pii_detector import PIIDetector
from src.utils.logger import logger


class EnhancedValidationAgent(ValidationAgent):
    """
    Enhanced validation with PII column protection
    Enforces aggregation on sensitive data
    """

    def validate_query(
        self,
        sql_query: str,
        schema: Dict[str, str]
    ) -> Tuple[bool, List[str], Optional[str], str]:
        """
        Validate SQL query with enhanced PII protection

        Returns:
            tuple: (is_valid, issues, corrected_query, risk_level)
        """
        # Run base validation first
        is_valid, issues, corrected_query, risk_level = super().validate_query(
            sql_query, schema
        )

        # Additional PII protection checks
        pii_valid, pii_issues = self._validate_pii_access(sql_query, schema)

        if not pii_valid:
            issues.extend(pii_issues)
            is_valid = False
            risk_level = "high"
            logger.warning(f"PII validation failed: {pii_issues}")

        return is_valid, issues, corrected_query, risk_level

    def _validate_pii_access(
        self,
        sql_query: str,
        schema: Dict[str, str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that PII columns are properly aggregated

        BigQuery AI Rule: Sensitive columns must use GROUP BY or aggregate functions
        """
        issues = []
        sql_upper = sql_query.upper()

        # Get PII columns
        pii_classification = PIIDetector.get_pii_columns(schema)
        critical_columns = pii_classification["critical"]
        sensitive_columns = pii_classification["sensitive"]

        # Check if query has GROUP BY
        has_group_by = "GROUP BY" in sql_upper

        # Check if query uses aggregate functions
        has_aggregation = any(
            func in sql_upper
            for func in ["COUNT(", "SUM(", "AVG(", "MIN(", "MAX(", "COUNT DISTINCT"]
        )

        # Extract columns in SELECT clause (simplified parsing)
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_upper, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_clause = select_match.group(1)

            # Check for critical PII in SELECT without aggregation
            for col in critical_columns:
                col_upper = col.upper()

                # Check if column appears in SELECT
                if col_upper in select_clause:
                    # Allow if inside aggregate function
                    agg_patterns = [
                        f"COUNT({col_upper})",
                        f"COUNT(DISTINCT {col_upper})",
                        f"COUNT(DISTINCT({col_upper})",
                    ]

                    if any(pattern in select_clause for pattern in agg_patterns):
                        continue  # Aggregated - OK

                    # Check if this is a DISTINCT without aggregation
                    if "DISTINCT" in select_clause and not has_aggregation:
                        issues.append(
                            f"CRITICAL: Column '{col}' contains PII and must be aggregated. "
                            f"Use COUNT(DISTINCT {col}) instead of SELECT DISTINCT {col}"
                        )
                        continue

                    # If no GROUP BY and no aggregation, it's raw PII access
                    if not has_group_by and not has_aggregation:
                        issues.append(
                            f"CRITICAL: Column '{col}' contains PII and cannot be selected directly. "
                            f"Use GROUP BY or aggregate functions (COUNT, SUM, etc.)"
                        )

            # Warn about sensitive columns without aggregation
            for col in sensitive_columns:
                col_upper = col.upper()

                if col_upper in select_clause:
                    # Check if aggregated
                    if not has_group_by and not any(
                        f"{func}{col_upper}" in select_clause.replace(" ", "")
                        for func in ["COUNT(", "SUM(", "AVG("]
                    ):
                        issues.append(
                            f"WARNING: Column '{col}' is sensitive. "
                            f"Consider using GROUP BY or aggregation for privacy."
                        )

        is_valid = len([i for i in issues if "CRITICAL" in i]) == 0

        return is_valid, issues


__all__ = ['EnhancedValidationAgent']
