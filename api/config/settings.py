import os
from dotenv import load_dotenv

# determine the project root directory (adjust if necessary)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

# load the .env file from the project root
dotenv_path = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)


# logging directories (build absolute paths)
LOGS_BASE = os.path.join(BASE_DIR, os.getenv("LOGS_BASE", "api/logs"))
LOGS_DIR = os.path.join(BASE_DIR, os.getenv("LOGS_DIR", "api/logs/logs"))
FINAL_LOGS_DIR = os.path.join(BASE_DIR, os.getenv("FINAL_LOGS_DIR", "api/logs/final_logs"))
RUN_LOGS_DIR = os.path.join(BASE_DIR, os.getenv("RUN_LOGS_DIR", "api/logs/run_logs"))
LOG_CONFIG_PATH = os.path.join(BASE_DIR, os.getenv("LOG_CONFIG_PATH", "api/config/logging.yaml"))

# processing directories (build absolute paths)
FILE_HANDLING_DIR = os.path.join(BASE_DIR, os.getenv("FILE_HANDLING_DIR", "api/file_handling"))
TEMP_PROCESSING_DIR = os.path.join(BASE_DIR, os.getenv("TEMP_PROCESSING_DIR", "api/file_handling/temp_input"))
FINAL_OUTPUT_DIR = os.path.join(BASE_DIR, os.getenv("FINAL_OUTPUT_DIR", "api/file_handling/final_output"))
DATA_WORK_PYAVI_DIR = os.path.join(BASE_DIR, os.getenv("DATA_WORK_PYAVI_DIR", "syncnet_python/data/work/pyavi"))
DATA_WORK_DIR = os.path.join(BASE_DIR, os.getenv("DATA_WORK_DIR", "syncnet_python/data/work"))
DATA_DIR = os.path.join(BASE_DIR, os.getenv("DATA_DIR", "syncnet_python/data"))
SYNCNET_BASE_DIR = os.path.join(BASE_DIR, os.getenv("SYNCNET_BASE_DIR", "syncnet_python"))

# processing constants
DEFAULT_MAX_ITERATIONS = int(os.getenv("DEFAULT_MAX_ITERATIONS", 10))
DEFAULT_TOLERANCE_MS = int(os.getenv("DEFAULT_TOLERANCE_MS", 10))

# test data directory
TEST_DATA_DIR = os.path.join(BASE_DIR, os.getenv("TEST_DATA_DIR", "syncnet_python/tests/test_data"))

# allowed cors origins
ALLOWED_LOCAL_1 = os.getenv("ALLOWED_LOCAL_1", "http://localhost:3000")
ALLOWED_LOCAL_2 = os.getenv("ALLOWED_LOCAL_2", "http://127.0.0.1:3000")
ALLOWED_ORIGINS = [ALLOWED_LOCAL_1, ALLOWED_LOCAL_2]

