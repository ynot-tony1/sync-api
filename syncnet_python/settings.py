import os
from dotenv import load_dotenv

# determining the project root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# loading the .env file
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=dotenv_path)

# logging directories
LOGS_DIR = os.getenv('LOGS_DIR')
FINAL_LOGS_DIR = os.getenv('FINAL_LOGS_DIR')
RUN_LOGS_DIR = os.getenv('RUN_LOGS_DIR')

# path to the logging configuration file
LOG_CONFIG_PATH = os.getenv('LOG_CONFIG_PATH')

# processing directories
TEMP_PROCESSING_DIR = os.getenv('TEMP_PROCESSING_DIR')
DATA_WORK_PYAVI_DIR = os.getenv('DATA_WORK_PYAVI_DIR')
DATA_WORK_DIR = os.getenv('DATA_WORK_DIR')
DATA_DIR = os.getenv('DATA_DIR')
OUTPUT_DIR = os.getenv('OUTPUT_DIR')
FINAL_OUTPUT_DIR = os.getenv('FINAL_OUTPUT_DIR')

# processing onstants
DEFAULT_MAX_ITERATIONS = int(os.getenv('DEFAULT_MAX_ITERATIONS'))
DEFAULT_TOLERANCE_MS = int(os.getenv('DEFAULT_TOLERANCE_MS'))
