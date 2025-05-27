import logging
from typing import Dict, Union
from api.utils.api_utils import ApiUtils
from api.utils.syncnet_utils import SyncNetUtils
from api.types.props import SyncError, ProcessSuccess, ProcessError
logger: logging.Logger = logging.getLogger('process_video')

"""
Module: process_video
Description:
    This module processes a video file by preparing it, synchronizing its audio and video streams using SyncNet,
    and verifying the final synchronization. It leverages asynchronous programming with asyncio to ensure that
    I/O-bound operations (such as reading/writing files and invoking external processes) do not block the event loop.
    Blocking operations (e.g., file operations) are delegated to a thread pool to maintain responsiveness.

Overview:
    The main function, process_video, orchestrates the following workflow:
      1. **Video Preparation:** 
         - Converts the input video to AVI format if required.
         - Retrieves video and audio properties using asynchronous FFmpeg utilities.
         - Copies/moves files using thread pool execution to avoid blocking.
      2. **Synchronization:**
         - Invokes the SyncNet pipeline and model asynchronously to determine audio-video offset.
         - Performs iterative synchronization adjustments if the video is out-of-sync.
      3. **Verification:**
         - Verifies the final synchronization by running a verification pipeline.
      4. **Broadcasting Updates:**
         - Sends status messages via WebSocket to inform clients of progress.

Concurrency and Threading:
    - **Asynchronous Operations:** 
        All major processing steps are implemented as async functions. This allows the use of non-blocking I/O
        (e.g., reading files with aiofiles, running FFmpeg commands with asyncio.create_subprocess_exec).
    - **Thread Pool Execution:**
        Blocking file system operations (such as copying, moving, or deleting files) are executed using:
            - `asyncio.get_running_loop().run_in_executor()`
            - FastAPI's `run_in_threadpool`
        This integration of threading prevents these operations from stalling the asynchronous event loop.
    - **Task Management and Cancellation:**
        The code sets up proper cancellation points and error propagation to handle scenarios where the
        processing pipeline needs to be cancelled or encounters errors.

Function:
    async def process_video(input_file: str, original_filename: str) -> Dict[str, Union[str, bool]]:
        Processes the input video file by preparing it, synchronizing its audio and video, and verifying the
        final synchronization status. It returns a dictionary with either a success message and the final output
        path or error details in case of failure.

    Args:
        input_file (str): The file system path to the uploaded video file.
        original_filename (str): The original name of the uploaded video file.

    Returns:
        Dict[str, Union[str, bool]]:
            - On success:
                {
                    "status": "success",
                    "final_output": "<path to the processed file>",
                    "message": "Video processed successfully."
                }
            - If the video is already synchronized:
                {
                    "already_in_sync": True,
                    "message": "Your clip is already in sync."
                }
            - On error (e.g., missing audio stream, video stream, or fps):
                {
                    "error": True,
                    "message": "<error details>"
                }

    Raises:
        RuntimeError: Propagates any error encountered during video processing.

Usage Example:
    async def main():
        result = await process_video("path/to/video.mp4", "video.mp4")
        if result.get("status") == "success":
            print("Video processed successfully:", result["final_output"])
        else:
            print("Error processing video:", result.get("message"))
    
To run the asynchronous main function, use:
    import asyncio
    asyncio.run(main())
"""

async def process_video(input_file: str, original_filename: str) -> Union[ProcessSuccess, ProcessError]:
    """
    Processes a video file by preparing it, synchronizing its audio and video using SyncNet, and verifying 
    the synchronization.

    The function implements an asynchronous pipeline that:
      1. Prepares the video by copying/moving the file to the appropriate directory, extracting video 
         and audio properties, and converting it to AVI format if necessary. Blocking file operations are 
         executed via a thread pool.
      2. Synchronizes the video using the SyncNet pipeline:
         - Invokes asynchronous methods to run the SyncNet model and pipeline.
         - Iteratively adjusts the video based on the computed audio-video offset.
      3. Verifies the final synchronization by running an asynchronous verification process.
      4. Sends WebSocket messages to broadcast status updates to the client throughout the process.

    Concurrency and Threading:
      - **Asynchronous Execution:** 
            Utilizes async/await syntax and asyncio's subprocess management to run external commands (e.g., FFmpeg,
            SyncNet) without blocking the event loop.
      - **Thread Pool Usage:** 
            File I/O operations that are blocking are offloaded to a thread pool using methods such as 
            `run_in_threadpool` to ensure the asynchronous workflow remains responsive.
      - **Cooperative Cancellation:** 
            The function provides cancellation points where asynchronous operations can be safely cancelled,
            ensuring that resources are properly cleaned up on exit.
      
    Args:
        input_file (str): Path to the uploaded video file.
        original_filename (str): Original filename of the uploaded video.

    Returns:
        Dict[str, Union[str, bool]]:
            - If processing is successful:
                {
                    "status": "success",
                    "final_output": "<final output file path>",
                    "message": "Video processed successfully."
                }
            - If the video is already synchronized:
                {
                    "already_in_sync": True,
                    "message": "Your clip is already in sync."
                }
            - In case of an error (e.g., missing audio/video streams, fps retrieval issues):
                {
                    "error": True,
                    "message": "<error details>"
                }

    Raises:
        RuntimeError: Propagates any error encountered during processing.
    """
    try:
        avi_file, vid_props, audio_props, fps, destination_path, reference_number = await SyncNetUtils.prepare_video(
            input_file, original_filename
        )
        result_tuple = await SyncNetUtils.synchronize_video(
            avi_file, input_file, original_filename, vid_props, audio_props, fps, destination_path, reference_number
        )
        if isinstance(result_tuple, SyncError):
            return ProcessError(
                error=True,
                message=result_tuple.message,
                no_audio=False,
                no_video=False,
                no_fps=False
            )
        
        final_output, already_in_sync = result_tuple
        if not already_in_sync:
            ref_str: str = f"{reference_number:05d}"
            await SyncNetUtils.verify_synchronization(final_output, ref_str, fps)
            ApiUtils.send_websocket_message("Click the orange circle tick below to get your file! Thanks")
            return ProcessSuccess(
                status="success",
                final_output=final_output,
                message="Video processed successfully."
            )
        else:
            ApiUtils.send_websocket_message("Your clip was already in sync. No changes were made.")
            return ProcessSuccess(
                status="already_in_sync",
                final_output="",
                message="Your clip is already in sync."
            )
    except Exception as e:
        error_msg: str = f"An error occurred during video processing: {e}"
        logger.error(error_msg)
        ApiUtils.send_websocket_message(error_msg)
        err_text: str = str(e)
        if "No audio stream" in err_text:
            return ProcessError(
                error=True,
                no_audio=True,
                message="The video you uploaded has no audio stream inside it"
            )
        elif "Couldn't find any video stream" in err_text:
            return ProcessError(
                error=True,
                no_video=True,
                message="Couldn't see any video stream in the file"
            )
        elif "retrieve fps" in err_text:
            return ProcessError(
                error=True,
                no_fps=True,
                message="Could not retrieve fps"
            )
        else:
            return ProcessError(
                error=True,
                message=err_text
            )
