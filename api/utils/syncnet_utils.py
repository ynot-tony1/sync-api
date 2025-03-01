"""
Module for asynchronous operations related to SyncNet.

This module contains the SyncNetUtils class, which provides asynchronous wrappers
for running the SyncNet pipeline and related FFmpeg operations. It uses asyncio’s
subprocess API to run external commands without blocking the event loop.

Attributes:
    logger (logging.Logger): Logger for the module.
"""
import os, shutil, asyncio
from typing import Tuple, Union, Optional, Dict
import logging

from api.config.settings import (
    DEFAULT_MAX_ITERATIONS,
    TEMP_PROCESSING_DIR,
    FINAL_LOGS_DIR,
    FINAL_OUTPUT_DIR,
    DATA_WORK_PYAVI_DIR,
    DATA_WORK_DIR,
    DATA_DIR
)
from api.utils.api_utils import ApiUtils
from api.utils.file_utils import FileUtils
from api.utils.ffmpeg_utils import FFmpegUtils
from api.utils.analysis_utils import AnalysisUtils
from api.types.props import VideoProps, AudioProps, SyncError

logger: logging.Logger = logging.getLogger('process_video')


class SyncNetUtils:
    """A collection of asynchronous utility methods for running SyncNet and FFmpeg tasks.

    This class encapsulates methods to run the SyncNet model, SyncNet pipeline, and
    associated video/audio processing. All blocking operations are executed using
    asyncio's subprocess API.
    """

    @staticmethod
    async def run_syncnet(ref_str: str, log_file: Optional[str] = None) -> str:
        """Runs the SyncNet model asynchronously using a subprocess.
        
        Debug statements have been added to log input parameters, intermediate variables,
        and the output log file path.
        """
        logger.debug(f"[run_syncnet][ENTER] ref_str='{ref_str}', log_file='{ref_str}'")
        if log_file is None:
            log_file = os.path.join(FINAL_LOGS_DIR, f"run_{ref_str}.log")
        command_str = (
            "python -m syncnet_python.run_syncnet "
            f"--data_dir {DATA_WORK_DIR} --reference {ref_str}"
        )
        logger.debug(f"[run_syncnet] Constructed command: {command_str}")

        process = await asyncio.create_subprocess_shell(
            command_str,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        stdout_bytes, _ = await process.communicate()
        stdout_decoded = stdout_bytes.decode()
        with open(log_file, 'w') as f:
            f.write(stdout_decoded)
        logger.debug(f"[run_syncnet] Written output to log file: {ref_str}")

        if process.returncode != 0:
            error_msg = f"SyncNet failed for reference {ref_str} with return code {process.returncode}"
            logger.error(f"[run_syncnet] {error_msg}")
            raise RuntimeError(error_msg)
        logger.info(f"SyncNet model completed successfully. Log saved to: {ref_str}")
        logger.debug(f"[run_syncnet][EXIT] Returning log_file: {ref_str}")
        return log_file

    @staticmethod
    async def run_pipeline(video_file: str, ref: str) -> None:
        """Runs the SyncNet pipeline asynchronously using a subprocess.

        Debug statements have been added to log input parameters, the command string,
        process outputs, and the final status.
        """
        logger.debug(f"[run_pipeline][ENTER] video_file='{video_file}', ref='{ref}'")
        command_str = (
            "python -m syncnet_python.run_pipeline "
            f"--videofile {video_file} --reference {ref}"
        )
        logger.debug(f"[run_pipeline] Constructed command: {command_str}")

        log_file: str = os.path.join(os.path.dirname(FINAL_LOGS_DIR), 'pipeline.log')
        process = await asyncio.create_subprocess_shell(
            command_str,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        stdout_bytes, _ = await process.communicate()
        stdout_decoded = stdout_bytes.decode()

        with open(log_file, 'w') as f:
            f.write(stdout_decoded)
        logger.debug(f"[run_pipeline] Written output to log file: {ref}")

        if process.returncode != 0:
            error_msg = f"SyncNet pipeline failed for video {video_file} (ref={ref}) with return code {process.returncode}"
            logger.error(f"[run_pipeline] {error_msg}")
            raise RuntimeError(error_msg)
        logger.info(f"SyncNet pipeline successfully executed for video: {video_file} with reference: {ref}")
        logger.debug(f"[run_pipeline][EXIT] Completed pipeline run for video_file='{video_file}'")

    @staticmethod
    async def prepare_video(input_file: str, original_filename: str) -> Tuple[str, VideoProps, AudioProps, Union[int, float], str, int]:
        """Prepares a video file for synchronization asynchronously.

        Debug statements have been added to log input parameters, intermediate file paths,
        properties extracted, and the values returned.
        """
        logger.debug(f"[prepare_video][ENTER] input_file='{input_file}', original_filename='{original_filename}'")
        ApiUtils.send_websocket_message("Here we go...")
        ApiUtils.send_websocket_message("Setting up our filing system...")

        reference_number: int = int(FileUtils.get_next_directory_number(DATA_WORK_PYAVI_DIR))
        logger.debug(f"[prepare_video] Obtained reference_number: {reference_number}")

        ApiUtils.send_websocket_message("Copying your file to work on...")
        temp_copy_path: str = FileUtils.copy_file(input_file, original_filename)
        logger.debug(f"[prepare_video] Copied file to temp_copy_path: {temp_copy_path}")

        destination_path: str = os.path.join(DATA_DIR, f"{reference_number}_{original_filename}")
        FileUtils.move_file(temp_copy_path, destination_path)
        logger.debug(f"[prepare_video] Moved file to destination_path: {destination_path}")

        if not os.path.exists(destination_path):
            error_msg = f"Destination file {destination_path} doesn't exist. Aborting process."
            logger.error(f"[prepare_video] {error_msg}")
            raise RuntimeError(error_msg)
        else:
            logger.debug(f"[prepare_video] Verified destination file exists.")

        vid_props: Optional[VideoProps] = await FFmpegUtils.get_video_properties(input_file)

        logger.debug(f"[prepare_video] Video properties: {vid_props}")
        if vid_props is None:
            error_msg = "Couldn't find any video stream"
            logger.error(f"[prepare_video] {error_msg}")
            raise RuntimeError(error_msg)

        fps: Union[int, float] = vid_props.get('fps')
        ApiUtils.send_websocket_message("Finding out about your file...")

        audio_props: Optional[AudioProps] = await FFmpegUtils.get_audio_properties(input_file)

        logger.debug(f"[prepare_video] Audio properties: {audio_props}")
        if audio_props is None:
            error_msg = "No audio stream found in the video."
            logger.error(f"[prepare_video] {error_msg}")
            raise RuntimeError(error_msg)

        ext: str = os.path.splitext(original_filename)[1].lower()
        if ext == ".avi":
            avi_file: str = destination_path
            logger.debug(f"[prepare_video] File already in AVI format. avi_file set to destination_path: {avi_file}")
        else:
            logger.info("Converting file to avi for processing")
            avi_file = os.path.splitext(destination_path)[0] + "_reencoded.avi"
            logger.debug(f"[prepare_video] Re-encoding to avi. New avi_file: {avi_file}")
            await FFmpegUtils.reencode_to_avi(destination_path, avi_file)

        logger.debug(
            f"[prepare_video][EXIT] Returning avi_file='{avi_file}', vid_props={vid_props}, "
            f"audio_props={audio_props}, fps={fps}, destination_path='{destination_path}', reference_number={reference_number}"
        )
        return avi_file, vid_props, audio_props, fps, destination_path, reference_number

    @staticmethod
    async def perform_sync_iterations(
        corrected_file: str,
        original_filename: str,
        fps: Union[int, float],
        reference_number: int
    ) -> Union[SyncError, Tuple[int, str, int, int]]:
        """Performs iterative synchronization using SyncNet.

        Debug statements have been added to log input parameters, each iteration's progress,
        computed offsets, cumulative shifts, and the final values being returned.
        """
        logger.debug(
            "[DATA][ENTER] perform_sync_iterations -> "
            f"corrected_file='{corrected_file}', original_filename='{original_filename}', "
            f"fps={fps}, reference_number={reference_number}"
        )
        total_shift_ms: int = 0
        iteration_count: int = 0

        for iteration in range(DEFAULT_MAX_ITERATIONS):
            iteration_count = iteration + 1
            iteration_msg: str = f"Pass number {iteration_count} in progress..."
            ApiUtils.send_websocket_message(iteration_msg)
            logger.info(f"[perform_sync_iterations] {iteration_msg}")

            ref_str: str = f"{reference_number:05d}"
            logger.debug(f"[perform_sync_iterations] Using ref_str: {ref_str}")

            ApiUtils.send_websocket_message("Running the pipeline...")
            await SyncNetUtils.run_pipeline(corrected_file, ref_str)

            ApiUtils.send_websocket_message("Running the model...")

            log_file: str = await SyncNetUtils.run_syncnet(ref_str)

            logger.debug(f"[perform_sync_iterations] Obtained log_file: {log_file}")

            ApiUtils.send_websocket_message("Analyzing the results that came back...")
            offset_ms: int = AnalysisUtils.analyze_syncnet_log(log_file, fps)
            logger.debug(f"[perform_sync_iterations] Computed offset_ms: {offset_ms}")

            if offset_ms == 0:
                if iteration == 0:
                    logger.debug("[perform_sync_iterations] Zero offset on first iteration -> already in sync.")
                    logger.debug(f"[perform_sync_iterations][EXIT] Returning (0, {corrected_file}, {reference_number}, {iteration_count})")
                    return (0, corrected_file, reference_number, iteration_count)
                else:
                    ApiUtils.send_websocket_message("Clip is now perfectly in sync; finishing...")
                    logger.debug(f"[perform_sync_iterations] Ending iterations at iteration_count: {iteration_count}")
                    break

            total_shift_ms += offset_ms
            logger.debug(f"[perform_sync_iterations] Total shift after pass {iteration_count}: {total_shift_ms}")

            offset_msg: str = f"Total shift after pass {iteration_count} will be {total_shift_ms} ms."
            ApiUtils.send_websocket_message(offset_msg)
            logger.info(f"[perform_sync_iterations] {offset_msg}")

            base_name: str = os.path.splitext(original_filename)[0]
            new_corrected_file: str = os.path.join(
                TEMP_PROCESSING_DIR,
                f"corrected_iter{iteration_count}_{base_name}.avi"
            )
            logger.debug(f"[perform_sync_iterations] New corrected file will be: {new_corrected_file}")

            ApiUtils.send_websocket_message("Adjusting the streams in your file...")
            await FFmpegUtils.shift_audio(corrected_file, new_corrected_file, offset_ms)

            if not os.path.exists(new_corrected_file):
                error_msg = f"Corrected file {new_corrected_file} was not created. Aborting process."
                logger.error(f"[perform_sync_iterations] {error_msg}")
                raise RuntimeError(error_msg)
            corrected_file = new_corrected_file
            reference_number += 1
            logger.debug(f"[perform_sync_iterations] Updated corrected_file: {corrected_file}, updated reference_number: {reference_number}")

        logger.debug(
            f"[DATA][EXIT] perform_sync_iterations -> total_shift_ms={total_shift_ms}, "
            f"corrected_file='{corrected_file}', updated_reference_number={reference_number}, iteration_count={iteration_count}"
        )
        return (total_shift_ms, corrected_file, reference_number, iteration_count)

    @staticmethod
    async def finalize_sync(
        input_file: str,
        original_filename: str,
        total_shift_ms: int,
        reference_number: int,
        fps: Union[int, float],
        destination_path: str,
        vid_props: VideoProps,
        audio_props: AudioProps,
        corrected_file: str
    ) -> Union[str, SyncError]:
        """Finalizes the synchronization process.

        Debug statements have been added to log input parameters, intermediate file paths,
        computed offsets, and final return values or errors.
        """
        logger.debug(
            "[DATA][ENTER] finalize_sync -> "
            f"input_file='{input_file}', original_filename='{original_filename}', total_shift_ms={total_shift_ms}, "
            f"reference_number={reference_number}, fps={fps}, destination_path='{destination_path}', "
            f"corrected_file='{corrected_file}'"
        )
        final_output_path: str = os.path.join(FINAL_OUTPUT_DIR, f"corrected_{original_filename}")
        logger.debug(f"[finalize_sync] Final output path set to: {final_output_path}")

        ApiUtils.send_websocket_message("Making the final shift...")

        await FFmpegUtils.apply_cumulative_shift(input_file, final_output_path, total_shift_ms)

        logger.debug("[finalize_sync] Applied cumulative shift.")

        ApiUtils.send_websocket_message("Double checking everything...")
        ref_str: str = f"{reference_number:05d}"
        logger.debug(f"[finalize_sync] Using ref_str for final check: {ref_str}")
        await SyncNetUtils.run_pipeline(final_output_path, ref_str)

        final_log: str = os.path.join(FINAL_LOGS_DIR, f"final_output_{ref_str}.log")
        await SyncNetUtils.run_syncnet(ref_str, final_log)

        final_offset: int = AnalysisUtils.analyze_syncnet_log(final_log, fps)
        logger.debug(f"[finalize_sync] Analyzed final_offset: {final_offset}")

        if final_offset != 0:
            error_msg: str = "final offset incorrect"
            ApiUtils.send_websocket_message("Something went wrong behind the scenes and your clip wasnt synced properly! Please refresh the page and give it another go there")
            logger.error(f"[finalize_sync] {error_msg} -> final_offset={final_offset}")
            return {
                "error": True,
                "message": "Something went wrong behind the scenes. Your clip wasnt synced properly",
                "final_offset": final_offset
            }

        if corrected_file != destination_path and os.path.exists(corrected_file):
            os.remove(corrected_file)
            logger.debug(f"[finalize_sync] Removed old corrected_file: '{corrected_file}'")

        original_ext: str = os.path.splitext(original_filename)[1].lower()
        if original_ext == ".avi":
            logger.info("[finalize_sync] Original file was AVI -> skipping re-encode.")
            logger.debug(f"[finalize_sync][EXIT] Returning final_output_path: '{final_output_path}'")
            return final_output_path
        else:
            logger.info("[finalize_sync] Re-encoding final output back to original container/codec.")
            original_video_codec: Optional[str] = vid_props.get('codec_name')
            original_audio_codec: Optional[str] = audio_props.get('codec_name')
            restored_final: str = os.path.splitext(final_output_path)[0] + "_restored" + original_ext
            logger.debug(f"[finalize_sync] Restored final path: {restored_final}")
            await FFmpegUtils.reencode_to_original_format(final_output_path, restored_final, original_ext,
                                                     original_video_codec, original_audio_codec)
            logger.debug(f"[finalize_sync][EXIT] Returning restored_final: '{restored_final}'")
            return restored_final

    @staticmethod
    async def synchronize_video(
        avi_file: str,
        input_file: str,
        original_filename: str,
        vid_props: VideoProps,
        audio_props: AudioProps,
        fps: Union[int, float],
        destination_path: str,
        reference_number: int
    ) -> Union[Tuple[str, bool], SyncError]:
        """Orchestrates the entire synchronization process.

        Debug statements have been added to log input parameters, intermediate results from the
        iterative synchronization, and the final output values.
        """
        logger.debug(
            "[DATA][ENTER] synchronize_video -> "
            f"avi_file='{avi_file}', input_file='{input_file}', original_filename='{original_filename}', "
            f"vid_props={vid_props}, audio_props={audio_props}, fps={fps}, "
            f"destination_path='{destination_path}', reference_number={reference_number}"
        )
        ApiUtils.send_websocket_message("Ok, had a look; let's begin to sync...")

        sync_iterations_result = await SyncNetUtils.perform_sync_iterations(
            corrected_file=avi_file,
            original_filename=original_filename,
            fps=fps,
            reference_number=reference_number
        )
        logger.debug(f"[synchronize_video] perform_sync_iterations returned: {sync_iterations_result}")

        if isinstance(sync_iterations_result, dict):
            logger.debug(f"[synchronize_video][EXIT] Returning error dict: {sync_iterations_result}")
            return sync_iterations_result

        total_shift_ms, final_corrected_file, updated_reference_number, iteration_count = sync_iterations_result
        logger.info(
            "[synchronize_video] "
            f"iteration_count={iteration_count}, total_shift_ms={total_shift_ms}, final_corrected_file='{final_corrected_file}', "
            f"updated_reference_number={updated_reference_number}"
        )

        if iteration_count == 1 and total_shift_ms == 0:
            ApiUtils.send_websocket_message(
                "Your clip was already in sync on the first pass; skipping final verification."
            )
            final_output_path: str = os.path.join(FINAL_OUTPUT_DIR, f"corrected_{original_filename}")
            if os.path.splitext(original_filename)[1].lower() == ".avi":
                shutil.copy(input_file, final_output_path)
                logger.debug(f"[synchronize_video] Copied original file to final_output_path: {final_output_path}")
            else:
                original_ext: str = os.path.splitext(original_filename)[1].lower()
                original_video_codec: Optional[str] = vid_props.get('codec_name')
                original_audio_codec: Optional[str] = audio_props.get('codec_name')
                restored_final: str = os.path.splitext(final_output_path)[0] + "_restored" + original_ext
                logger.debug(f"[synchronize_video] Re-encoding input file to restored_final: {restored_final}")
                await FFmpegUtils.reencode_to_original_format(input_file, restored_final, original_ext,
                                                        original_video_codec, original_audio_codec)
                final_output_path = restored_final

            logger.debug(
                f"[synchronize_video][EXIT] Returning (final_output_path='{final_output_path}', already_in_sync=True)"
            )
            return (final_output_path, True)

        final_output_path = await SyncNetUtils.finalize_sync(
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
        logger.debug(
            f"[synchronize_video][EXIT] Returning (final_output_path='{final_output_path}', already_in_sync=False)"
        )
        return (final_output_path, False)

    @staticmethod
    async def verify_synchronization(final_path: str, ref_str: str, fps: Union[int, float]) -> None:
        """Verifies the synchronization of the final output video.

        Debug statements have been added to log input parameters, steps performed, and the final
        computed offset.
        """
        logger.debug(
            f"[verify_synchronization][ENTER] final_path='{final_path}', ref_str='{ref_str}', fps={fps}"
        )
        logger.info("[verify_synchronization] Starting final verification pipeline...")
        await SyncNetUtils.run_pipeline(final_path, ref_str)

        final_log: str = os.path.join(FINAL_LOGS_DIR, f"final_output_{ref_str}.log")
        await SyncNetUtils.run_syncnet(ref_str, final_log)

        final_offset: int = AnalysisUtils.analyze_syncnet_log(final_log, fps)
        logger.info(f"[verify_synchronization] final_offset -> {final_offset} ms")
        logger.debug("[verify_synchronization][EXIT]")
