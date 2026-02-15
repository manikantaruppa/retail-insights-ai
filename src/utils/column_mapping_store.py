"""
Column Mapping Store
Saves and loads user-confirmed column mappings for CSVs
"""
import json
import os
from datetime import datetime
from typing import Dict, Optional
from src.utils.logger import logger


MAPPING_FILE = "./data/column_mappings.json"


class ColumnMappingStore:
    """Store and retrieve column mappings for CSVs"""

    @staticmethod
    def save_column_mapping(csv_filename: str, column_mapping: Dict[str, str]) -> None:
        """
        Save user-confirmed column mapping for future use

        Args:
            csv_filename: Name of the CSV file
            column_mapping: Dictionary of column types to column names
        """
        try:
            # Load existing mappings
            if os.path.exists(MAPPING_FILE):
                with open(MAPPING_FILE, 'r') as f:
                    mappings = json.load(f)
            else:
                mappings = {}

            # Save new mapping
            mappings[csv_filename] = {
                'categorical': column_mapping.get('categorical'),
                'numeric': column_mapping.get('numeric'),
                'location': column_mapping.get('location'),
                'date': column_mapping.get('date'),
                'timestamp': datetime.now().isoformat()
            }

            # Ensure data directory exists
            os.makedirs(os.path.dirname(MAPPING_FILE), exist_ok=True)

            with open(MAPPING_FILE, 'w') as f:
                json.dump(mappings, f, indent=2)

            logger.info(f"Saved column mapping for '{csv_filename}'")

        except Exception as e:
            logger.error(f"Failed to save column mapping: {e}")

    @staticmethod
    def load_column_mapping(csv_filename: str) -> Optional[Dict[str, str]]:
        """
        Load previously saved column mapping

        Args:
            csv_filename: Name of the CSV file

        Returns:
            Dictionary of column mappings or None if not found
        """
        try:
            if os.path.exists(MAPPING_FILE):
                with open(MAPPING_FILE, 'r') as f:
                    mappings = json.load(f)
                    mapping = mappings.get(csv_filename)

                    if mapping:
                        logger.info(f"Loaded saved column mapping for '{csv_filename}'")
                        return mapping

            logger.info(f"No saved mapping found for '{csv_filename}'")
            return None

        except Exception as e:
            logger.error(f"Failed to load column mapping: {e}")
            return None

    @staticmethod
    def delete_column_mapping(csv_filename: str) -> None:
        """
        Delete saved column mapping

        Args:
            csv_filename: Name of the CSV file
        """
        try:
            if os.path.exists(MAPPING_FILE):
                with open(MAPPING_FILE, 'r') as f:
                    mappings = json.load(f)

                if csv_filename in mappings:
                    del mappings[csv_filename]

                    with open(MAPPING_FILE, 'w') as f:
                        json.dump(mappings, f, indent=2)

                    logger.info(f"Deleted column mapping for '{csv_filename}'")

        except Exception as e:
            logger.error(f"Failed to delete column mapping: {e}")


__all__ = ['ColumnMappingStore']
