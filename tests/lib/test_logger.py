"""
Test Logger Utility Module
Provides border decorator and logger for unit tests
"""
import logging
import sys
from functools import wraps

def border(func):
    """Decorator to add border logging around test methods"""
    MAX_CHARS = 80
    @wraps(func)
    def border_writer(*arg, **kwargs):
        print('\n')
        logger.info(" Start {} ".format(func.__name__).center(MAX_CHARS, "="))
        out = func(*arg, **kwargs)
        logger.info(" End {} ".format(func.__name__).center(MAX_CHARS, "="))
        return out
    return border_writer

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    # Colors
    BLACK = "\033[0;30m"
    YELLOW = "\033[1;33m"
    GREEN = "\033[0;32m"
    RED = "\033[31;20m"
    BOLD_RED = "\033[31;1m"
    CYAN = "\033[0;36m"
    RESET = "\033[0m"

    # Formats
    ONLY_LEVEL_FMT = "%(asctime)s-[%(filename)s:%(lineno)d]-{}[%(levelname)s]{} - %(message)s"
    FULL_MSG_FMT = "{}%(asctime)s-[%(filename)s:%(lineno)d]-[%(levelname)s] - %(message)s{}"

    FORMATS = {
        logging.DEBUG: ONLY_LEVEL_FMT.format(CYAN, RESET),
        logging.INFO: ONLY_LEVEL_FMT.format(GREEN, RESET),
        logging.WARNING: FULL_MSG_FMT.format(YELLOW, RESET),
        logging.ERROR: FULL_MSG_FMT.format(RED, RESET),
        logging.CRITICAL: FULL_MSG_FMT.format(BOLD_RED, RESET)
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create formatter
__formatter = logging.Formatter('%(asctime)s-[%(filename)s:%(lineno)d]-[%(levelname)s] - %(message)s')
__formatter.datefmt = "%H:%M:%S"

# Create console handler
__ch = logging.StreamHandler(sys.stdout)
__ch.setLevel(logging.DEBUG)
__ch.setFormatter(CustomFormatter())
logger.addHandler(__ch)

