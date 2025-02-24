import os
import logging
from api.utils.api_utils import ApiUtils
from api.utils.syncnet_utils import SyncNetUtils

logger = logging.getLogger('process_video')

def process_video(input_file, original_filename):
    """
    Processes a video file to synchronize its audio and video streams using SyncNet.

    This function orchestrates the complete video processing workflow:
      1. Prepares the video for synchronization by copying, moving, and re-encoding 
         (if necessary) using SyncNet utilities.
      2. Iteratively applies audio shifts and finalizes the synchronization using
         the SyncNet pipeline.
      3. Sends websocket notifications to update the user about the processing progress.
      4. Returns a dictionary indicating success and includes the final output file path,
         or returns an error dictionary if processing fails.

    Args:
        input_file (str): The file path to the uploaded video that needs processing.
        original_filename (str): The original name of the uploaded video file.

    Returns:
        dict: A dictionary containing the outcome of the processing. On success, it contains:
            - "status": "success"
            - "final_output": <str> Final output file path after synchronization and re-encoding.
            - "message": "Video processed successfully."
            
            On failure, it returns one of the following error dictionaries:
            - {"no_audio": True, "message": "The video you uploaded has no audio stream inside"}
            - {"no_video": True, "message": "Couldn't see any video stream in the file"}
            - {"no_fps": True, "message": "Could not retrieve fps"}
            - {"error": True, "message": <error message>}

    Raises:
        This function does not raise exceptions directly. Instead, it catches exceptions,
        logs the error, sends a websocket notification, and returns an error dictionary.
    """
    try:
        avi_file, vid_props, audio_props, fps, destination_path, reference_number = SyncNetUtils.prepare_video(
            input_file, original_filename)
        
        result = SyncNetUtils.synchronize_video(
            avi_file, input_file, original_filename, vid_props, audio_props, fps, destination_path, reference_number
        )
        if isinstance(result, dict):
            return result
        ApiUtils.send_websocket_message("We're done, download your file with the link at the top! Thanks")
        return {
            "status": "success",
            "final_output": result,
            "message": "Video processed successfully."
        }

    except Exception as e:
        error_msg = f"An error occurred during video processing: {e}"
        logger.error(error_msg)
        ApiUtils.send_websocket_message(error_msg)
        err_text = str(e)
        if "No audio stream" in err_text:
            return {"no_audio": True, "message": "The video you uploaded has no audio stream inside"}
        elif "Couldn't find any video stream" in err_text:
            return {"no_video": True, "message": "Couldn't see any video stream in the file"}
        elif "retrieve fps" in err_text:
            return {"no_fps": True, "message": "Could not retrieve fps"}
        else:
            return {"error": True, "message": {e}}
