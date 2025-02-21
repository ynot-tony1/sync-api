import os
import shutil
import uuid
import logging
from .log_utils import LogUtils
import asyncio
from api.config.settings import TEMP_PROCESSING_DIR

LogUtils.configure_logging() 
logger = logging.getLogger(__name__)

class ApiUtils:
    """Utility class for handling Api operations."""


    @staticmethod
    def save_temp_file(uploaded_file):
        """
        Saves an uploaded file to a temporary directory with a unique UUID4 name.

        Args:
            uploaded_file (UploadFile): The uploaded file to save.
            directory (str): Directory where the file will be saved.

        Returns:
            str: Path to the saved temporary file.

        Raises:
            IOError: If there is an error saving the file.

            
        """
        # split the file path to get the extension outside of it
        file_extension = os.path.splitext(uploaded_file.filename)[1] 
        # create the file path with the temp directory, the UUID4 name and the file
        unique_filename = os.path.join(TEMP_PROCESSING_DIR, f"{uuid.uuid4()}{file_extension}")
        try:
            # open the file in binary write mode
            temp_file = open(unique_filename, "wb")
            # copy over the content of the uploaded file to the temporary file safely
            shutil.copyfileobj(uploaded_file.file, temp_file)
            # close the file after writing
            temp_file.close()
            logger.info(f"Temporary file saved: {unique_filename}")
        except Exception as e:
            logger.error(f"Failed to save temporary file '{unique_filename}': {e}")
            raise IOError(f"Could not save temporary file: {e}")
        return unique_filename

