"""
Configuration management for the Retail Insights Assistant
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""

    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    LOGS_DIR = PROJECT_ROOT / "logs"

    # Ensure directories exist
    DATA_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)

    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Default to latest experimental model for best free tier quota
    # Will fallback to other models automatically if this one fails
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash-exp")

    # Database Configuration
    DUCKDB_PATH = os.getenv("DUCKDB_PATH", str(DATA_DIR / "retail_insights.duckdb"))

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", str(LOGS_DIR / "system.log"))

    # Cost Configuration (per 1M tokens) - Updated for Gemini 2.0
    # Free tier: 1500 requests per day, 1M tokens per minute
    GEMINI_INPUT_COST = float(os.getenv("GEMINI_INPUT_COST", "0.0"))  # Free tier
    GEMINI_OUTPUT_COST = float(os.getenv("GEMINI_OUTPUT_COST", "0.0"))  # Free tier

    # System Configuration
    MAX_QUERY_TIMEOUT = 300  # 5 minutes
    MAX_RESULT_ROWS = 10000
    MAX_RETRIES = 3

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables. "
                "Get your key from: https://aistudio.google.com/app/apikey"
            )
        return True

# Validate configuration on import
Config.validate()
