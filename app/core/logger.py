import logging
import os
from datetime import date

def setup_logger():
    # Buat folder logs jika belum ada
    os.makedirs("logs", exist_ok=True)

    # Format log
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # File handler per hari
    log_file = f"logs/{date.today()}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Check if handlers already exist to avoid duplicate logs in uvicorn reload
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
