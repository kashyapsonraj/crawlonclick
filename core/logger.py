import logging
import datetime
from functools import wraps
import sys

# Configure a basic logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(stream=sys.stdout)
    ]
)

# Create a logger instance
logger = logging.getLogger(__name__)


def info(msg):
    logger.info(msg)


def error(msg):
    logger.error(msg)


def warning(msg):
    logger.warning(msg)


def decorate_log(fn):
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        start_dt = datetime.datetime.now()
        logger.info("Function \"%s\" and Start Time is: %s" % (fn.__name__, start_dt.strftime("%Y-%m-%d %H:%M:%S")))
        result = fn(self, *args, **kwargs)
        end_dt = datetime.datetime.now()
        logger.info("Time taken to execute function \"%s\": %s" % (fn.__name__, end_dt - start_dt))
        logger.info("Function \"%s\" and End Time is: %s" % (fn.__name__, end_dt.strftime("%Y-%m-%d %H:%M:%S")))
        return result
    return wrapper