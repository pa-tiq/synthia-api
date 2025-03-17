import logging
import sys


def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Set specific log levels for certain modules if needed
    logging.getLogger("uvicorn").setLevel(logging.WARNING)

    return logging.getLogger(__name__)


# Create a logger instance
logger = setup_logging()
