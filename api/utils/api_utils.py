"""
Utility class for handling API operations.
"""

import os
import shutil
import uuid
import logging
import asyncio
from fastapi import UploadFile
from api.connection_manager import broadcast
from api.utils.log_utils import LogUtils
from api.config.settings import TEMP_PROCESSING_DIR

LogUtils.configure_logging()
logger: logging.Logger = logging.getLogger(__name__)


class ApiUtils:
    @staticmethod
    def save_temp_file(uploaded_file: UploadFile) -> str:
        """
        Saves an uploaded file to a temporary directory with a unique name.
        
        Args:
            uploaded_file (UploadFile): The file uploaded by the client.
        
        Returns:
            str: Path to the saved temporary file.
        
        Raises:
            IOError: If the file cannot be saved.
        """
        file_extension: str = os.path.splitext(uploaded_file.filename)[1]
        unique_filename: str = os.path.join(TEMP_PROCESSING_DIR, f"{uuid.uuid4()}{file_extension}")
        try:
            with open(unique_filename, "wb") as temp_file:
                shutil.copyfileobj(uploaded_file.file, temp_file)
            logger.info(f"Temporary file saved: {unique_filename}")
        except Exception as e:
            logger.error(f"Failed to save temporary file '{unique_filename}': {e}")
            raise IOError(f"Could not save temporary file: {e}")
        return unique_filename

    @staticmethod
    def send_websocket_message(message: str) -> None:
        """
        Broadcasts a message to connected WebSocket clients.
        
        Args:
            message (str): The message to send.
        """
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(broadcast(message))
        except RuntimeError:
            asyncio.run(broadcast(message))
