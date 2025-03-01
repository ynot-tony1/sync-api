import os
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from api.config.settings import FINAL_OUTPUT_DIR

logger: logging.Logger = logging.getLogger("file_routes")
router: APIRouter = APIRouter()

@router.get("/download/{filename}")
def download_file(filename: str) -> FileResponse:
    logger.debug(
        f"[ENTER] download_file - Requested download for filename='{filename}'"
    )
    file_path: str = os.path.join(FINAL_OUTPUT_DIR, filename)
    logger.debug(f"[download_file] Constructed file_path='{file_path}'")

    if not os.path.isfile(file_path):
        logger.error(f"[download_file] File not found -> {file_path}")
        raise HTTPException(status_code=404, detail="file not found.")

    logger.info(f"[download_file] File found. Returning FileResponse -> {file_path}")
    logger.debug(f"[EXIT] download_file -> returning FileResponse for '{filename}'")
    return FileResponse(file_path, filename=filename)