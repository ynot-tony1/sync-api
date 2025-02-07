from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import logging
from api.utils.api_utils import ApiUtils
from api.process_video import process_video

logger = logging.getLogger("processing_routes")
router = APIRouter()

@router.post("/process", tags=["processing"])
async def process_video_endpoint(file: UploadFile = File(...)):
    """
    endpoint to process an uploaded video.
      - saves the uploaded file to a temporary location,
      - calls process_video to perform the syncnet processing,
      - if the first offset is 0, the function returns a dict with "already_in_sync",
      - otherwise, we get a final file path. if that path doesn't exist, processing failed.
    """
    input_file_path = ApiUtils.save_temp_file(file)
    try:
        result = process_video(input_file_path, file.filename)
        # if the result is a dict and it includes the already_in_sync key, its already in sync
        if isinstance(result, dict) and result.get("already_in_sync"):
            return JSONResponse(content=result)

        # if its none or doesn't exist, raise a 500 error
        if not result or not os.path.exists(result):
            logger.error("processing failed. no final output generated.")
            raise HTTPException(status_code=500, detail="processing failed.")
        logger.info(f"file fully synced and ready for download at: {result}")
    except Exception as e:
        logger.error(f"an error occurred: {e}")
        raise HTTPException(status_code=500, detail="processing failed.") from e
    finally:
        # delete originally uploaded file
        os.remove(input_file_path)

    corrected_filename = f"corrected_{file.filename}"
    return JSONResponse(content={
        "filename": corrected_filename,
        "url": f"/download/{corrected_filename}"
    })
