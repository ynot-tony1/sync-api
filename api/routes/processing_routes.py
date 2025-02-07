import os
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from api.utils.api_utils import ApiUtils
from api.process_video import process_video
from api.config.settings import FINAL_OUTPUT_DIR

logger = logging.getLogger("processing_routes")
router = APIRouter()

@router.post("/process", tags=["processing"])
async def process_video_endpoint(file: UploadFile = File(...)):
    """
    endpoint to process an uploaded video.
    - saves the uploaded file to a temporary location,
    - calls process_video to perform the syncnet processing,
    - returns the corrected filename and download url.
    """
    # save the uploaded file to my temp_input directory
    input_file_path = ApiUtils.save_temp_file(file)
    try:
        # process the uploaded file
        final_shifted_output = process_video(input_file_path, file.filename)
        if not os.path.exists(final_shifted_output):
            logger.error("no processed file, it must have failed.")
            raise HTTPException(status_code=500, detail="processing failed.")
        logger.info(f"file fully synced and ready for download at: {final_shifted_output}")
    except Exception as e:
        logger.error(f"an error happened: {e}")
        raise HTTPException(status_code=500, detail="processing failed.") from e
    finally:
        # remove the temporary file
        os.remove(input_file_path)
    # return the filename and download url to the front end by json
    corrected_filename = f"corrected_{file.filename}"
    return JSONResponse(content={
        "filename": corrected_filename,
        "url": f"/download/{corrected_filename}"
    })
