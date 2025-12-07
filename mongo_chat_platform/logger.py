import logging
from logging.config import dictConfig
import os

# Create logs directory
os.makedirs("logs", exist_ok=True)

def setup_logging():
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {
                # Using standard Formatter to avoid dependency on Uvicorn if not present
                "format": "%(levelname)s: %(asctime)s - %(name)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "file": { 
                "format": "%(levelname)s: %(asctime)s - %(name)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "formatter": "console",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "file": {
                "formatter": "file",
                "class": "logging.FileHandler",
                "filename": "logs/mongo_chat.log",
                "mode": "a",
                "encoding": "utf-8"
            },
        },
        "loggers": {
            "mongo_chat": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False
            },
            # root logger
            "": {
                "handlers": ["console", "file"],
                "level": "INFO",
            }
        },
    }
    dictConfig(log_config)

# Initialize logging immediately
setup_logging()

# Export logger
logger = logging.getLogger("mongo_chat")
