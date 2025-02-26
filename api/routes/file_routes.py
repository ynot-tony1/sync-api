"""
Routes for file download.
"""

import os
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from api.config.settings import FINAL_OUTPUT_DIR

logger: logging.Logger = logging.getLogger("file_routes")
router: APIRouter = APIRouter()

@router.get("/download/{filename}")
def download_file(filename: str) -> FileResponse:
    """
    Constructs file path and returns the file if it exists.
    
    Args:
        filename (str): Name of the file to download.
    
    Returns:
        FileResponse: The response containing the file.
    
    Raises:
        HTTPException: If the file is not found.
    """
    file_path: str = os.path.join(FINAL_OUTPUT_DIR, filename)
    if not os.path.isfile(file_path):
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail="file not found.")
    logger.info(f"File download successful: {file_path}")
    return FileResponse(file_path, filename=filename)
