# logger.py


import logging
import yaml
import logging.config

def init_logger(path="config/logging.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        logging.config.dictConfig(config)
    return logging.getLogger(__name__)


