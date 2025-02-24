import os
import shutil
import uuid
import logging
from .log_utils import LogUtils
from api.connection_manager import broadcast  
import asyncio
from api.config.settings import TEMP_PROCESSING_DIR

LogUtils.configure_logging() 
logger = logging.getLogger(__name__)


class ApiUtils:
    """Utility class for handling API operations."""

    @staticmethod
    def save_temp_file(uploaded_file):
        """
        Saves an uploaded file to a temporary directory with a unique UUID4 name.

        The function extracts the file extension from the uploaded file's filename,
        generates a unique filename using UUID4, and constructs a full file path using
        the TEMP_PROCESSING_DIR. It then opens the destination file in binary write mode,
        copies the content from the uploaded file to the temporary file, and closes the file.
        If any error occurs during this process, an IOError is raised.

        Args:
            uploaded_file (UploadFile): The uploaded file to save.

        Returns:
            str: The path to the saved temporary file.

        Raises:
            IOError: If there is an error saving the file.
        """
        file_extension = os.path.splitext(uploaded_file.filename)[1]
        unique_filename = os.path.join(TEMP_PROCESSING_DIR, f"{uuid.uuid4()}{file_extension}")
        try:
            temp_file = open(unique_filename, "wb")
            shutil.copyfileobj(uploaded_file.file, temp_file)
            temp_file.close()
            logger.info(f"Temporary file saved: {unique_filename}")
        except Exception as e:
            logger.error(f"Failed to save temporary file '{unique_filename}': {e}")
            raise IOError(f"Could not save temporary file: {e}")
        return unique_filename

    @staticmethod
    def send_websocket_message(message: str):
        """
        Schedules a broadcast of a debug message to connected WebSocket clients.

        This function attempts to retrieve the current running asyncio event loop and
        schedules the broadcast function as a task within that loop. If no event loop is
        currently running, it uses asyncio.run to execute the broadcast immediately.

        Args:
            message (str): The message to broadcast to WebSocket clients.
        """
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(broadcast(message))
        except RuntimeError:
            asyncio.run(broadcast(message))
