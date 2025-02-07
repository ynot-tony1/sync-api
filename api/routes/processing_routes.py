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
      - saves the uploaded file to a temporary location
      - calls process_video to perform the syncnet processing
      - if process_video returns a dict (e.g. no audio or already in sync), returns it directly
      - otherwise, checks the path and returns the usual file info
    """
    input_file_path = ApiUtils.save_temp_file(file)
    try:
        result = process_video(input_file_path, file.filename)
         # if result comes back as a dict then return that from the function
        if isinstance(result, dict):
            return JSONResponse(content=result)
        # if result doesnt exist, raise a 500 error
        if not result or not os.path.exists(result):
            logger.error("processing failed. no final output generated.")
            raise HTTPException(status_code=500, detail="processing failed.")
        logger.info(f"file fully synced and ready for download at: {result}")
    except Exception as e:
        logger.error(f"an error occurred: {e}")
        raise HTTPException(status_code=500, detail="processing failed.") from e
    finally:
        # delete the uploaded file from the temp_input dir
        os.remove(input_file_path)
    corrected_filename = f"corrected_{file.filename}"
    return JSONResponse(content={
        "filename": corrected_filename,
        "url": f"/download/{corrected_filename}"
    })
