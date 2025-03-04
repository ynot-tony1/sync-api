from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from api.utils.api_utils import ApiUtils
from api.process_video import process_video
from api.types.props import ProcessSuccess, ProcessError
import os
import logging
from fastapi.concurrency import run_in_threadpool

logger: logging.Logger = logging.getLogger("processing_routes")
router: APIRouter = APIRouter()

@router.post("/process")
async def process_video_endpoint(file: UploadFile = File(...)) -> JSONResponse:
    """
    Processes an uploaded video file by invoking the video synchronization pipeline and returns a JSON response
    with either a download URL for the processed file or an appropriate status message.

    This endpoint performs the following steps:
      1. Saves the uploaded file to a temporary directory using ApiUtils.save_temp_file.
      2. Calls the asynchronous process_video function to process the video:
         - If the video is successfully processed and modified, verifies the existence of the final output file,
           extracts its filename, and returns a JSON response containing the filename and a download URL.
         - If the video is already synchronized, returns a JSON response with an appropriate message.
         - If an error occurs during processing, returns a JSON response with error details.
      3. In all cases, ensures that the temporary input file is deleted after processing, using a thread pool
         to handle the blocking I/O operation.

    Args:
        file (UploadFile): The uploaded video file received from the client.

    Returns:
        JSONResponse: A JSON response containing:
            - For successful processing:
                  {
                      "filename": "<final_output_filename>",
                      "url": "/download/<final_output_filename>"
                  }
            - For a video that is already in sync:
                  {
                      "message": "Your clip is already in sync."
                  }
            - For an error during processing:
                  A JSON object with error details as defined by the ProcessError Pydantic model.

    Raises:
        HTTPException: If the final output file is missing after processing, or if any unexpected error occurs
                       during the processing pipeline. The HTTP status code 500 is returned in such cases.

    Examples:
        To use this endpoint, a client would typically perform a POST request to /process with the video file:
        
        >>> import requests
        >>> files = {'file': open('video.mp4', 'rb')}
        >>> response = requests.post("http://localhost:8000/process", files=files)
        >>> print(response.json())
    """
    input_file_path: str = await ApiUtils.save_temp_file(file)
    try:
        result = await process_video(input_file_path, file.filename)
        if isinstance(result, ProcessSuccess):
            if result.status == "success" and result.final_output:
                if not os.path.exists(result.final_output):
                    logger.error("Final output file does not exist.")
                    raise HTTPException(status_code=500, detail="processing failed.")
                final_filename: str = os.path.basename(result.final_output)
                return JSONResponse(content={
                    "filename": final_filename,
                    "url": f"/download/{final_filename}"
                })
            elif result.status == "already_in_sync":
                return JSONResponse(content={
                    "message": result.message
                })
        elif isinstance(result, ProcessError):
            return JSONResponse(content=result.dict())
        
        logger.error("Unexpected result type from process_video.")
        raise HTTPException(status_code=500, detail="processing failed.")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="processing failed.") from e
    finally:
        if os.path.exists(input_file_path):
            await run_in_threadpool(os.remove, input_file_path)
