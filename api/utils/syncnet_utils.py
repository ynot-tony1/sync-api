"""
Utility class for handling SyncNet operations.
"""

import os
import subprocess
from typing import Any, Dict, Tuple, Union, Optional
from api.config.type_settings import (
    DEFAULT_MAX_ITERATIONS, TEMP_PROCESSING_DIR, FINAL_LOGS_DIR, FINAL_OUTPUT_DIR, DATA_WORK_PYAVI_DIR, DATA_WORK_DIR
)
from api.utils.api_utils import ApiUtils
from api.utils.file_utils import FileUtils
from api.utils.ffmpeg_utils import FFmpegUtils
from api.utils.analysis_utils import AnalysisUtils

import logging

logger: logging.Logger = logging.getLogger('pipeline_logger')


class SyncNetUtils:
    @staticmethod
    def run_syncnet(ref_str: str, log_file: Optional[str] = None) -> str:
        """
        Executes the SyncNet model.
        
        Args:
            ref_str (str): The reference string.
            log_file (Optional[str]): Path to the log file.
        
        Returns:
            str: Path to the log file.
        
        Raises:
            RuntimeError: If SyncNet subprocess fails.
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
        """
        Runs the SyncNet pipeline on a video file.
        
        Args:
            video_file (str): Path to the video file.
            ref (str): Reference identifier.
        
        Raises:
            RuntimeError: If the pipeline subprocess fails.
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
    def prepare_video(input_file: str, original_filename: str) -> Tuple[str, Dict[str, Any], Dict[str, Any], Union[int, float], str, int]:
        """
        Prepares the video for synchronization.
        
        Returns a tuple containing:
            - avi_file (str)
            - vid_props (dict)
            - audio_props (dict)
            - fps (int | float)
            - destination_path (str)
            - reference_number (int)
        """
        ApiUtils.send_websocket_message("Here we go...")
        ApiUtils.send_websocket_message("Setting up our filing system...")
        reference_number: int = int(FileUtils.get_next_directory_number(DATA_WORK_PYAVI_DIR))
        ApiUtils.send_websocket_message("Copying your file to work on...")
        temp_copy_path: str = FileUtils.copy_input_to_temp(input_file, original_filename)
        destination_path: str = FileUtils.move_to_data_work(temp_copy_path, reference_number)
        if not os.path.exists(destination_path):
            raise RuntimeError(f"Destination file {destination_path} doesn't exist. Aborting process.")
        vid_props: Dict[str, Any] = FFmpegUtils.get_video_properties(input_file)  # Using original file for properties
        if vid_props is None:
            raise RuntimeError("Couldn't find any video stream")
        fps: Union[int, float] = vid_props.get('fps')
        ApiUtils.send_websocket_message("Finding out about your file...")
        audio_props: Dict[str, Any] = FFmpegUtils.get_audio_properties(input_file)
        if audio_props is None:
            raise RuntimeError("No audio stream found in the video.")
        ext: str = os.path.splitext(original_filename)[1].lower()
        if ext == ".avi":
            avi_file: str = destination_path
        else:
            avi_file = os.path.splitext(destination_path)[0] + "_reencoded.avi"
            FFmpegUtils.reencode_to_avi(destination_path, avi_file)
        return avi_file, vid_props, audio_props, fps, destination_path, reference_number

    @staticmethod
    def perform_sync_iterations(corrected_file: str, original_filename: str, fps: Union[int, float], reference_number: int) -> Union[Dict[str, Any], Tuple[int, str, int]]:
        """
        Iteratively runs the SyncNet pipeline and applies audio shifts.
        
        Returns a tuple:
            (total_shift_ms, corrected_file, updated_reference_number)
        
        Or an error dict.
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
                    return {"already_in_sync": True, "message": "already in sync"}
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
                      fps: Union[int, float], destination_path: str, vid_props: Dict[str, Any],
                      audio_props: Dict[str, Any], corrected_file: str) -> Union[str, Dict[str, Any]]:
        """
        Finalizes synchronization by applying the cumulative shift and re-encoding if necessary.
        
        Returns the final output file path or an error dict.
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
            original_video_codec: Optional[str] = vid_props.get('codec_name')
            original_audio_codec: Optional[str] = audio_props.get('codec_name')
            restored_final: str = os.path.splitext(final_output_path)[0] + "_restored" + original_ext
            logger.info("Re-encoding final output back to original container.")
            FFmpegUtils.reencode_to_original_format(final_output_path, restored_final, original_ext,
                                                     original_video_codec, original_audio_codec)
            return restored_final

    @staticmethod
    def synchronize_video(avi_file: str, input_file: str, original_filename: str, vid_props: Dict[str, Any],
                          audio_props: Dict[str, Any], fps: Union[int, float], destination_path: str,
                          reference_number: int) -> Union[str, Dict[str, Any]]:
        """
        Orchestrates the synchronization process.
        
        Returns the final output file path on success or an error dict.
        """
        ApiUtils.send_websocket_message("Ok, had a look; let's begin to sync...")
        sync_iterations_result: Union[Dict[str, Any], Tuple[int, str, int]] = SyncNetUtils.perform_sync_iterations(
            corrected_file=avi_file,
            original_filename=original_filename,
            fps=fps,
            reference_number=reference_number
        )
        if isinstance(sync_iterations_result, dict):
            return sync_iterations_result
        total_shift_ms, final_corrected_file, updated_reference_number = sync_iterations_result
        final_output_path: Union[str, Dict[str, Any]] = SyncNetUtils.finalize_sync(
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
        """
        Verifies that the final synchronized video is in sync.
        
        Args:
            final_path (str): Path to the final output.
            ref_str (str): Reference string.
            fps (int | float): Frames per second.
        """
        logger.info("Starting final synchronization verification...")
        SyncNetUtils.run_pipeline(final_path, ref_str)
        final_log: str = os.path.join(FINAL_LOGS_DIR, f"final_output_{ref_str}.log")
        SyncNetUtils.run_syncnet(ref_str, final_log)
        final_offset: int = AnalysisUtils.analyze_syncnet_log(final_log, fps)
        logger.info(f"Final offset: {final_offset} ms")
