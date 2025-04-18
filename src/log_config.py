import logging
import os
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger("UCAutomation")
logger.setLevel(logging.INFO)

# Set up logging only if it hasn't been configured yet
if not logger.handlers:
    # Configure log file path
    log_file = os.path.expanduser("~/UCAutomation/lib/rawconverter_out.log")

    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Create and configure the timed rotating file handler
    handler = TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=7
    )
    handler.suffix = "%Y-%m-%d"
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)


def get_logger():
    """Return the configured logger instance."""
    return logger
