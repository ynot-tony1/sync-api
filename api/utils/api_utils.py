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
logger: logging.Logger = logging.getLogger("api_utils_logger")
import aiofiles

class ApiUtils:

    @staticmethod
    async def run_blocking(func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)

    @staticmethod
    async def save_temp_file(uploaded_file: UploadFile) -> str:
        """
        Saves an uploaded file to a temporary directory with a unique name.
        
        Args:
            uploaded_file (UploadFile): The file uploaded by the client.
        
        Returns:
            str: Path to the saved temporary file.
        
        Raises:
            IOError: If the file cannot be saved.
        """
        file_extension = os.path.splitext(uploaded_file.filename)[1]
        unique_filename = os.path.join(TEMP_PROCESSING_DIR, f"{uuid.uuid4()}{file_extension}")
        try:
            async with aiofiles.open(unique_filename, "wb") as temp_file:
                content = await uploaded_file.read()
                await temp_file.write(content)
            return unique_filename
        except Exception as e:
            logger.error(f"Failed to save temp file: {e}")
            raise

    @staticmethod
    def send_websocket_message(message: str) -> None:
        """
        Broadcasts a message to connected WebSocket clients.

        Args:
            message (str): The message to send.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            loop.create_task(broadcast(message))
        else:
            new_loop = asyncio.new_event_loop()
            try:
                new_loop.run_until_complete(broadcast(message))
            finally:
                new_loop.close()
