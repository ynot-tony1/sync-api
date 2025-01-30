from fastapi import FastAPI, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from api.utils.api_utils import ApiUtils
from api.config.settings import FINAL_OUTPUT_DIR, ALLOWED_LOCAL_1, ALLOWED_LOCAL_2
from syncnet_python.run_postline import process_video
import os
import logging

logger = logging.getLogger("fastapi")
uvicorn_access_logger = logging.getLogger("uvicorn.access")
app = FastAPI()

# define allowed origins for CORS
origins = [
    ALLOWED_LOCAL_1,
    ALLOWED_LOCAL_2,
]
app.add_middleware(CORSMiddleware)

@app.post("/process")
def process_endpoint(file=File(...)):
    # save the uploaded file to a temporary location
    input_file_path = ApiUtils.save_temp_file(file)
    try:
        # calling the the process_video function from run_postline module and passing the copied temp file into it
        # which returns the path to the final shifted output
        final_shifted_output = process_video(input_file_path, file.filename)

        # uses os's path.exists method to check if the final path / final file exists
        if not os.path.exists(final_shifted_output):
            logger.error("processing failed. no final output generated.")
            raise HTTPException(status_code=500, detail="processing failed.")
        logger.info(f"fully processed file available at: {final_shifted_output}")
    except Exception as e:
        logger.error(f"an error occurred: {e}")
        raise HTTPException(status_code=500, detail="processing failed.") from e
    finally:
            # delete the temporary file
            os.remove(input_file_path)
    corrected_filename = f"corrected_{file.filename}"
    # append the filename and download url to the json response and return it
    return JSONResponse(content={
        "filename": corrected_filename,
        "url": f"/download/{corrected_filename}"
    })


@app.get("/download/{filename}")
def download_file(filename):
    # create the file path for the requested file
    file_path = os.path.join(FINAL_OUTPUT_DIR, filename)
    logger.debug(f"download requested for file: {file_path}")
    # check if the file exists
    if not os.path.isfile(file_path):
        logger.error(f"file not found: {file_path}")
        raise HTTPException(status_code=404, detail="file not found.")
    logger.info(f"file download successful: {file_path}")
    # return the file as a response
    return FileResponse(file_path, filename=filename)

@app.get("/")
def read_root():
    # log when the root endpoint is accessed
    logger.info("root endpoint accessed.")
    return {"message": "Welcome to sync-api"}
