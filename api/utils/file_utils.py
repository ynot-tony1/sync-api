"""
Utility class for handling file operations.
"""

import os
import shutil
import logging
from typing import List, Optional

from api.config.type_settings import DATA_DIR, TEMP_PROCESSING_DIR

logger: logging.Logger = logging.getLogger('file_utils_logger')


class FileUtils:
    @staticmethod
    def move_to_data_work(initial_path: str, dir_num: int) -> str:
        """
        Moves a file to the data work directory with a directory number prefix.
        
        Args:
            initial_path (str): Path of the file to move.
            dir_num (int): Numeric prefix for the file.
        
        Returns:
            str: Destination file path.
        
        Raises:
            IOError: If the file cannot be moved.
        """
        original_filename: str = os.path.basename(initial_path)
        dest_file_path: str = os.path.join(DATA_DIR, f"{dir_num}_{original_filename}")
        try:
            shutil.move(initial_path, dest_file_path)
        except Exception as e:
            error_msg: str = f"Couldn't move the file to {dest_file_path}: {e}"
            logger.error(error_msg)
            raise IOError(f"File can't be moved to {dest_file_path}: {e}")
        logger.debug(f"File successfully moved to: {dest_file_path}")
        return dest_file_path

    @staticmethod
    def copy_input_to_temp(input_file: str, original_name: str) -> str:
        """
        Copies the input file to a temporary processing directory.
        
        Args:
            input_file (str): Path to the input file.
            original_name (str): Original filename.
        
        Returns:
            str: Path to the temporary file copy.
        """
        temp_file: str = os.path.join(TEMP_PROCESSING_DIR, f"corrected_{original_name}")
        shutil.copy(input_file, temp_file)
        logger.debug(f"Copied file to: {temp_file}")
        return temp_file

    @staticmethod
    def prepare_directories(directories: List[str]) -> None:
        """
        Ensures that all directories in the list exist.
        
        Args:
            directories (List[str]): List of directory paths.
        """
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    @staticmethod
    def read_log_file(file_path: str) -> Optional[str]:
        """
        Reads the contents of a log file.
        
        Args:
            file_path (str): Path to the log file.
        
        Returns:
            Optional[str]: Content of the file or None if not found.
        """
        try:
            with open(file_path, 'r') as file:
                content: str = file.read()
            logger.debug(f"Successfully read log file: {file_path}")
            return content
        except FileNotFoundError:
            logger.warning(f"Log file not found: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to read log file {file_path}: {e}")
            return None

    @staticmethod
    def cleanup_file(file_path: str) -> None:
        """
        Removes a file.
        
        Args:
            file_path (str): Path to the file to remove.
        
        Raises:
            IOError: If the file cannot be removed.
        """
        try:
            os.remove(file_path)
            logger.debug(f"File successfully removed: {file_path}")
        except FileNotFoundError:
            logger.warning(f"File already removed: {file_path}")
        except Exception as e:
            logger.error(f"Failed to remove file {file_path}: {e}")
            raise IOError(f"Could not remove file {file_path}: {e}")

    @staticmethod
    def copy_video_file(source: str, destination: str) -> str:
        """
        Copies a video file from source to destination.
        
        Args:
            source (str): Source file path.
            destination (str): Destination path.
        
        Returns:
            str: Destination path.
        
        Raises:
            IOError: If the file cannot be copied.
        """
        try:
            shutil.copy(source, destination)
            logger.info(f"Video file copied from {source} to {destination}")
            return destination
        except Exception as e:
            logger.error(f"Failed to copy video file from {source} to {destination}: {e}")
            raise IOError(f"Could not copy video file: {e}")

    @staticmethod
    def get_next_directory_number(data_dir: str) -> str:
        """
        Returns the next directory number as a zero-padded string.
        
        Args:
            data_dir (str): Path to the data directory.
        
        Returns:
            str: Next directory number, e.g. "00001".
        """
        existing_numbers: List[int] = []
        all_items = os.listdir(data_dir)
        for item in all_items:
            if item.isdigit():
                existing_numbers.append(int(item))
            else:
                logger.debug(f"Ignoring non-numeric directory: {item}")
        next_number: int = (max(existing_numbers) + 1) if existing_numbers else 1
        formatted_number: str = f"{next_number:05d}"
        logger.debug(f"The next number in the directory is: {formatted_number}")
        return formatted_number
