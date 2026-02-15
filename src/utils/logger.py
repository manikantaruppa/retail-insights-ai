"""
Logging configuration with PII masking
"""
import re
from loguru import logger
from src.config import Config

# PII patterns to mask
PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    'order_id': r'\b\d{3}-\d{7}-\d{7}\b',
    'postal_code': r'\b\d{6}\b',
}

def mask_pii(message: str) -> str:
    """Mask PII in log messages"""
    masked = message
    for pii_type, pattern in PII_PATTERNS.items():
        masked = re.sub(pattern, f'[{pii_type.upper()}_MASKED]', masked)
    return masked

class PIIFilter:
    """Filter to mask PII in logs"""

    def __call__(self, record):
        record["message"] = mask_pii(record["message"])
        return True

# Configure logger
logger.remove()  # Remove default handler

# Add console handler with PII masking
logger.add(
    lambda msg: print(msg, end=""),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=Config.LOG_LEVEL,
    filter=PIIFilter()
)

# Add file handler with PII masking
logger.add(
    Config.LOG_FILE,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
    level=Config.LOG_LEVEL,
    rotation="10 MB",
    retention="7 days",
    filter=PIIFilter()
)

__all__ = ['logger']
