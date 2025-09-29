import logging
import os
from datetime import datetime

LOG_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "logs"))

def setup_logger(name="bigworld_exporter"):
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logfile = os.path.join(LOG_DIR, f"export_{timestamp}.log")
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        fh = logging.FileHandler(logfile, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fmt = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)
        sh.setFormatter(fmt)
        logger.addHandler(sh)
    return logger
