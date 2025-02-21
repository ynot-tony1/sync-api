import os
import logging
from api.utils.api_utils import ApiUtils
from api.utils.file_utils import FileUtils
from api.utils.ffmpeg_utils import FFmpegUtils
from api.utils.syncnet_utils import SyncNetUtils
from api.utils.analysis_utils import AnalysisUtils
from api.config.settings import (
    DEFAULT_MAX_ITERATIONS, TEMP_PROCESSING_DIR, DEFAULT_TOLERANCE_MS, FINAL_LOGS_DIR, 
    FINAL_OUTPUT_DIR, DATA_WORK_PYAVI_DIR
)

logger = logging.getLogger('process_video')

def process_video(input_file, original_filename):
    try:
        logger.info("Starting the process video function")
        ApiUtils.send_websocket_message("Here we go...")
        ApiUtils.send_websocket_message("Setting up our filing system...")
        reference_number = int(FileUtils.get_next_directory_number(DATA_WORK_PYAVI_DIR))
        ApiUtils.send_websocket_message("Copying your file to work on...")

        temp_copy_path = FileUtils.copy_input_to_temp(input_file, original_filename)
        destination_path = FileUtils.move_to_data_work(temp_copy_path, reference_number)

        if not os.path.exists(destination_path):
            error_msg = f"Destination file {destination_path} doesn't exist. Aborting process."
            logger.error(error_msg)
            ApiUtils.send_websocket_message(error_msg)
            return None

        vid_props = FFmpegUtils.get_video_properties(input_file)
        if vid_props is None:
            error_msg = "Couldn't find any video stream"
            logger.error(error_msg)
            ApiUtils.send_websocket_message(error_msg)
            return {"no_video": True, "message": "Couldn't see any video stream in the file"}

        fps = FFmpegUtils.get_video_fps(input_file)
        if fps is None:
            error_msg = "Could not retrieve fps"
            logger.error(error_msg)
            ApiUtils.send_websocket_message(error_msg)
            return {"no_fps": True, "message": "Could not retrieve fps"}

        ApiUtils.send_websocket_message("Finding out about your file...")
        audio_props = FFmpegUtils.get_audio_properties(input_file)
        if audio_props is None:
            error_msg = "No audio stream found in the video."
            logger.error(error_msg)
            ApiUtils.send_websocket_message(error_msg)
            return {"no_audio": True, "message": "The video you uploaded has no audio stream inside"}

        total_shift_ms = 0
        corrected_file = destination_path

        ApiUtils.send_websocket_message("Ok, had a look; let's begin to sync...")

        for iteration in range(DEFAULT_MAX_ITERATIONS):
            iteration_msg = f"Pass number {iteration + 1} in progress..."
            logger.info(iteration_msg)
            ApiUtils.send_websocket_message(iteration_msg)

            ref_str = f"{reference_number:05d}"
            ApiUtils.send_websocket_message("Running the pipeline...")
            SyncNetUtils.run_pipeline(corrected_file, ref_str)

            ApiUtils.send_websocket_message("Running the model...")
            log_file = SyncNetUtils.run_syncnet(ref_str)

            ApiUtils.send_websocket_message("Analyzing the results that came back...")
            offset_ms = AnalysisUtils.analyze_syncnet_log(log_file, fps)

            if offset_ms > 0:
                debug_msg = f"Your clip is currently {offset_ms} ms ahead of the video"
            elif offset_ms < 0:
                debug_msg = f"Your clip is {abs(offset_ms)} ms behind the video"
            else:
                if iteration == 0:
                    ApiUtils.send_websocket_message("Your clip is already in sync")
                    return {"already_in_sync": True, "message": "already in sync"}
                else:
                    ApiUtils.send_websocket_message("Clip is now perfectly in sync; finishing...")
                    break

            ApiUtils.send_websocket_message(debug_msg)

            total_shift_ms += offset_ms
            offset_msg = f"Total shift after pass {iteration + 1} will be {total_shift_ms} ms."
            logger.info(offset_msg)
            ApiUtils.send_websocket_message(offset_msg)

            new_corrected_file = os.path.join(
                TEMP_PROCESSING_DIR,
                f"corrected_iter{iteration + 1}_{original_filename}"
            )
            ApiUtils.send_websocket_message("Adjusting the streams in your file...")
            FFmpegUtils.shift_audio(corrected_file, new_corrected_file, offset_ms)
            if not os.path.exists(new_corrected_file):
                error_msg = f"Corrected file {new_corrected_file} was not created. Aborting process."
                logger.error(error_msg)
                ApiUtils.send_websocket_message(error_msg)
                return None

            corrected_file = new_corrected_file
            reference_number += 1

        final_output_path = os.path.join(FINAL_OUTPUT_DIR, f"corrected_{original_filename}")
        ApiUtils.send_websocket_message("Making the final shift...")
        FFmpegUtils.apply_cumulative_shift(input_file, final_output_path, total_shift_ms)
        ApiUtils.send_websocket_message("Double checking everything...")

        # Final verification
        AnalysisUtils.verify_synchronization(
            final_output_path, f"{reference_number:05d}", fps, DEFAULT_TOLERANCE_MS
        )

        final_log = os.path.join(FINAL_LOGS_DIR, f"final_output_{reference_number:05d}.log")
        final_offset = AnalysisUtils.analyze_syncnet_log(final_log, fps)
        if final_offset != 0:
            ApiUtils.send_websocket_message(
                f"Final offset is {final_offset} ms; applying final correction to reach 0 offset..."
            )
            corrected_final_output = os.path.join(
                FINAL_OUTPUT_DIR, f"corrected_final_{original_filename}"
            )
            FFmpegUtils.apply_cumulative_shift(final_output_path, corrected_final_output, final_offset)
            final_output_path = corrected_final_output

        # Clean up
        if corrected_file != destination_path and os.path.exists(corrected_file):
            os.remove(corrected_file)

        ApiUtils.send_websocket_message("We're done, download your file with the link at the top! Thanks")
        return final_output_path

    except Exception as e:
        error_msg = f"An error occurred during video processing: {e}"
        logger.error(error_msg)
        ApiUtils.send_websocket_message(error_msg)
        return None
