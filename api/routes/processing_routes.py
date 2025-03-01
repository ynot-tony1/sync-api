from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from api.utils.api_utils import ApiUtils
from api.process_video import process_video  # now async
import os
import logging
from fastapi.concurrency import run_in_threadpool

logger: logging.Logger = logging.getLogger("processing_routes")
router: APIRouter = APIRouter()

@router.post("/process")
async def process_video_endpoint(file: UploadFile = File(...)) -> JSONResponse:
    input_file_path: str = await run_in_threadpool(ApiUtils.save_temp_file, file)
    try:
        result = await process_video(input_file_path, file.filename)
        if isinstance(result, dict):
            if result.get("status") == "success" and "final_output" in result:
                final_filename: str = os.path.basename(result["final_output"])
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