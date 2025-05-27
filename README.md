# SyncNet API

This project is an API for synchronizing audio and video in uploaded files using a SyncNet-based pipeline. The API orchestrates the video processing workflow by receiving an upload, performing multiple iterations of synchronization (via file copying, re-encoding, and audio shifting), and finally returning a processed file that is synchronized.
Table of Contents

    Overview
    Directory Structure
    Environment Variables
    Main Control Flow
    API Endpoints
    Installation and Running
    Development Notes
    Logging and Debugging
    License

## Overview

The SyncNet API is built on FastAPI and leverages a SyncNet pipeline for video processing. The core workflow is implemented in the process_video module. It handles the following tasks:

    File Upload and Temporary Storage:
    The API accepts a video file (preferably in AVI format) and saves it temporarily.

    Video Preparation:
    The video is prepared by copying and moving it to a working directory. The preparation phase extracts video properties (such as FPS) and audio properties. If needed, the video is re-encoded to an AVI container using FFmpeg.

## Iterative Synchronization:
    The API iteratively calls the SyncNet pipeline:
        It runs the pipeline and then analyzes the output logs to determine the required audio shift.
        If the audio and video are out of sync, it applies incremental audio shifts using FFmpeg.
        These iterations continue until the audio offset is zero or a maximum number of iterations is reached.

    Finalization and Re-Encoding:
    Once synchronization is achieved, the API performs a final audio shift and, if necessary, re-encodes the final output back to the original container format (e.g., MP4).

    Notification via WebSockets:
    Throughout the process, the API sends real-time notifications to the client via WebSocket connections.

    Download Endpoint:
    The final processed file is made available via a download endpoint.

## Directory Structure

Below is a simplified view of the directory structure (excluding third-party modules such as node_modules):
'''
sync-api
│
├── api
│   ├── config
│   │   ├── logging.yaml
│   │   ├── settings.py
│   │   └── type_settings.py    # Typed environment variables for type safety
│   ├── connection_manager.py   # Handles WebSocket connections
│   ├── file_handling           # Contains directories for temporary and final files
│   ├── logs                    # Log files are stored here
│   ├── main.py                 # Main FastAPI application
│   ├── process_video.py        # Main control flow for processing a video
│   ├── routes                # API endpoints
│   │   ├── file_routes.py      # Download endpoint for processed files
│   │   ├── processing_routes.py # Endpoint to trigger video processing
│   │   └── ws_routes.py        # WebSocket endpoint for real-time updates
│   └── utils                   # Utility modules for various processing steps
│       ├── analysis_utils.py   # Analyzes SyncNet log output
│       ├── api_utils.py        # Helper for API operations, temporary file handling, notifications
│       ├── ffmpeg_utils.py     # Functions wrapping FFmpeg calls for re-encoding and shifting audio
│       ├── file_utils.py       # File operations (copying, moving, cleanup)
│       ├── log_utils.py        # Logging configuration and helpers
│       ├── syncnet_utils.py    # Orchestrates SyncNet pipeline, synchronization, and finalization
│       └── ws_logging_handler.py # Custom WebSocket logging handler
├── syncnet_python              # Contains the SyncNet model and related processing scripts
└── ... (Other project files and scripts)

'''

## Environment Variables

The API uses a set of environment variables to configure logging directories, processing directories, constants, and allowed origins. These variables are loaded in api/config/settings.py and then re-exported as typed constants in api/config/type_settings.py. Key variables include:

- ##   Logging Directories:
        LOGS_BASE
        LOGS_DIR
        FINAL_LOGS_DIR
        RUN_LOGS_DIR
        LOG_CONFIG_PATH

- ##   Processing Directories:
        FILE_HANDLING_DIR
        TEMP_PROCESSING_DIR
        FINAL_OUTPUT_DIR
        DATA_WORK_PYAVI_DIR
        DATA_WORK_DIR
        DATA_DIR

- ##   Processing Constants:
        DEFAULT_MAX_ITERATIONS

- ##   Allowed CORS Origins:
        ALLOWED_LOCAL_1
        ALLOWED_LOCAL_2

The frontend uses additional environment variables (prefixed with NEXT_PUBLIC_) to determine the backend URL, authentication endpoints, and more.
Main Control Flow

The primary video processing workflow is managed in the api/process_video.py module. The flow is as follows:

## Receive Upload:
    The /process endpoint (defined in api/routes/processing_routes.py) receives an uploaded video file.

##  Temporary File Handling:
    ApiUtils.save_temp_file saves the file in a temporary directory, ensuring a unique name using a UUID.

- ##  Video Preparation:
    SyncNetUtils.prepare_video performs the following:
        Copies the file to a temporary working directory.
        Moves the file into the processing directory and assigns a reference number.
        Extracts video and audio properties (via FFmpeg).
        Re-encodes the file to AVI if necessary.

- ##  Synchronization Iterations:
    SyncNetUtils.synchronize_video:
        Calls SyncNetUtils.perform_sync_iterations to run multiple iterations.
        Each iteration runs the SyncNet pipeline, analyzes the resulting log, and calculates the required audio offset.
        If an offset is found, FFmpegUtils.shift_audio is used to adjust the audio.

##  Finalization:
    SyncNetUtils.finalize_sync applies the cumulative audio shift and, if needed, re-encodes the file back to its original container.

    Notifications:
    Throughout the process, ApiUtils.send_websocket_message sends real-time status updates to connected WebSocket clients.

    Return Result:
    On success, a JSON response is returned with the final output file’s name and a download URL (provided by the /download/{filename} endpoint).

## API Endpoints
1. Process Video Endpoint

    URL: /process
    Method: POST
    Description: Accepts an uploaded video file, processes it through the SyncNet pipeline, and returns a download URL.
    Request:
        File upload (multipart/form-data)
    Response:
        Success: { "status": "success", "final_output": "<file_path>", "message": "Video processed successfully." }
        Error: { "error": true, "message": "<error details>" }

2. Download Endpoint

    URL: /download/{filename}
    Method: GET
    Description: Serves the final processed file for download.
    Response:
        A file download response or HTTP 404 if the file is not found.

3. WebSocket Endpoint

    URL: /ws
    Description: Establishes a WebSocket connection to send real-time processing updates.
    Usage:
        The frontend creates a WebSocket connection to receive log messages and status updates during video processing.

## Installation and Running
Prerequisites

- ## Python 3.7+
    (Note: For Python 3.7, install typing_extensions for support of Final.)
    Node.js and npm/yarn for the frontend.
    FFmpeg must be installed and available in the system path.
    Virtual environment (recommended).

## Backend Setup

## Clone the repository:

git clone https://github.com/yourusername/syncnet-api.git
cd syncnet-api

## Create and activate a virtual environment:

python3 -m venv venv
source venv/bin/activate

Install Python dependencies:

pip install -r requirements.txt

## Configure environment variables:
Create a .env file in the project root (if not already provided) with your required variables.

## Run the API server using Uvicorn:

    uvicorn api.main:app --reload

## Frontend Setup

    Navigate to the frontend directory (if separate) and install dependencies:

- ## npm install
# or
- ## yarn install

Run the frontend development server:

- ## npm run dev
    # or
- ## yarn dev

Ensure that the frontend’s environment variables (e.g., NEXT_PUBLIC_BACKEND_URL) point to your backend server (usually http://localhost:8000).
## Development Notes

    Type Safety:
    The project uses explicit type annotations (with help from typing_extensions on Python 3.7) to ensure consistency and early error detection.

    Modularity:
    The API is structured into logical modules:
        Utils: Contains helper functions for logging, file handling, FFmpeg operations, and SyncNet pipeline orchestration.
        Routes: Define REST endpoints and WebSocket connections.
        Configuration: Environment variables are centralized in settings.py and re-exported as typed constants in type_settings.py.

    SyncNet Pipeline:
    The core synchronization functionality is implemented in SyncNetUtils (found in api/utils/syncnet_utils.py). It integrates multiple iterations, log analysis, and cumulative audio shifting.

## Logging and Debugging

    Logging Configuration:
    The logging is configured via a YAML file (api/config/logging.yaml) and applied through LogUtils.configure_logging(). Logs are written to dedicated files under the api/logs directory.

    Debugging Tips:
        Check log files in the api/logs directory for errors.
        Use the WebSocket connection (monitored by the frontend) to see real-time status updates.
        If file processing fails, inspect the logs generated by the SyncNet pipeline for clues.

License

This project is licensed under the MIT License.

