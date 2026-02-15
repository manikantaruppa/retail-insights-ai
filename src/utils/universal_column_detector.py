"""
Universal Column Detector
Auto-detects column types from any CSV schema
"""
from typing import Dict, List, Tuple
from src.utils.logger import logger


class UniversalColumnDetector:
    """Detects column types from schema with confidence scoring"""

    # Pattern definitions for column detection
    CATEGORICAL_PATTERNS = [
        'category', 'type', 'class', 'status', 'genre', 'group',
        'kind', 'style', 'segment', 'classification'
    ]

    NUMERIC_PATTERNS = [
        'amount', 'price', 'cost', 'revenue', 'sales', 'total',
        'value', 'sum', 'quantity', 'qty', 'count', 'number'
    ]

    LOCATION_PATTERNS = [
        'city', 'state', 'country', 'region', 'location', 'area',
        'zone', 'territory', 'district', 'province', 'postal'
    ]

    DATE_PATTERNS = [
        'date', 'time', 'created', 'updated', 'order_date', 'timestamp',
        'datetime', 'day', 'month', 'year', 'period'
    ]

    @staticmethod
    def detect_columns_with_confidence(schema: Dict[str, str]) -> Tuple[Dict[str, List[str]], float]:
        """
        Detect column types from schema with confidence score

        Args:
            schema: Dictionary of {column_name: data_type}

        Returns:
            Tuple of (detected_columns_dict, confidence_score)
        """
        detected = {
            'categorical': [],
            'numeric': [],
            'location': [],
            'date': []
        }

        confidence_scores = []

        for col_name, data_type in schema.items():
            col_lower = col_name.lower()
            col_confidence = 0.0

            # Check categorical patterns
            for pattern in UniversalColumnDetector.CATEGORICAL_PATTERNS:
                if pattern in col_lower:
                    detected['categorical'].append(col_name)
                    col_confidence = 0.90  # High confidence
                    break

            # Check numeric patterns
            if not col_confidence:
                for pattern in UniversalColumnDetector.NUMERIC_PATTERNS:
                    if pattern in col_lower:
                        detected['numeric'].append(col_name)
                        col_confidence = 0.90
                        break

            # Check location patterns
            if not col_confidence:
                for pattern in UniversalColumnDetector.LOCATION_PATTERNS:
                    if pattern in col_lower:
                        detected['location'].append(col_name)
                        col_confidence = 0.85  # Slightly lower (could be sensitive)
                        break

            # Check date patterns
            if not col_confidence:
                for pattern in UniversalColumnDetector.DATE_PATTERNS:
                    if pattern in col_lower:
                        detected['date'].append(col_name)
                        col_confidence = 0.90
                        break

            # Check data type hints (if no pattern match)
            if not col_confidence:
                if 'INT' in data_type.upper() or 'FLOAT' in data_type.upper() or 'DOUBLE' in data_type.upper():
                    # Numeric type but unclear column name
                    detected['numeric'].append(col_name)
                    col_confidence = 0.50  # Medium confidence
                elif 'VARCHAR' in data_type.upper() or 'TEXT' in data_type.upper():
                    # Text type, assume categorical
                    detected['categorical'].append(col_name)
                    col_confidence = 0.40  # Low confidence
                else:
                    col_confidence = 0.20  # Very low confidence

            confidence_scores.append(col_confidence)

        # Calculate average confidence
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        logger.info(f"Auto-detected columns with {avg_confidence:.2%} confidence")
        logger.debug(f"Detected: {detected}")

        return detected, avg_confidence

    @staticmethod
    def validate_detection(detected: Dict[str, List[str]]) -> bool:
        """
        Validate that detection found minimum required columns

        Returns:
            bool: True if valid (has at least categorical OR numeric)
        """
        has_categorical = len(detected.get('categorical', [])) > 0
        has_numeric = len(detected.get('numeric', [])) > 0

        return has_categorical or has_numeric


__all__ = ['UniversalColumnDetector']
