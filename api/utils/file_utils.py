import os
import shutil
import logging
from typing import List, Optional

logger: logging.Logger = logging.getLogger('file_utils_logger')

class FileUtils:
    @staticmethod
    def copy_file(source: str, destination: str) -> str:
        logger.debug(f"[ENTER] copy_file -> source='{source}', destination='{destination}'")
        try:
            shutil.copy(source, destination)
            logger.info(f"[copy_file] Copied from '{source}' to '{destination}'")
            logger.debug(f"[EXIT] copy_file -> returning destination='{destination}'")
            return destination
        except Exception as e:
            logger.error(f"[copy_file] Exception -> {str(e)}")
            raise IOError(f"Could not copy file: {e}")

    @staticmethod
    def move_file(source: str, destination: str) -> str:
        logger.debug(f"[ENTER] move_file -> source='{source}', destination='{destination}'")
        try:
            shutil.move(source, destination)
            logger.info(f"[move_file] Moved from '{source}' to '{destination}'")
            logger.debug(f"[EXIT] move_file -> returning destination='{destination}'")
            return destination
        except Exception as e:
            logger.error(f"[move_file] Exception -> {str(e)}")
            raise IOError(f"Could not move file: {e}")

    @staticmethod
    def read_file(file_path: str) -> Optional[str]:
        logger.debug(f"[ENTER] read_file -> file_path='{file_path}'")
        try:
            with open(file_path, 'r') as file:
                content = file.read()
            logger.debug(
                f"[read_file] Successfully read file -> '{file_path}' (length={len(content)})"
            )
            logger.debug("[EXIT] read_file -> returning file content.")
            return content
        except FileNotFoundError:
            logger.warning(f"[read_file] File not found -> '{file_path}'")
            return None
        except Exception as e:
            logger.error(f"[read_file] Exception -> {str(e)}")
            return None

    @staticmethod
    def cleanup_file(file_path: str) -> None:
        logger.debug(f"[ENTER] cleanup_file -> file_path='{file_path}'")
        try:
            os.remove(file_path)
            logger.debug(f"[cleanup_file] Removed file -> '{file_path}'")
        except FileNotFoundError:
            logger.warning(f"[cleanup_file] File not found or already removed -> '{file_path}'")
        except Exception as e:
            logger.error(f"[cleanup_file] Exception -> {str(e)}")
            raise IOError(f"Could not remove file {file_path}: {e}")
        logger.debug("[EXIT] cleanup_file")

    @staticmethod
    def get_next_directory_number(data_dir: str) -> str:
        logger.debug(f"[ENTER] get_next_directory_number -> data_dir='{data_dir}'")
        existing_numbers: List[int] = []
        for item in os.listdir(data_dir):
            if item.isdigit():
                existing_numbers.append(int(item))
            else:
                logger.debug(f"[get_next_directory_number] Ignoring non-numeric dir='{item}'")
        next_number: int = (max(existing_numbers) + 1) if existing_numbers else 1
        formatted_number: str = f"{next_number:05d}"
        logger.debug(f"[EXIT] get_next_directory_number -> '{formatted_number}'")
        return formatted_number
