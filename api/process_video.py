# process_video.py
import logging
from typing import Dict, Union
from api.utils.api_utils import ApiUtils
from api.utils.syncnet_utils import SyncNetUtils

logger: logging.Logger = logging.getLogger('process_video')

async def process_video(input_file: str, original_filename: str) -> Dict[str, Union[str, bool]]:
    """Processes a video file by preparing it, synchronizing audio and video using SyncNet,
    and verifying the synchronization.

    Args:
        input_file (str): Path to the uploaded video file.
        original_filename (str): Original filename of the uploaded video.

    Returns:
        Dict[str, Union[str, bool]]: A dictionary containing either the final output path
            and a success message or error details.

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
        if isinstance(result_tuple, dict):
            return result_tuple
        final_output, already_in_sync = result_tuple

        if not already_in_sync:
            ref_str: str = f"{reference_number:05d}"
            await SyncNetUtils.verify_synchronization(final_output, ref_str, fps)
            ApiUtils.send_websocket_message("Done, click the orange box above to get your file! Thanks")
            return {
                "status": "success",
                "final_output": final_output,
                "message": "Video processed successfully."
            }
        else:
            ApiUtils.send_websocket_message("Your clip was already in sync. No changes were made.")
            return {
                "already_in_sync": True,
                "message": "Your clip is already in sync."
            }
    except Exception as e:
        error_msg: str = f"An error occurred during video processing: {e}"
        logger.error(error_msg)
        ApiUtils.send_websocket_message(error_msg)
        err_text: str = str(e)
        if "No audio stream" in err_text:
            return {"no_audio": True, "message": "The video you uploaded has no audio stream inside it"}
        elif "Couldn't find any video stream" in err_text:
            return {"no_video": True, "message": "Couldn't see any video stream in the file"}
        elif "retrieve fps" in err_text:
            return {"no_fps": True, "message": "Could not retrieve fps"}
        else:
            return {"error": True, "message": err_text}
