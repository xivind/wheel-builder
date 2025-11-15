import logging
import sys

def setup_logger():
    """Configure unified logging for FastAPI and Python modules.

    Logs to stdout/stderr for Docker container visibility.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()