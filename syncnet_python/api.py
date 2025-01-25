import os 
from fastapi import FastAPI, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from utils.log_utils import LogUtils
from utils.api_utils import ApiUtils
from settings import FINAL_OUTPUT_DIR



from run_postline import process_video
import logging

# Initialize Logging
logger = logging.getLogger('api_logger')

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
def process_endpoint(file = File(...)):
    """
    Processes the uploaded video file using the synchronization pipeline.
    Returns a JSON response with the output filename and a download URL.
    """
    # copying the file into the temp folder with an UUID4 name
    input_file_path = ApiUtils.save_temp_file(file)
    try:
        # calling the the process_video function from run_postline module and passing the copied temp file into it
        # which returns the path to the final shifted output
        final_shifted_output = process_video(input_file_path, file.filename)
        # uses os's path.exists method to check if the final path / final file exists
        if not os.path.exists(final_shifted_output):
            logger.error("Processing wasn't completed, final file hasn't been found.")
            raise HTTPException(status_code=500, detail="Processing failed.")
        logger.info(f"Fully processed file available at: {final_shifted_output}")
    except Exception as e:
        logger.error(f"The processing failed: {e}")
        raise HTTPException(status_code=500, detail="Processing failed.") from e
    # delete the temporary file 
    os.remove(input_file_path)

    corrected_filename = f"corrected_{file.filename}"
    download_url = f"/download/{corrected_filename}"
    # append the filename and download url to the json response and return it
    return JSONResponse(content={
        "filename": corrected_filename,
        "url": download_url
    })

@app.get("/download/{filename}")
def download_file(filename):
    # create the path to the final output file
    file_path = os.path.join(FINAL_OUTPUT_DIR, filename)
    # confirm that the path actually exists and is a file
    if not os.path.isfile(file_path):
        logger.error(f"file not found: {file_path}")
        raise HTTPException(status_code=404, detail="file not found.")
    # append the file_path, file name and content disposition header to to the file response and return it
    return FileResponse(
        path=file_path,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


 
@app.get("/")
def read_root():
    return {"message": "Welcome to sync-api"}
