import os
import logging
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from api.utils.api_utils import ApiUtils
from api.config.settings import FINAL_OUTPUT_DIR
from api.process_video import process_video

logger = logging.getLogger("fastapi")
app = FastAPI()

# setup cors.
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
async def process_endpoint(file: UploadFile = File(...)):
    # save the uploaded file to a temporary location.
    input_file_path = ApiUtils.save_temp_file(file)
    try:
        # process the video using our new control flow.
        final_shifted_output = process_video(input_file_path, file.filename)

        if not final_shifted_output or not os.path.exists(final_shifted_output):
            logger.error("processing failed. no final output generated.")
            raise HTTPException(status_code=500, detail="processing failed.")
        logger.info(f"file fully processed and available at: {final_shifted_output}")
    except Exception as e:
        logger.error(f"an error occurred: {e}")
        raise HTTPException(status_code=500, detail="processing failed.") from e
    finally:
        # clean up the temporary file.
        os.remove(input_file_path)

    corrected_filename = f"corrected_{file.filename}"
    # return the json response with the file info.
    return JSONResponse(content={
        "filename": corrected_filename,
        "url": f"/download/{corrected_filename}"
    })

@app.get("/download/{filename}")
def download_file(filename: str):
    # create the file path for the requested file.
    file_path = os.path.join(FINAL_OUTPUT_DIR, filename)
    # check if the file exists.
    if not os.path.isfile(file_path):
        logger.error(f"file not found: {file_path}")
        raise HTTPException(status_code=404, detail="file not found.")
    logger.info(f"file download successful: {file_path}")
    # return the file as a response.
    return FileResponse(file_path, filename=filename)

@app.get("/")
def read_root():
    # log when the root endpoint is accessed.
    logger.info("root endpoint accessed.")
    return {"message": "welcome to sync-api"}
