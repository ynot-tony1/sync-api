import os
import subprocess
import logging
from .log_utils import LogUtils
from api.config.settings import LOGS_DIR, RUN_LOGS_DIR, DATA_WORK_DIR
from api.utils.api_utils import ApiUtils
from api.utils.file_utils import FileUtils
from api.utils.ffmpeg_utils import FFmpegUtils
from api.utils.analysis_utils import AnalysisUtils
from api.config.settings import (
    DEFAULT_MAX_ITERATIONS, TEMP_PROCESSING_DIR, FINAL_LOGS_DIR, 
    FINAL_OUTPUT_DIR, DATA_WORK_PYAVI_DIR
)

LogUtils.configure_logging()
logger = logging.getLogger('pipeline_logger')


class SyncNetUtils:
    """Utility class for handling SyncNet operations."""

    @staticmethod
    def run_syncnet(ref_str, log_file=None):
        """
        Executes the SyncNet model and logs the output.

        This function runs the SyncNet module as a subprocess using the provided 
        reference string and directs its stdout/stderr output into a log file.
        
        Args:
            ref_str (str): The reference identifier used for processing.
            log_file (str, optional): The path to the log file. If not provided, a default 
                log file in RUN_LOGS_DIR is used.
        
        Returns:
            str: The path to the log file where SyncNet output is stored.
        
        Raises:
            RuntimeError: If the subprocess call to run SyncNet fails.
        """
        if log_file is None:
            log_file = os.path.join(RUN_LOGS_DIR, f"run_{ref_str}.log")
        cmd = [
            "python",
            "-m",
            "syncnet_python.run_syncnet",
            "--data_dir", DATA_WORK_DIR,
            "--reference", ref_str
        ]
        try:
            with open(log_file, 'w') as log:
                subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
            logger.info(f"SyncNet model completed successfully. Log saved to: {log_file}")
        except subprocess.CalledProcessError as e:
            error_msg = f"SyncNet failed while processing reference {ref_str}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        return log_file

    @staticmethod
    def run_pipeline(video_file, ref):
        """
        Runs the SyncNet pipeline on a given video file.

        This function calls the SyncNet pipeline module as a subprocess, which performs 
        the preliminary synchronization steps on the provided video file.
        
        Args:
            video_file (str): The path to the video file to be processed.
            ref (str): The reference identifier used during processing.
        
        Returns:
            None
        
        Raises:
            RuntimeError: If the subprocess call to run the pipeline fails.
        """
        cmd = [
            "python",
            "-m",
            "syncnet_python.run_pipeline",
            "--videofile", video_file,
            "--reference", ref
        ]
        log_file = os.path.join(LOGS_DIR, 'pipeline.log')
        try:
            with open(log_file, 'w') as log:
                subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
            logger.info(f"SyncNet pipeline successfully executed for video: {video_file} with reference: {ref}")
        except subprocess.CalledProcessError as e:
            logger.error(f"SyncNet pipeline failed for video {video_file} (ref={ref}): {e}")
            raise RuntimeError(f"SyncNet pipeline failed for video {video_file} (ref={ref}): {e}") from e

    @staticmethod
    def prepare_video(input_file, original_filename):
        """
        Prepares the video for synchronization by performing file operations and re-encoding if necessary.

        The function performs the following steps:
          1. Sends websocket messages to indicate progress.
          2. Copies the input file to a temporary location.
          3. Moves the file to the working directory and retrieves a reference number.
          4. Extracts video and audio properties.
          5. Checks if the file is already an AVI; if not, it re-encodes the file to AVI.
        
        Args:
            input_file (str): The path to the input video file.
            original_filename (str): The original filename of the uploaded video.
        
        Returns:
            tuple: A tuple containing:
                - avi_file (str): The path to the AVI file (either original or re-encoded).
                - vid_props (dict): The video properties.
                - audio_props (dict): The audio properties.
                - fps (float): Frames per second of the video.
                - destination_path (str): The path where the file was moved.
                - reference_number (int): A unique reference number for processing.
        
        Raises:
            RuntimeError: If the destination file does not exist or required video/audio properties are missing.
        """
        ApiUtils.send_websocket_message("Here we go...")
        ApiUtils.send_websocket_message("Setting up our filing system...")
        reference_number = int(FileUtils.get_next_directory_number(DATA_WORK_PYAVI_DIR))
        ApiUtils.send_websocket_message("Copying your file to work on...")
        temp_copy_path = FileUtils.copy_input_to_temp(input_file, original_filename)
        destination_path = FileUtils.move_to_data_work(temp_copy_path, reference_number)
        if not os.path.exists(destination_path):
            raise RuntimeError(f"Destination file {destination_path} doesn't exist. Aborting process.")
        
        vid_props = FFmpegUtils.get_video_properties(input_file)
        if vid_props is None:
            raise RuntimeError("Couldn't find any video stream")
        fps = vid_props.get('fps')
        ApiUtils.send_websocket_message("Finding out about your file...")
        audio_props = FFmpegUtils.get_audio_properties(input_file)
        if audio_props is None:
            raise RuntimeError("No audio stream found in the video.")
        
        ext = os.path.splitext(original_filename)[1].lower()
        if ext == ".avi":
            avi_file = destination_path
        else:
            avi_file = os.path.splitext(destination_path)[0] + "_reencoded.avi"
            FFmpegUtils.reencode_to_avi(destination_path, avi_file)
        
        return avi_file, vid_props, audio_props, fps, destination_path, reference_number

    @staticmethod
    def perform_sync_iterations(corrected_file, original_filename, fps, reference_number):
        """
        Iteratively runs the SyncNet pipeline and applies incremental audio shifts.

        For a maximum number of iterations, this function:
          1. Runs the SyncNet pipeline and model.
          2. Analyzes the log file to determine the required audio offset.
          3. If the offset is zero (and it's the first iteration), returns an "already in sync" dict.
          4. Otherwise, adjusts the audio stream by shifting it and accumulates the total shift.
        
        Args:
            corrected_file (str): The path to the current corrected video file.
            original_filename (str): The original filename of the video.
            fps (float): Frames per second of the video.
            reference_number (int): The current reference number.
        
        Returns:
            tuple: A tuple containing:
                - total_shift_ms (int): The total cumulative audio shift in milliseconds.
                - corrected_file (str): The path to the final corrected video file after iterations.
                - reference_number (int): The updated reference number after iterations.
        
        Raises:
            RuntimeError: If a corrected file is not created during an iteration.
        """
        total_shift_ms = 0
        for iteration in range(DEFAULT_MAX_ITERATIONS):
            iteration_msg = f"Pass number {iteration + 1} in progress..."
            ApiUtils.send_websocket_message(iteration_msg)
            logger.info(iteration_msg)

            ref_str = f"{reference_number:05d}"
            ApiUtils.send_websocket_message("Running the pipeline...")
            SyncNetUtils.run_pipeline(corrected_file, ref_str)

            ApiUtils.send_websocket_message("Running the model...")
            log_file = SyncNetUtils.run_syncnet(ref_str)

            ApiUtils.send_websocket_message("Analyzing the results that came back...")
            offset_ms = AnalysisUtils.analyze_syncnet_log(log_file, fps)
            
            if offset_ms == 0:
                if iteration == 0:
                    ApiUtils.send_websocket_message("Your clip is already in sync")
                    return {"already_in_sync": True, "message": "already in sync"}
                else:
                    ApiUtils.send_websocket_message("Clip is now perfectly in sync; finishing...")
                    break

            if offset_ms > 0:
                debug_msg = (f"Analysis complete: offset is {offset_ms} ms. "
                             f"Your clip is currently exactly {offset_ms} ms ahead of the video.")
            elif offset_ms < 0:
                debug_msg = (f"Analysis complete: offset is {offset_ms} ms. "
                             f"Your clip is sitting at {abs(offset_ms)} ms behind the video.")

            ApiUtils.send_websocket_message(debug_msg)
            total_shift_ms += offset_ms

            offset_msg = f"Total shift after pass {iteration + 1} will be {total_shift_ms} ms."
            logger.info(offset_msg)
            ApiUtils.send_websocket_message(offset_msg)

            base_name = os.path.splitext(original_filename)[0]
            new_corrected_file = os.path.join(
                TEMP_PROCESSING_DIR,
                f"corrected_iter{iteration + 1}_{base_name}.avi"
            )
            ApiUtils.send_websocket_message("Adjusting the streams in your file...")
            FFmpegUtils.shift_audio(corrected_file, new_corrected_file, offset_ms)
            if not os.path.exists(new_corrected_file):
                raise RuntimeError(f"Corrected file {new_corrected_file} was not created. Aborting process.")

            corrected_file = new_corrected_file
            reference_number += 1

        return total_shift_ms, corrected_file, reference_number

    @staticmethod
    def finalize_sync(input_file, original_filename, total_shift_ms, reference_number,
                      fps, destination_path, vid_props, audio_props, corrected_file):
        """
        Finalizes the synchronization process by applying the cumulative shift, generating the final log file, 
        and performing any final corrections before re-encoding to the original container.

        This function applies the cumulative audio shift to produce a preliminary final output, then runs
        the SyncNet pipeline and model to generate a final log file. The log is analyzed for any remaining 
        offset. If the offset is non-zero, an error dict is returned. Otherwise, the function re-encodes the
        output back to the original container unless the original file is AVI (in which case re-encoding is skipped).

        Args:
            input_file (str): Path to the user's original video.
            original_filename (str): Original filename of the video.
            total_shift_ms (int): Cumulative audio shift from iterations.
            reference_number (int): The reference number used in processing.
            fps (float): Frames per second.
            destination_path (str): Path where the file was originally moved.
            vid_props (dict): Video properties.
            audio_props (dict): Audio properties.
            corrected_file (str): Path to the corrected file from the iterative process.
        
        Returns:
            str or dict: On success, returns the final output file path (re-encoded if necessary).
                         On error, returns a dictionary containing error information.
        """
        final_output_path = os.path.join(FINAL_OUTPUT_DIR, f"corrected_{original_filename}")
        ApiUtils.send_websocket_message("Making the final shift...")
        FFmpegUtils.apply_cumulative_shift(input_file, final_output_path, total_shift_ms)
        ApiUtils.send_websocket_message("Double checking everything...")
        ref_str = f"{reference_number:05d}"
        SyncNetUtils.run_pipeline(final_output_path, ref_str)
        final_log = os.path.join(FINAL_LOGS_DIR, f"final_output_{ref_str}.log")
        SyncNetUtils.run_syncnet(ref_str, final_log)
        final_offset = AnalysisUtils.analyze_syncnet_log(final_log, fps)
        
        if final_offset != 0:
            error_msg = "final offset incorrect"
            ApiUtils.send_websocket_message(
                "Something has gone wrong behind the scenes, apologies. Please refresh the page and try again"
            )
            logger.error(error_msg)
            return {
                "error": True,
                "message": "Something has gone wrong behind the scenes, apologies. Please refresh the page and try again",
                "final_offset": final_offset
            }
        
        if corrected_file != destination_path and os.path.exists(corrected_file):
            os.remove(corrected_file)
        original_ext = os.path.splitext(original_filename)[1].lower()

        if original_ext == ".avi":
            logger.info("Original file was AVI; skipping re-encoding to preserve AVI format.")
            return final_output_path
        else:
            original_video_codec = vid_props.get('codec_name')
            original_audio_codec = audio_props.get('codec_name')
            restored_final = os.path.splitext(final_output_path)[0] + "_restored" + original_ext
            logger.info("Re-encoding the final output back to the original container.")
            FFmpegUtils.reencode_to_original_format(
                final_output_path,
                restored_final,
                original_ext,
                original_video_codec,
                original_audio_codec
            )
            return restored_final

    @staticmethod
    def synchronize_video(avi_file, input_file, original_filename, vid_props, audio_props,
                          fps, destination_path, reference_number):
        """
        Performs synchronization by iteratively applying audio shifts and finalizing the output.

        This function serves as the main orchestration method. It calls the functions to perform iterative
        synchronization and then finalizes the video output. The final output file path is returned if 
        processing is successful, otherwise an error dict is returned.
        
        Args:
            avi_file (str): Path to the AVI version of the input video.
            input_file (str): Path to the original input video.
            original_filename (str): Original filename of the video.
            vid_props (dict): Video properties.
            audio_props (dict): Audio properties.
            fps (float): Frames per second.
            destination_path (str): Path where the file was moved.
            reference_number (int): The initial reference number.
        
        Returns:
            str or dict: On success, the final output file path (string). If an error occurs, returns a dict with error details.
        """
        ApiUtils.send_websocket_message("Ok, had a look; let's begin to sync...")
        sync_iterations_result = SyncNetUtils.perform_sync_iterations(
            corrected_file=avi_file,
            original_filename=original_filename,
            fps=fps,
            reference_number=reference_number
        )
        if isinstance(sync_iterations_result, dict):
            return sync_iterations_result

        total_shift_ms, final_corrected_file, updated_reference_number = sync_iterations_result
        final_output_path = SyncNetUtils.finalize_sync(
            input_file=input_file,
            original_filename=original_filename,
            total_shift_ms=total_shift_ms,
            reference_number=updated_reference_number,
            fps=fps,
            destination_path=destination_path,
            vid_props=vid_props,
            audio_props=audio_props,
            corrected_file=final_corrected_file
        )
        return final_output_path

    @staticmethod
    def verify_synchronization(final_path, ref_str, fps):
        """
        Double-checks that the final synchronized video is within the correct offset.

        This function re-runs the SyncNet pipeline and model on the final output file to generate a log.
        It then analyzes the log to determine if the audio and video streams are synchronized properly.
        
        Args:
            final_path (str): The path to the final output video file.
            ref_str (str): The reference identifier as a string.
            fps (float): Frames per second of the video.
        
        Returns:
            None
        
        Side Effects:
            Logs the final offset in milliseconds.
        """
        logger.info("Starting final synchronization verification...")
        SyncNetUtils.run_pipeline(final_path, ref_str)
        final_log = os.path.join(FINAL_LOGS_DIR, f"final_output_{ref_str}.log")
        SyncNetUtils.run_syncnet(ref_str, final_log)
        final_offset = AnalysisUtils.analyze_syncnet_log(final_log, fps)
        logger.info(f"Final offset: {final_offset} ms")
