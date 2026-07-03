"""
Logging configuration for TFT Auto Chess
"""
import sys
from pathlib import Path
from loguru import logger

from config.settings import LOG_DIR, LOG_LEVEL, LOG_FORMAT


def setup_logger():
    """Setup logger configuration"""
    
    # Remove default handler
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stdout,
        format=LOG_FORMAT,
        level=LOG_LEVEL,
        colorize=True,
    )
    
    # File handler
    log_file = LOG_DIR / "tft_auto_chess.log"
    logger.add(
        str(log_file),
        format=LOG_FORMAT,
        level=LOG_LEVEL,
        rotation="500 MB",  # Rotate when file reaches 500MB
        retention="7 days",  # Keep logs for 7 days
        compression="zip",  # Compress rotated logs
    )
    
    return logger


# Initialize logger
logger = setup_logger()

__all__ = ["logger"]