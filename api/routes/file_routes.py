import os
import aiofiles
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import logging
from api.config.settings import FINAL_OUTPUT_DIR

router = APIRouter()
logger = logging.getLogger("file_routes")



@router.get("/download/{filename}")
async def download_file(filename: str) -> FileResponse:
    """Handles file download requests by asynchronously verifying file existence 
    and returning a FileResponse if the file is accessible.

    Args:
        filename (str): The name of the file to be downloaded.

    Returns:
        FileResponse: A response object that streams the requested file.

    Raises:
        HTTPException: 404 if the file does not exist.
        HTTPException: 500 if an error occurs while accessing the file.
    """
    logger.debug(f"[ENTER] download_file - Requested download for filename='{filename}'")
    file_path: str = os.path.join(FINAL_OUTPUT_DIR, filename)
    logger.debug(f"[download_file] Constructed file_path='{file_path}'")

    if not os.path.isfile(file_path):
        logger.error(f"[download_file] File not found -> {file_path}")
        raise HTTPException(status_code=404, detail="file not found.")

    logger.info(f"[download_file] File found. Preparing to return FileResponse -> {file_path}")

    try:
        async with aiofiles.open(file_path, "rb") as f:
            await f.read(10)
    except Exception as e:
        logger.error(f"[download_file] Error accessing file -> {file_path}, Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

    logger.debug(f"[EXIT] download_file -> returning FileResponse for '{filename}'")
    return FileResponse(file_path, filename=filename)
