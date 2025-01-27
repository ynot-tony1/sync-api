import os
import logging
import logging.config
from api.config.settings import LOG_CONFIG_PATH
import yaml

class LogUtils:
    @staticmethod
    def configure_logging():
        """
        Configure logging using a YAML configuration file.
        """
        try:
            with open(LOG_CONFIG_PATH, 'r') as file:
                config = yaml.safe_load(file)

            # Ensure log directories exist
            for handler_name, handler_config in config.get('handlers', {}).items():
                if 'filename' in handler_config:
                    log_file = handler_config['filename']
                    log_dir = os.path.dirname(log_file)
                    os.makedirs(log_dir, exist_ok=True)

            logging.config.dictConfig(config)
            logging.debug("Logging configured successfully.")
        except FileNotFoundError:
            logging.error(f"Couldn't find the logging configuration file at: {LOG_CONFIG_PATH}")
            raise
        except Exception as e:
            logging.error(f"Failed to configure logging: {e}")
            raise
