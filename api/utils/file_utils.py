import os
import shutil
import logging
from .log_utils import LogUtils
from api.config.settings import TEMP_PROCESSING_DIR, DATA_DIR, DATA_WORK_PYAVI_DIR


LogUtils.configure_logging()
logger = logging.getLogger('file_utils_logger')

class FileUtils:
    """Utility class for handling file operations."""

    @staticmethod
    def move_to_data_work(initial_path, dir_num):
        """
        Moves a file to the data work directory, prefixing the filename with the directory number.

        Args:
            initial_path (str): Path to the file to be moved.
            dir_num (str or int): Reference number for the filename prefix.

        Returns:
            str: Destination path after moving.

        Raises:
            FileNotFoundError: If the destination file does not exist after moving.
            IOError: If the file cannot be moved.
        """


        original_filename = os.path.basename(initial_path)

        dest_file_path = os.path.join(DATA_DIR, f"{dir_num}_{original_filename}")

        try:
            shutil.move(initial_path, dest_file_path)
        except Exception as e:
            error_msg = f"Couldnt move the file to {dest_file_path}: {e}"
            logger.error(error_msg)
            raise IOError(f"File cant be moved to {dest_file_path}: {e}")
        logger.debug(f"Copied file successfully moved from temp directory to: {dest_file_path}")
        return dest_file_path

    @staticmethod
    def copy_input_to_temp(input_file, original_name):
        """
        Copies the input file to a temporary processing directory.

        Args:
            input_file (str): Path to the input video file.
            original_name (str): Original filename of the video.

        Returns:
            str: Path to the copied file in the temporary directory.
        """
        temp_file = os.path.join(TEMP_PROCESSING_DIR, f"corrected_{original_name}")
        shutil.copy(input_file, temp_file)
        logger.debug(f"copied file to: {temp_file}")
        
        return temp_file

    @staticmethod
    def prepare_directories(directories):
        """
        Ensures that all specified directories exist.

        Args:
            directories (list of str): List of directory paths to create.
        """
        for directory in directories:
            os.makedirs(directory, exist_ok=True)


    @staticmethod
    def read_log_file(file_path):
        """
        Reads the content of a log file.

        Args:
            file_path (str): Path to the log file.

        Returns:
            str or None: Content of the log file if successful; otherwise, None.
        """
        try:
            with open(file_path, 'r') as file:
                content = file.read()
            logger.debug(f"successfully read log file: {file_path}")
            return content
        except FileNotFoundError:
            logger.warning(f"log file not found: {file_path}")
            return None
        except Exception as e:
            logger.error(f"failed to read log file {file_path}: {e}")
            return None

    @staticmethod
    def cleanup_file(file_path):
        """
        Removes a specified file.

        Args:
            file_path (str): Path to the file to remove.
        """
        try:
            os.remove(file_path)
            logger.debug(f"file successfully removed: {file_path}")
        except FileNotFoundError:
            logger.warning(f"file already removed: {file_path}")
        except Exception as e:
            logger.error(f"failed to remove file {file_path}: {e}")
            raise IOError(f"could not remove file {file_path}: {e}")

    @staticmethod
    def copy_video_file(source, destination):
        """
        Copies a video file from source to destination.

        Args:
            source (str): Path to the source video file.
            destination (str): Path to the destination.

        Returns:
            str: Path to the copied video file.
        """
        try:
            shutil.copy(source, destination)
            logger.info(f"video file copied from {source} to {destination}")
            return destination
        except Exception as e:
            logger.error(f"failed to copy video file from {source} to {destination}: {e}")
            raise IOError(f"could not copy video file: {e}")

    @staticmethod
    def get_next_directory_number(data_dir):
        """
        Returns the next directory number as a zero-padded string, eg. 00001.
        If no numeric subdirectories exist, it starts at 1.
        """
        existing_numbers = []
        all_items = os.listdir(data_dir)
        for item in all_items:
            if item.isdigit():
                number = int(item)
                existing_numbers.append(number)
            else:
                logger.debug(f"Going to ignore this non-numeric directory: {item}")
        if not existing_numbers:
            logger.info("Couldn't see any numeric directories. Starting it off at 00001.")
            next_number = 1
        else:   
            next_number = max(existing_numbers) + 1
        formatted_number = f"{next_number:05d}"
        logger.debug(f"The next number in the directory is: {formatted_number}")
        return formatted_number