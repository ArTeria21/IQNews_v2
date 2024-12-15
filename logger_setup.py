# logger_setup.py

import logging
import os
from logging import Logger
from logging.handlers import RotatingFileHandler
import uuid
class CorrelationLogger(Logger):
    """
    Custom Logger class that adds support for correlation_id in log records.
    """

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, **kwargs):
        """
        Overrides the default _log method to extract correlation_id from kwargs
        and add it to the extra dictionary.
        """
        correlation_id = kwargs.pop('correlation_id', None)

        if extra is None:
            extra = {}

        if correlation_id:
            extra['correlation_id'] = correlation_id
        else:
            # Provide a default value if correlation_id is not provided
            extra['correlation_id'] = 'N/A'

        super()._log(level, msg, args, exc_info, extra, stack_info)


class CorrelationFormatter(logging.Formatter):
    """
    Custom Formatter that ensures correlation_id and source_file are always present in log records.
    """

    def format(self, record):
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = 'N/A'
        if not hasattr(record, 'source_file'):
            record.source_file = 'Unknown'
        return super().format(record)


def setup_logger(source_file: str) -> Logger:
    """
    Configures and returns a LoggerAdapter that writes to ./logs/system.log
    with support for correlation_id and source_file.

    Args:
        source_file (str): The name of the Python file/source generating the logs.

    Returns:
        LoggerAdapter: A logger adapter with the source_file included in log records.
    """
    # Define the log directory and file path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(current_dir, 'logs')
    log_file = os.path.join(log_dir, 'system.log')

    # Create the log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Set the custom Logger class
    logging.setLoggerClass(CorrelationLogger)

    # Create a base logger instance
    logger = logging.getLogger('system_logger')
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent log messages from being propagated to the root logger

    # Check if handlers are already added to avoid duplicate logs
    if not logger.handlers:
        # Create a RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)

        # Define the log message format
        formatter = CorrelationFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - Source: %(source_file)s - Correlation ID: %(correlation_id)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(file_handler)

    # Create a LoggerAdapter to include the source_file in each log record
    adapter = logging.LoggerAdapter(logger, {'source_file': source_file})

    return adapter

def generate_correlation_id():
    return str(uuid.uuid4())