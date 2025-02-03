import os
import logging
from api.utils.file_utils import FileUtils
from api.utils.ffmpeg_utils import FFmpegUtils
from api.utils.syncnet_utils import SyncNetUtils
from api.utils.analysis_utils import AnalysisUtils
from api.config.settings import (
    RUN_LOGS_DIR, LOGS_DIR, FINAL_LOGS_DIR, DEFAULT_MAX_ITERATIONS,
    DEFAULT_TOLERANCE_MS, TEMP_PROCESSING_DIR, DATA_WORK_PYAVI_DIR,
    FINAL_OUTPUT_DIR
)

logger = logging.getLogger('run_postline')

def process_video(input_file, original_filename):
    """
    synchronizes a video file by processing it through the syncnet pipeline.
    this function:
      - prepares necessary directories.
      - copies the input file to a temporary folder.
      - moves the file to the pipeline’s data directory.
      - retrieves the video's fps.
      - runs a series of iterations to sync audio and video.
      - applies a cumulative shift to generate the final synchronized video.
    
    returns:
        str or none: path to the final synchronized video, or none if processing failed.
    """
    try:
        logger.info("starting video synchronization process...")

        # ensure all required directories exist.
        directories = [
            LOGS_DIR, RUN_LOGS_DIR, FINAL_LOGS_DIR, TEMP_PROCESSING_DIR,
            DATA_WORK_PYAVI_DIR, FINAL_OUTPUT_DIR
        ]
        FileUtils.prepare_directories(directories)

        # get the next directory reference number.
        reference_number = int(FileUtils.get_next_directory_number())

        # copy input to temp and move it into the data work directory.
        temp_copy_path = FileUtils.copy_input_to_temp(input_file, original_filename)
        destination_path = FileUtils.move_to_data_work(temp_copy_path, reference_number)

        if not os.path.exists(destination_path):
            logger.error(f"destination file {destination_path} does not exist. aborting process.")
            return None

        # get the fps of the video.
        fps = FFmpegUtils.get_video_fps(input_file)
        if fps is None:
            logger.error("could not retrieve fps from the video. aborting process.")
            return None

        total_shift_ms = 0
        current_file_path = destination_path

        # iterate through sync steps.
        for iteration in range(DEFAULT_MAX_ITERATIONS):
            logger.info(f"--- synchronization iteration {iteration + 1} ---")
            ref_str = f"{reference_number:05d}"

            # run the pipeline and then the syncnet model.
            SyncNetUtils.run_pipeline(current_file_path, ref_str)
            log_file = SyncNetUtils.run_syncnet(ref_str)

            # analyze the log to get the offset.
            offset_ms = AnalysisUtils.analyze_syncnet_log(log_file, fps)
            total_shift_ms += offset_ms
            logger.info(f"total shift after iteration {iteration + 1}: {total_shift_ms} ms")

            # if the offset is acceptable, break out of the loop.
            if abs(offset_ms) <= DEFAULT_TOLERANCE_MS:
                logger.info("synchronization offset is within the acceptable tolerance.")
                break

            # apply the offset shift for the next iteration.
            corrected_file = os.path.join(
                TEMP_PROCESSING_DIR,
                f"corrected_iter{iteration + 1}_{original_filename}"
            )
            FFmpegUtils.shift_audio(current_file_path, corrected_file, offset_ms)

            if not os.path.exists(corrected_file):
                logger.error(f"corrected file {corrected_file} was not created. aborting process.")
                return None

            current_file_path = corrected_file
            reference_number += 1

        # apply the cumulative shift to generate the final output.
        final_output_path = os.path.join(FINAL_OUTPUT_DIR, f"corrected_{original_filename}")
        FFmpegUtils.apply_cumulative_shift(input_file, final_output_path, total_shift_ms)

        # run a final verification.
        AnalysisUtils.verify_synchronization(
            final_output_path, f"{reference_number:05d}", fps, DEFAULT_TOLERANCE_MS
        )
        os.remove(corrected_file)
        return final_output_path

    except Exception as e:
        logger.error(f"an error occurred during video processing: {e}")
        return None
