import logging
from logging.handlers import RotatingFileHandler
import contextvars

# Define a context variable for correlation ID
correlation_id = contextvars.ContextVar("correlation_id", default="N/A")

class ContextFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = correlation_id.get()
        return True

def setup_logger(service_name: str, log_file: str = "./logs/system.log"):
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - CorrelationID:%(correlation_id)s - %(message)s"
    )
    handler = RotatingFileHandler(log_file, maxBytes=10**6, backupCount=5)
    handler.setFormatter(formatter)

    logger = logging.getLogger(service_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    # Add correlation ID filter
    logger.addFilter(ContextFilter())
    return logger
