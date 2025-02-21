from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
import os
import logging

from api.utils.api_utils import ApiUtils
from api.process_video import process_video

logger = logging.getLogger("processing_routes")
router = APIRouter()


@router.post("/process", tags=["processing"])
async def process_video_endpoint(file: UploadFile = File(...)):
    """
    Endpoint to process an uploaded video file.
    """
    input_file_path = await run_in_threadpool(ApiUtils.save_temp_file, file)
    try:
        result = await run_in_threadpool(process_video, input_file_path, file.filename)
        if isinstance(result, dict):
            return JSONResponse(content=result)
        if not result or not os.path.exists(result):
            logger.error("Processing failed. No final output generated.")
            raise HTTPException(status_code=500, detail="processing failed.")
        logger.info(f"File fully synced and ready for download at: {result}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="processing failed.") from e
    finally:
        if os.path.exists(input_file_path):
            await run_in_threadpool(os.remove, input_file_path)
    
    corrected_filename = f"corrected_{file.filename}"
    return JSONResponse(content={
        "filename": corrected_filename,
        "url": f"/download/{corrected_filename}"
    })
