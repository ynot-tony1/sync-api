from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import logging
from fastapi.concurrency import run_in_threadpool
from api.implementations.default_video_processor import DefaultVideoProcessor
from api.interfaces.video_processor import VideoProcessorInterface
from api.utils.api_utils import ApiUtils

router = APIRouter()
logger = logging.getLogger("processing_routes")
"""

FastAPI route definitions for handling media-file upload, synchronisation, and
download-link generation.

This module exposes a single **POST** endpoint, **`/process`**, that accepts a
multipart-encoded video file, forwards it to the core processing pipeline, and
returns a JSON payload describing either the corrected video’s download
location or a structured error.  It acts as the glue between the HTTP layer
and the asynchronous `process_video` orchestration implemented deeper in the
service.

--------------------------------------
1.  **Persist upload** – Streams the incoming `UploadFile` to a temporary
    location using `ApiUtils.save_temp_file`, ensuring no blocking I/O on the
    event loop.
2.  **Delegate processing** – Instantiates a `VideoProcessorInterface`
    (currently `DefaultVideoProcessor`) via FastAPI’s dependency-injection
    system and awaits `process_video(...)`, which performs:
        • format/codec inspection & optional AVI re-encode  
        • SyncNet pipeline + iterative audio-shift passes  
        • cumulative shift and final verification  
        • optional re-encode back to the original container
3.  **Interpret result models** – Consumes either `ProcessSuccess` or
    `ProcessError` Pydantic models and shapes the appropriate `JSONResponse`.
4.  **Housekeeping** – Deletes the temporary upload file in a thread-pool to
    avoid blocking, regardless of success or failure.

Module-level variables
----------------------
`router`  
    FastAPI `APIRouter` instance whose prefix is defined by the parent package.

`logger`  
    `logging.Logger` scoped to “processing_routes”; mirrors log-level settings
    from the shared logging configuration.

Examples
--------
Typical successful call/response cycle:

```bash
$ curl -F "file=@example.mp4" http://localhost:8000/process
{
  "filename": "corrected_example.mp4",
  "url": "/download/corrected_example.mp4"
}
"""

def get_video_processor() -> VideoProcessorInterface:
    return DefaultVideoProcessor()

@router.post("/process")
async def process_video_endpoint(
    file: UploadFile = File(...),
    video_processor: VideoProcessorInterface = Depends(get_video_processor)
) -> JSONResponse:
    input_file_path: str = await ApiUtils.save_temp_file(file)
    try:
        result = await video_processor.process_video(input_file_path, file.filename)
        if hasattr(result, "status") and result.status == "success" and result.final_output:
            if not os.path.exists(result.final_output):
                logger.error("Final output file does not exist.")
                raise HTTPException(status_code=500, detail="processing failed.")
            final_filename: str = os.path.basename(result.final_output)
            return JSONResponse(content={
                "filename": final_filename,
                "url": f"/download/{final_filename}"
            })
        elif hasattr(result, "status") and result.status == "already_in_sync":
            return JSONResponse(content={"message": result.message})
        elif hasattr(result, "error") and result.error:
            return JSONResponse(content=result.dict())
        logger.error("Unexpected result type from process_video.")
        raise HTTPException(status_code=500, detail="processing failed.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="processing failed.") from e
    finally:
        if os.path.exists(input_file_path):
            await run_in_threadpool(os.remove, input_file_path)
