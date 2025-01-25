import logging
import logging.config
from settings import LOG_CONFIG_PATH
import yaml

class LogUtils:
    """
    Utilities for configuring and retrieving loggers using YAML configurations.
    """

    @staticmethod
    def configure_logging():
        """
        Configure logging using a YAML configuration file.
        
        Does not return any specific named logger—once the config is applied, 
        you can call `logging.getLogger('name')` anywhere in your code.
        """
        try:
            with open(LOG_CONFIG_PATH, 'r') as file:
                config = yaml.safe_load(file)
            logging.debug(f"Loaded logging configuration from {LOG_CONFIG_PATH}")
        except FileNotFoundError:
            logging.error(f"Couldn't find the logging configuration file at: {LOG_CONFIG_PATH}")
            raise

        # Apply the logging configuration to configure all loggers from the YAML
        logging.config.dictConfig(config)

