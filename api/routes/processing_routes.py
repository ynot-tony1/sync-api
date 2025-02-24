from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
import os
import logging

from api.utils.api_utils import ApiUtils
from api.process_video import process_video

logger = logging.getLogger("processing_routes")
router = APIRouter()

@router.post("/process")
async def process_video_endpoint(file: UploadFile = File(...)):
    """
    Processes an uploaded video file and returns a download link for the processed video.

    This endpoint performs the following workflow:
      1. Saves the uploaded file temporarily using ApiUtils.
      2. Invokes the process_video function to perform video synchronization.
      3. If processing is successful, extracts the final output filename and constructs
         a download URL in the format "/download/<final_filename>".
      4. Returns a JSON response containing the filename and download URL.
      5. In the event of an error or if processing fails, returns an error response.

    Args:
        file (UploadFile): The video file uploaded by the client.

    Returns:
        JSONResponse: A JSON object with either:
            - On success:
                {
                    "filename": "<final_filename>",
                    "url": "/download/<final_filename>"
                }
            - On failure, an error dictionary describing the issue.

    Raises:
        HTTPException: If the processing fails or no final output is generated.
    """
    input_file_path = await run_in_threadpool(ApiUtils.save_temp_file, file)
    try:
        result = await run_in_threadpool(process_video, input_file_path, file.filename)
        
        if isinstance(result, dict):
            if result.get("status") == "success" and "final_output" in result:
                final_filename = os.path.basename(result["final_output"])
                return JSONResponse(content={
                    "filename": final_filename,
                    "url": f"/download/{final_filename}"
                })
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
    final_filename = os.path.basename(result)
    return JSONResponse(content={
        "filename": final_filename,
        "url": f"/download/{final_filename}"
    })
