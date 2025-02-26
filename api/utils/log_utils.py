"""
Utilities for configuring logging using YAML.
"""

import os
import logging.config
import yaml
from api.config.settings import LOG_CONFIG_PATH
from api.types.props import LogConfig

class LogUtils:
    @staticmethod
    def configure_logging() -> None:
        """
        Configures logging from a YAML configuration file.
        
        Raises:
            FileNotFoundError: If the config file is not found.
        """
        try:
            with open(LOG_CONFIG_PATH, 'r') as file:
                config: LogConfig = yaml.safe_load(file)
        except FileNotFoundError:
            logging.error(f"Couldn't find the logging configuration file at: {LOG_CONFIG_PATH}")
            raise
        logging.config.dictConfig(config)
