import os
import shutil
import logging
from typing import List, Optional
import aiofiles, asyncio
from asyncio import get_running_loop
from api.utils.api_utils import ApiUtils

logger: logging.Logger = logging.getLogger('file_utils_logger')


class FileUtils:
    @staticmethod
    async def copy_file(source: str, destination: str) -> str:
        """Async copy using threadpool for blocking I/O."""
        logger.debug(f"Copying file: {source} -> {destination}")
        try:
            await ApiUtils.run_blocking(shutil.copy, source, destination)
            logger.info(f"Copied file: {source} -> {destination}")
            return destination
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            raise IOError(f"Could not copy file: {e}")

    @staticmethod
    async def move_file(source: str, destination: str) -> str:
        """Async move using threadpool for blocking I/O."""
        logger.debug(f"Moving file: {source} -> {destination}")
        try:
            await ApiUtils.run_blocking(shutil.move, source, destination)
            logger.info(f"Moved file: {source} -> {destination}")
            return destination
        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            raise IOError(f"Could not move file: {e}")

    @staticmethod
    async def read_file(file_path: str) -> str:
        """Async file read using aiofiles."""
        logger.debug(f"Reading file: {file_path}")
        try:
            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()
            logger.debug(f"Successfully read file: {file_path}")
            return content
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            raise IOError(f"Could not read file: {e}")

    @staticmethod
    async def cleanup_file(file_path: str) -> None:
        """Async file deletion using threadpool for blocking I/O."""
        logger.debug(f"Cleaning up file: {file_path}")
        try:
            await ApiUtils.run_blocking(os.remove, file_path)
            logger.info(f"Removed file: {file_path}")
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Failed to remove file: {e}")
            raise IOError(f"Could not remove file: {e}")

    @staticmethod
    async def get_next_directory_number(data_dir: str) -> str:
        """Async directory number calculation"""
        try:
            items = await ApiUtils.run_blocking(os.listdir, data_dir)
            existing_numbers = [int(item) for item in items if item.isdigit()]
            next_number = max(existing_numbers) + 1 if existing_numbers else 1
            return f"{next_number:05d}"
        except FileNotFoundError:
            await ApiUtils.run_blocking(os.makedirs, data_dir, exist_ok=True)
            return "00001"
