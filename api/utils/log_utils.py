import os
import logging
import logging.config
import yaml
from api.config.settings import LOG_CONFIG_PATH
from api.types.props import LogConfig

class LogUtils:
    @staticmethod
    def configure_logging() -> None:
        logger = logging.getLogger("log_utils_logger")
        logger.debug("[ENTER] configure_logging")
        try:
            with open(LOG_CONFIG_PATH, 'r') as file:
                config: LogConfig = yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"[configure_logging] Couldn't find logging config -> '{LOG_CONFIG_PATH}'")
            raise
        logging.config.dictConfig(config)
        logger.debug("[EXIT] configure_logging")
