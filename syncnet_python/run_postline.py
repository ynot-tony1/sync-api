import os
import logging
from syncnet_python.utils.file_utils import FileUtils
from syncnet_python.utils.ffmpeg_utils import FFmpegUtils
from syncnet_python.utils.syncnet_utils import SyncNetUtils
from syncnet_python.utils.analysis_utils import AnalysisUtils
from api.config.settings import (
    RUN_LOGS_DIR, LOGS_DIR, FINAL_LOGS_DIR, DEFAULT_MAX_ITERATIONS,
    DEFAULT_TOLERANCE_MS, TEMP_PROCESSING_DIR, DATA_WORK_PYAVI_DIR,
    FINAL_OUTPUT_DIR
)


logger = logging.getLogger('run_postline')

def process_video(input_file, original_filename):
    """
    Synchronizes a video file using ffmpeg and the CNN 'SyncNet'.

    Args:
        input_file (str): The path to the input video file.
        original_filename (str): The original name of the input video file.

    Returns:
        str or None: Path to the synchronized video file if successful; otherwise, None.
    """
    try:
        logger.info("Starting video synchronization process...")

        # making a list of directories for intermediate files and logs
        directories = [
            LOGS_DIR, RUN_LOGS_DIR, FINAL_LOGS_DIR, TEMP_PROCESSING_DIR,
            DATA_WORK_PYAVI_DIR, FINAL_OUTPUT_DIR
        ]

        # making sure all directories exist and creating them if not
        FileUtils.prepare_directories(directories)

        # getting the next directory number from the pipeline's data dir to make sure it all runs in ascending order 
        reference_number = int(FileUtils.get_next_directory_number())

        # copying the input file to the temp directory 
        temp_copy_path = FileUtils.copy_input_to_temp(input_file, original_filename)

        # moving the copied file to the data directory to start off the pipeline processing
        destination_path = FileUtils.move_to_data_work(temp_copy_path, reference_number)

        # making sure the file has been moved to the data directory by checking the existence of its path with os.path
        if not os.path.exists(destination_path):
            logger.error(f"Destination file {destination_path} does not exist. Aborting process.")
            return None

        # get fps (frames per second) of the video
        fps = FFmpegUtils.get_video_fps(input_file)

        # if fps retrieval fails
        if fps is None:
            logger.error("Could not retrieve FPS from the video. Aborting process.")
            return None
        
        # initialize a variable to count the total needed for the final cumulative shift
        total_shift_ms = 0

        # current file path to be processed
        current_file_path = destination_path

        # sync the video and audio streams from input file across multiple iterations using syncnet for analysis and ffmpeg with apad and atrim
        for iteration in range(DEFAULT_MAX_ITERATIONS):
            logger.info(f"--- Synchronization Iteration {iteration + 1} ---")
            ref_str = f"{reference_number:05d}"

            # run the SyncNet pipeline
            SyncNetUtils.run_pipeline(current_file_path, ref_str)

            # run the syncnet model and get the log file path
            log_file = SyncNetUtils.run_syncnet(ref_str)

            # pass the log file path and the fps into the  my analysis function to get the offset in ms
            offset_ms = AnalysisUtils.analyze_syncnet_log(log_file, fps)

            # add the amount to the total_shift variable for the final cumulative shift
            total_shift_ms += offset_ms

            # loggin the amount shifted and the number of the iteration
            logger.info(f"Total shift after iteration {iteration + 1}: {total_shift_ms} ms")

            # checking if the offset is within the acceptable tolerance
            if abs(offset_ms) <= DEFAULT_TOLERANCE_MS:
                logger.info("Synchronization offset is within the acceptable tolerance.")
                break

            # defining the path and file name for the corrected file
            corrected_file = os.path.join(
                TEMP_PROCESSING_DIR,
                f"corrected_iter{iteration + 1}_{original_filename}"
            )

            # applying the calculated shift to the audio with ffmpeg for the next iteration
            FFmpegUtils.shift_audio(current_file_path, corrected_file, offset_ms)

            # checking if the corrected file was successfully created
            if not os.path.exists(corrected_file):
                logger.error(f"Corrected file {corrected_file} was not created. Aborting process.")
                return None

            # updating the current file path for the next iteration
            current_file_path = corrected_file

            # increment the reference number to ensure ascending order in the directorys for the logs and general order
            reference_number += 1

        # defining the path for the final output file
        final_output_path = os.path.join(FINAL_OUTPUT_DIR, f"corrected_{original_filename}")

        # finalizing the synchronization by applying the total shift
        FFmpegUtils.apply_cumulative_shift(input_file, final_output_path, total_shift_ms)

        # running the final file through the pipeline and SyncNet once more to ensure 0 offset
        AnalysisUtils.verify_synchronization(
            final_output_path,                 # path of the final synchronized video
            f"{reference_number:05d}",         # formatted reference string
            fps,                               # frames per second
            DEFAULT_TOLERANCE_MS               # tolerance in ms
        )

        # returning the path of the final synchronized video file
        return final_output_path, abs(total_shift_ms)

    except Exception as e:
        logger.error(f"An error occurred during video processing: {e}")
        return None
