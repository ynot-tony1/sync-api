# api/routes/processing_routes.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import logging
from fastapi.concurrency import run_in_threadpool
from api.implementations.default_video_processor import DefaultVideoProcessor
from api.interfaces.video_processor import VideoProcessorInterface
from api.utils.api_utils import ApiUtils
from api.types.props import ProcessSuccess, ProcessError

router = APIRouter()
logger = logging.getLogger("processing_routes")

# Dependency function to provide an instance of the video processor
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
