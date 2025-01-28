import os
from dotenv import load_dotenv

# determining the project root directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

# loading the .env file from the project root
dotenv_path = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=dotenv_path)

# paths for the logging Directories
LOGS_DIR = os.getenv("LOGS_DIR", os.path.join(BASE_DIR, "api/logs/logs"))
FINAL_LOGS_DIR = os.getenv("FINAL_LOGS_DIR", os.path.join(BASE_DIR, "api/logs/final_logs"))
RUN_LOGS_DIR = os.getenv("RUN_LOGS_DIR", os.path.join(BASE_DIR, "api/logs/run_logs"))
LOG_CONFIG_PATH = os.getenv("LOG_CONFIG_PATH", os.path.join(BASE_DIR, "api/config/logging.yaml"))

# different processing Directories
FILE_HANDLING_DIR = os.getenv("FILE_HANDLING_DIR", os.path.join(BASE_DIR, "syncnet_python/file_handling"))
TEMP_PROCESSING_DIR = os.getenv("TEMP_PROCESSING_DIR", os.path.join(FILE_HANDLING_DIR, "temp_input"))
DATA_WORK_PYAVI_DIR = os.getenv("DATA_WORK_PYAVI_DIR", os.path.join(BASE_DIR, "syncnet_python/data/work/pyavi"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(FILE_HANDLING_DIR, "output"))
FINAL_OUTPUT_DIR = os.getenv("FINAL_OUTPUT_DIR", os.path.join(FILE_HANDLING_DIR, "final_output"))
DATA_WORK_DIR = os.getenv("DATA_WORK_DIR", os.path.join(BASE_DIR, "syncnet_python/data/work"))
DATA_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "syncnet_python/data"))
SYNCNET_BASE_DIR = os.getenv("SYNCNET_BASE_DIR", os.path.join(BASE_DIR, "syncnet_python"))

# processing Constants
DEFAULT_MAX_ITERATIONS = int(os.getenv("DEFAULT_MAX_ITERATIONS", 10))
DEFAULT_TOLERANCE_MS = int(os.getenv("DEFAULT_TOLERANCE_MS", 10))

# test data directory
TEST_DATA_DIR = os.path.join(BASE_DIR, "syncnet_python", "tests", "test_data")


