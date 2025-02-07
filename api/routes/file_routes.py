import os
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from api.config.settings import FINAL_OUTPUT_DIR

logger = logging.getLogger("file_routes")
router = APIRouter()

@router.get("/download/{filename}", tags=["files"])
def download_file(filename: str):
    """
    endpoint to download a processed video file.
    - constructs the file path based on FINAL_OUTPUT_DIR,
    - returns the file if it exists, otherwise raises a 404 error.
    """
    # conbine the path of the final output dir with the provided filename to construct the file path
    file_path = os.path.join(FINAL_OUTPUT_DIR, filename)
        # raises a 404 to the front end if the file doesnt exist
    if not os.path.isfile(file_path):
        logger.error(f"file not found: {file_path}")
        raise HTTPException(status_code=404, detail="file not found.")
    logger.info(f"file download successful: {file_path}")
    # returns the file and its filename in the response as a downloadable file
    return FileResponse(file_path, filename=filename)
