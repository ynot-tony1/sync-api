"""
Utilities for configuring logging using YAML.
"""

import os
import logging.config
from typing import Any
import yaml

from api.config.type_settings import LOG_CONFIG_PATH


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
                config: Any = yaml.safe_load(file)
        except FileNotFoundError:
            logging.error(f"Couldn't find the logging configuration file at: {LOG_CONFIG_PATH}")
            raise
        logging.config.dictConfig(config)
