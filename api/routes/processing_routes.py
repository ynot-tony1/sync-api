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
    Endpoint to process an uploaded video.
    - Save the uploaded file to a temporary location which is blocking; offload to thread pool)
    - Calling the process_video fucntion which is CPU/IO-bound; offloaded to thread pool)
    - Return the result by json
    """
    # offloading the saving of the temp file to a thread pool
    input_file_path = await run_in_threadpool(ApiUtils.save_temp_file, file)
    try:
        # offloading the whole process_video function to a thread pool
        result = await run_in_threadpool(process_video, input_file_path, file.filename)
        # if the result is a dict, return it as json
        if isinstance(result, dict):
            return JSONResponse(content=result)
        # if the processing returned no path or the file doesn't exist, its an error
        if not result or not os.path.exists(result):
            logger.error("Processing failed. No final output generated.")
            raise HTTPException(status_code=500, detail="processing failed.")
        logger.info(f"File fully synced and ready for download at: {result}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="processing failed.") from e
    finally:
        # offloading the file clean up to a thread pool
        if os.path.exists(input_file_path):
            await run_in_threadpool(os.remove, input_file_path)
    # if successful, returns the path to the corrected file by json for download 
    corrected_filename = f"corrected_{file.filename}"
    return JSONResponse(content={
        "filename": corrected_filename,
        "url": f"/download/{corrected_filename}"
    })
