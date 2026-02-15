"""
PII Detection and Column Classification
Based on BigQuery AI security model
"""
from typing import Dict, List, Set
from src.utils.logger import logger


class PIIDetector:
    """Detects and classifies PII columns"""

    # Column classification by sensitivity level
    CRITICAL_PII = {
        "Order_ID", "order_id", "ASIN", "asin", "SKU", "sku",
        "promotion_ids", "Customer", "customer", "customer_name"
    }

    SENSITIVE_PII = {
        "ship_postal_code", "ship_city", "ship_state", "ship_country",
        "postal_code", "city", "state", "country", "address",
        "email", "phone", "mobile"
    }

    CONFIDENTIAL = {
        "Amount", "amount", "RATE", "rate", "GROSS_AMT", "gross_amt",
        "Price", "price", "Cost", "cost", "revenue", "profit"
    }

    SAFE_COLUMNS = {
        "Category", "category", "Status", "status", "Fulfilment",
        "fulfilment", "Size", "size", "Color", "color", "Style",
        "style", "currency", "B2B", "Months", "months", "Date",
        "date", "Qty", "qty", "Courier_Status"
    }

    @classmethod
    def classify_column(cls, column_name: str) -> str:
        """
        Classify column by sensitivity level

        Returns:
            "critical" | "sensitive" | "confidential" | "safe"
        """
        if column_name in cls.CRITICAL_PII:
            return "critical"
        elif column_name in cls.SENSITIVE_PII:
            return "sensitive"
        elif column_name in cls.CONFIDENTIAL:
            return "confidential"
        elif column_name in cls.SAFE_COLUMNS:
            return "safe"
        else:
            # Default to sensitive for unknown columns
            return "sensitive"

    @classmethod
    def get_pii_columns(cls, schema: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Get PII columns categorized by sensitivity

        Args:
            schema: Database schema {column_name: column_type}

        Returns:
            Dictionary with categorized column lists
        """
        categorized = {
            "critical": [],
            "sensitive": [],
            "confidential": [],
            "safe": []
        }

        for column in schema.keys():
            category = cls.classify_column(column)
            categorized[category].append(column)

        logger.info(
            f"PII Classification: "
            f"{len(categorized['critical'])} critical, "
            f"{len(categorized['sensitive'])} sensitive, "
            f"{len(categorized['confidential'])} confidential, "
            f"{len(categorized['safe'])} safe"
        )

        return categorized

    @classmethod
    def requires_aggregation(cls, column_name: str) -> bool:
        """
        Check if column requires aggregation for LLM exposure

        Args:
            column_name: Name of column

        Returns:
            True if column must be aggregated (not sent raw to LLM)
        """
        category = cls.classify_column(column_name)
        return category in ["critical", "sensitive"]

    @classmethod
    def can_expose_to_llm(cls, column_name: str, is_aggregated: bool) -> bool:
        """
        Check if column value can be exposed to LLM

        Args:
            column_name: Column name
            is_aggregated: Whether the value is aggregated (COUNT, SUM, etc.)

        Returns:
            True if safe to expose to LLM
        """
        category = cls.classify_column(column_name)

        if category == "safe":
            return True  # Always safe

        if category in ["critical", "sensitive"]:
            return is_aggregated  # Only if aggregated

        if category == "confidential":
            return is_aggregated  # Only aggregated financial data

        return False


__all__ = ['PIIDetector']
