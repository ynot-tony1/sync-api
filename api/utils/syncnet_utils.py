"""
Utility class for handling SyncNet operations.
"""

import os
import subprocess
from typing import Tuple, Union, Optional
from api.config.settings import (
    DEFAULT_MAX_ITERATIONS, TEMP_PROCESSING_DIR, FINAL_LOGS_DIR, FINAL_OUTPUT_DIR,
    DATA_WORK_PYAVI_DIR, DATA_WORK_DIR
)
from api.utils.api_utils import ApiUtils
from api.utils.file_utils import FileUtils
from api.utils.ffmpeg_utils import FFmpegUtils
from api.utils.analysis_utils import AnalysisUtils

import logging

from api.types.props import VideoProps, AudioProps, SyncError

logger: logging.Logger = logging.getLogger('pipeline_logger')


class SyncNetUtils:
    @staticmethod
    def run_syncnet(ref_str: str, log_file: Optional[str] = None) -> str:
        """Executes the SyncNet model.

        This method runs the SyncNet model using a subprocess call. It constructs the command with
        the provided reference string and an optional log file path. If no log file path is provided,
        a default log file path within FINAL_LOGS_DIR is used.

        Args:
            ref_str (str): The reference string used for the SyncNet process.
            log_file (Optional[str]): The path to the log file. If None, a default is generated.

        Returns:
            str: The path to the log file where the SyncNet output is saved.

        Raises:
            RuntimeError: If the subprocess call fails.
        """
        if log_file is None:
            log_file = os.path.join(FINAL_LOGS_DIR, f"run_{ref_str}.log")
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
            error_msg: str = f"SyncNet failed for reference {ref_str}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        return log_file

    @staticmethod
    def run_pipeline(video_file: str, ref: str) -> None:
        """Runs the SyncNet pipeline on a video file.

        This method invokes the SyncNet pipeline as a subprocess. It uses the provided video file and
        reference identifier to run the pipeline, writing output to a pipeline log file.

        Args:
            video_file (str): The path to the video file to process.
            ref (str): The reference identifier for this processing run.

        Raises:
            RuntimeError: If the pipeline subprocess call fails.
        """
        cmd = [
            "python",
            "-m",
            "syncnet_python.run_pipeline",
            "--videofile", video_file,
            "--reference", ref
        ]
        log_file: str = os.path.join(os.path.dirname(FINAL_LOGS_DIR), 'pipeline.log')
        try:
            with open(log_file, 'w') as log:
                subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
            logger.info(f"SyncNet pipeline successfully executed for video: {video_file} with reference: {ref}")
        except subprocess.CalledProcessError as e:
            logger.error(f"SyncNet pipeline failed for video {video_file} (ref={ref}): {e}")
            raise RuntimeError(f"SyncNet pipeline failed for video {video_file} (ref={ref}): {e}") from e

    @staticmethod
    def prepare_video(input_file: str, original_filename: str) -> Tuple[str, VideoProps, AudioProps, Union[int, float], str, int]:
        """Prepares the video for synchronization.

        This method performs the following operations:
          1. Notifies via websocket about the start of the process.
          2. Copies the input file to a temporary location and moves it into the processing directory.
          3. Retrieves video properties (using VideoProps) and audio properties (using AudioProps).
          4. Re-encodes the file to AVI format if it is not already in AVI.

        Args:
            input_file (str): The path to the uploaded video.
            original_filename (str): The original filename of the video.

        Returns:
            Tuple[str, VideoProps, AudioProps, Union[int, float], str, int]:
                - avi_file: Path to the AVI video file ready for synchronization.
                - vid_props: Video properties as a VideoProps model.
                - audio_props: Audio properties as an AudioProps model.
                - fps: Frames per second of the video.
                - destination_path: The final destination path of the video file.
                - reference_number: The reference number assigned for processing.

        Raises:
            RuntimeError: If the destination file does not exist, or if required video/audio streams are missing.
        """
        ApiUtils.send_websocket_message("Here we go...")
        ApiUtils.send_websocket_message("Setting up our filing system...")
        reference_number: int = int(FileUtils.get_next_directory_number(DATA_WORK_PYAVI_DIR))
        ApiUtils.send_websocket_message("Copying your file to work on...")
        temp_copy_path: str = FileUtils.copy_input_to_temp(input_file, original_filename)
        destination_path: str = FileUtils.move_to_data_work(temp_copy_path, reference_number)
        if not os.path.exists(destination_path):
            raise RuntimeError(f"Destination file {destination_path} doesn't exist. Aborting process.")

        # Retrieve video properties as a VideoProps model.
        vid_props: Optional[VideoProps] = FFmpegUtils.get_video_properties(input_file)
        if vid_props is None:
            raise RuntimeError("Couldn't find any video stream")
        fps: Union[int, float] = vid_props.get('fps')
        ApiUtils.send_websocket_message("Finding out about your file...")

        # Retrieve audio properties as an AudioProps model.
        audio_props: Optional[AudioProps] = FFmpegUtils.get_audio_properties(input_file)
        if audio_props is None:
            raise RuntimeError("No audio stream found in the video.")

        ext: str = os.path.splitext(original_filename)[1].lower()
        if ext == ".avi":
            avi_file: str = destination_path
        else:
            logger.info("Converting file to avi for processing")
            avi_file = os.path.splitext(destination_path)[0] + "_reencoded.avi"
            FFmpegUtils.reencode_to_avi(destination_path, avi_file)
        return avi_file, vid_props, audio_props, fps, destination_path, reference_number

    @staticmethod
    def perform_sync_iterations(corrected_file: str, original_filename: str, fps: Union[int, float], reference_number: int) -> Union[SyncError, Tuple[int, str, int]]:
        """Iteratively runs the SyncNet pipeline and applies audio shifts.

        This method runs the SyncNet pipeline repeatedly to determine and apply the required
        audio shift. It accumulates the total shift over iterations. If no shift is needed on the
        first iteration, it returns a SyncError (with error=False) indicating the clip is already in sync.

        Args:
            corrected_file (str): Path to the currently corrected video file.
            original_filename (str): The original filename of the video.
            fps (int | float): The video's frame rate.
            reference_number (int): The current reference number used for logging and file naming.

        Returns:
            Union[SyncError, Tuple[int, str, int]]:
                On success, returns a tuple:
                    - total_shift_ms (int): The cumulative shift applied (in ms).
                    - corrected_file (str): Path to the final corrected video file.
                    - updated_reference_number (int): The updated reference number.
                On failure, returns a SyncError model with keys 'error', 'message', and 'final_offset'.

        Raises:
            RuntimeError: If a new corrected file is not created during processing.
        """
        total_shift_ms: int = 0
        for iteration in range(DEFAULT_MAX_ITERATIONS):
            iteration_msg: str = f"Pass number {iteration + 1} in progress..."
            ApiUtils.send_websocket_message(iteration_msg)
            logger.info(iteration_msg)
            ref_str: str = f"{reference_number:05d}"
            ApiUtils.send_websocket_message("Running the pipeline...")
            SyncNetUtils.run_pipeline(corrected_file, ref_str)
            ApiUtils.send_websocket_message("Running the model...")
            log_file: str = SyncNetUtils.run_syncnet(ref_str)
            ApiUtils.send_websocket_message("Analyzing the results that came back...")
            offset_ms: int = AnalysisUtils.analyze_syncnet_log(log_file, fps)
            if offset_ms == 0:
                if iteration == 0:
                    ApiUtils.send_websocket_message("Your clip is already in sync")
                    return {"error": False, "message": "already in sync", "final_offset": 0}
                else:
                    ApiUtils.send_websocket_message("Clip is now perfectly in sync; finishing...")
                    break
            if offset_ms > 0:
                debug_msg: str = (f"Analysis complete: offset is {offset_ms} ms. "
                                  f"Your clip is currently {offset_ms} ms ahead of the video.")
            else:
                debug_msg = (f"Analysis complete: offset is {offset_ms} ms. "
                             f"Your clip is {abs(offset_ms)} ms behind the video.")
            ApiUtils.send_websocket_message(debug_msg)
            total_shift_ms += offset_ms
            offset_msg: str = f"Total shift after pass {iteration + 1} will be {total_shift_ms} ms."
            logger.info(offset_msg)
            ApiUtils.send_websocket_message(offset_msg)
            base_name: str = os.path.splitext(original_filename)[0]
            new_corrected_file: str = os.path.join(TEMP_PROCESSING_DIR, f"corrected_iter{iteration + 1}_{base_name}.avi")
            ApiUtils.send_websocket_message("Adjusting the streams in your file...")
            FFmpegUtils.shift_audio(corrected_file, new_corrected_file, offset_ms)
            if not os.path.exists(new_corrected_file):
                raise RuntimeError(f"Corrected file {new_corrected_file} was not created. Aborting process.")
            corrected_file = new_corrected_file
            reference_number += 1
        return total_shift_ms, corrected_file, reference_number

    @staticmethod
    def finalize_sync(input_file: str, original_filename: str, total_shift_ms: int, reference_number: int,
                      fps: Union[int, float], destination_path: str, vid_props: VideoProps,
                      audio_props: AudioProps, corrected_file: str) -> Union[str, SyncError]:
        """Finalizes synchronization by applying the cumulative shift and re-encoding if necessary.

        This method applies the final cumulative audio shift to the original video file. It then runs the
        pipeline and model to verify synchronization. If the final offset is not zero, it returns a SyncError.
        If the original file is in AVI format, re-encoding is skipped; otherwise, the file is re-encoded back
        to the original container and codecs.

        Args:
            input_file (str): Path to the original input video.
            original_filename (str): The original filename of the video.
            total_shift_ms (int): The cumulative audio shift applied (in ms).
            reference_number (int): The current reference number.
            fps (int | float): The video's frame rate.
            destination_path (str): The path where the video was moved.
            vid_props (VideoProps): The video properties.
            audio_props (AudioProps): The audio properties.
            corrected_file (str): Path to the corrected video file after iterative adjustments.

        Returns:
            Union[str, SyncError]:
                On success, returns a string containing the final output file path.
                On failure, returns a SyncError model.

        Raises:
            RuntimeError: If the corrected file cannot be processed.
        """
        final_output_path: str = os.path.join(FINAL_OUTPUT_DIR, f"corrected_{original_filename}")
        ApiUtils.send_websocket_message("Making the final shift...")
        FFmpegUtils.apply_cumulative_shift(input_file, final_output_path, total_shift_ms)
        ApiUtils.send_websocket_message("Double checking everything...")
        ref_str: str = f"{reference_number:05d}"
        SyncNetUtils.run_pipeline(final_output_path, ref_str)
        final_log: str = os.path.join(FINAL_LOGS_DIR, f"final_output_{ref_str}.log")
        SyncNetUtils.run_syncnet(ref_str, final_log)
        final_offset: int = AnalysisUtils.analyze_syncnet_log(final_log, fps)
        if final_offset != 0:
            error_msg: str = "final offset incorrect"
            ApiUtils.send_websocket_message("Something went wrong behind the scenes. Please refresh and try again")
            logger.error(error_msg)
            return {
                "error": True,
                "message": "Something went wrong behind the scenes. Please refresh and try again",
                "final_offset": final_offset
            }
        if corrected_file != destination_path and os.path.exists(corrected_file):
            os.remove(corrected_file)
        original_ext: str = os.path.splitext(original_filename)[1].lower()
        if original_ext == ".avi":
            logger.info("Original file was AVI; skipping re-encoding.")
            return final_output_path
        else:
            logger.info("Re-encoding with original container and codec")
            original_video_codec: Optional[str] = vid_props.get('codec_name')
            original_audio_codec: Optional[str] = audio_props.get('codec_name')
            restored_final: str = os.path.splitext(final_output_path)[0] + "_restored" + original_ext
            logger.info("Re-encoding final output back to original container.")
            FFmpegUtils.reencode_to_original_format(final_output_path, restored_final, original_ext,
                                                     original_video_codec, original_audio_codec)
            return restored_final

    @staticmethod
    def synchronize_video(avi_file: str, input_file: str, original_filename: str, vid_props: VideoProps,
                          audio_props: AudioProps, fps: Union[int, float], destination_path: str,
                          reference_number: int) -> Union[str, SyncError]:
        """Orchestrates the synchronization process.

        This method is the main controller that orchestrates video synchronization. It:
          1. Runs iterative synchronization to adjust audio offsets.
          2. Finalizes the synchronization process by applying the cumulative shift and re-encoding if needed.
        If the process is successful, it returns the final output file path; otherwise, it returns a SyncError.

        Args:
            avi_file (str): Path to the initial AVI video file.
            input_file (str): Path to the original input video.
            original_filename (str): The original filename of the video.
            vid_props (VideoProps): The video properties.
            audio_props (AudioProps): The audio properties.
            fps (int | float): The video's frame rate.
            destination_path (str): The destination path for the video file.
            reference_number (int): The initial reference number for processing.

        Returns:
            Union[str, SyncError]:
                A string containing the final output file path if successful,
                or a SyncError model if an error occurred.
        """
        ApiUtils.send_websocket_message("Ok, had a look; let's begin to sync...")
        sync_iterations_result: Union[SyncError, Tuple[int, str, int]] = SyncNetUtils.perform_sync_iterations(
            corrected_file=avi_file,
            original_filename=original_filename,
            fps=fps,
            reference_number=reference_number
        )
        if isinstance(sync_iterations_result, dict):
            return sync_iterations_result
        total_shift_ms, final_corrected_file, updated_reference_number = sync_iterations_result
        final_output_path: Union[str, SyncError] = SyncNetUtils.finalize_sync(
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
    def verify_synchronization(final_path: str, ref_str: str, fps: Union[int, float]) -> None:
        """Verifies that the final synchronized video is in sync.

        This method runs the pipeline and analyzes the final log to ensure that the audio and video streams
        are properly synchronized.

        Args:
            final_path (str): The path to the final output video.
            ref_str (str): The reference string used for this final verification.
            fps (int | float): The video's frame rate.
        """
        logger.info("Starting final synchronization verification...")
        SyncNetUtils.run_pipeline(final_path, ref_str)
        final_log: str = os.path.join(FINAL_LOGS_DIR, f"final_output_{ref_str}.log")
        SyncNetUtils.run_syncnet(ref_str, final_log)
        final_offset: int = AnalysisUtils.analyze_syncnet_log(final_log, fps)
        logger.info(f"Final offset: {final_offset} ms")
