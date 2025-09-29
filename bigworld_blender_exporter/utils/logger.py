import logging
import os

# Resolve log file path at addon root
LOG_FILE = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'bigworld_export.log'))

_file_handlers_by_logger = {}

def get_logger(name: str = 'BigWorldExporter') -> logging.Logger:
    """Return a configured logger with file + console handlers (idempotent)."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Install file handler once per named logger
    if name not in _file_handlers_by_logger:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        _file_handlers_by_logger[name] = file_handler

    # Install console handler if none
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# Backward-compatible helpers using default logger
def info(msg):
    get_logger().info(msg)

def warning(msg):
    get_logger().warning(msg)

def error(msg):
    get_logger().error(msg)

def setup():
    # Kept for backwards compatibility; ensure default logger is initialized
    get_logger()

def teardown():
    # Optional: remove file handlers if needed
    for name, handler in list(_file_handlers_by_logger.items()):
        logger = logging.getLogger(name)
        logger.removeHandler(handler)
        handler.close()
        del _file_handlers_by_logger[name]
