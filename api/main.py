from fastapi import FastAPI, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from api.utils.api_utils import ApiUtils
from api.config.settings import FINAL_OUTPUT_DIR
from syncnet_python.run_postline import process_video

import os
import logging

# Configure loggers
logger = logging.getLogger("fastapi")
uvicorn_access_logger = logging.getLogger("uvicorn.access")

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process")
def process_endpoint(file=File(...)):
    logger.info("Received a file for processing.")
    input_file_path = ApiUtils.save_temp_file(file)
    logger.debug(f"File saved temporarily at {input_file_path}")
    try:
        final_shifted_output = process_video(input_file_path, file.filename)
        if not os.path.exists(final_shifted_output):
            logger.error(f"Processing failed. Output file not found: {final_shifted_output}")
            raise HTTPException(status_code=500, detail="Processing failed.")
        logger.info(f"Processing successful. Output saved at {final_shifted_output}")
    except Exception as e:
        logger.exception("An error occurred during processing.")
        raise HTTPException(status_code=500, detail="Processing failed.") from e
    finally:
        os.remove(input_file_path)
        logger.debug(f"Temporary file deleted: {input_file_path}")

    corrected_filename = f"corrected_{file.filename}"
    download_url = f"/download/{corrected_filename}"
    logger.info(f"File processed successfully. Available for download at {download_url}")
    return JSONResponse(content={"filename": corrected_filename, "url": download_url})

@app.get("/download/{filename}")
def download_file(filename):
    file_path = os.path.join(FINAL_OUTPUT_DIR, filename)
    logger.debug(f"Download requested for file: {file_path}")
    if not os.path.isfile(file_path):
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail="File not found.")
    logger.info(f"File download successful: {file_path}")
    return FileResponse(file_path, filename=filename)

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed.")
    return {"message": "Welcome to sync-api"}
