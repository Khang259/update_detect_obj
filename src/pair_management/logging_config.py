import logging
import os
from datetime import datetime

def setup_logging():
    date_str = datetime.now().strftime("%Y%m%d")
    os.makedirs("logs/logs_pair_management", exist_ok=True)
    os.makedirs("logs/logs_errors/logs_errors_pair_management", exist_ok=True)

    log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    log_handler = logging.FileHandler(f"logs/logs_pair_management/log_pair_manager_{date_str}.log")
    log_handler.setFormatter(log_formatter)

    error_handler = logging.FileHandler(f"logs/logs_errors/logs_errors_pair_management/logs_errors_pair_management_{date_str}.log")
    error_handler.setFormatter(log_formatter)
    error_handler.setLevel(logging.DEBUG)

    logger = logging.getLogger("pair_manager")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(log_handler)
    logger.addHandler(error_handler)
    return logger