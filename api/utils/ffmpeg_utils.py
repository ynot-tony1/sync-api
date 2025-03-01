import os
import json
import logging
import shutil
import asyncio
from typing import Optional, Dict, List, Union
from api.config.settings import FINAL_OUTPUT_DIR
from api.types.props import VideoProps, AudioProps

logger: logging.Logger = logging.getLogger("ffmpeg_logger")


class FFmpegUtils:
    """Utility class for handling various FFmpeg operations asynchronously.

    This class provides methods for re-encoding videos to AVI format, converting AVI
    files back to their original container/codec, shifting audio tracks by a specified
    offset, applying cumulative audio shifts, and extracting audio and video properties
    using ffprobe. All operations are executed using asyncio subprocesses to prevent
    blocking the event loop during CPU-intensive or long-running FFmpeg tasks.
    """

    @staticmethod
    async def reencode_to_avi(input_file: str, output_file: str) -> None:
        """Re-encodes a given input video file to an AVI format with specific codecs.

        Args:
            input_file (str): Path to the source file to be converted.
            output_file (str): Desired path of the converted AVI file.

        Raises:
            RuntimeError: If the ffmpeg command fails with a non-zero exit code.
        """
        logger.debug(f"[ENTER] reencode_to_avi -> input_file='{input_file}', output_file='{output_file}'")
        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_file,
            "-vcodec", "mpeg4",
            "-acodec", "pcm_s16le",
            "-strict", "experimental",
            output_file
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            error_msg = stderr.decode("utf-8", "ignore")
            logger.error(f"[reencode_to_avi] FFmpeg error -> {error_msg}")
            raise RuntimeError(f"Failed to re-encode to AVI: {error_msg}")
        logger.debug("[EXIT] reencode_to_avi")

    @staticmethod
    async def reencode_to_original_format(
        input_avi_file: str,
        output_file: str,
        original_container_ext: str,
        original_video_codec: Optional[str],
        original_audio_codec: Optional[str]
    ) -> None:
        """Re-encodes an AVI file back to its original container/codec.

        Args:
            input_avi_file (str): Path to the intermediate AVI file.
            output_file (str): Desired path of the final restored video.
            original_container_ext (str): File extension of the original container (e.g. '.mp4').
            original_video_codec (Optional[str]): Original video codec if known.
            original_audio_codec (Optional[str]): Original audio codec if known.

        Raises:
            RuntimeError: If the ffmpeg command fails or if re-encoding fails.
        """
        logger.debug(
            f"[ENTER] reencode_to_original_format -> input_avi_file='{input_avi_file}', "
            f"output_file='{output_file}', original_container_ext='{original_container_ext}', "
            f"original_video_codec='{original_video_codec}', original_audio_codec='{original_audio_codec}'"
        )
        vcodec = original_video_codec if original_video_codec else "copy"
        acodec = original_audio_codec if original_audio_codec else "copy"
        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_avi_file,
            "-vcodec", vcodec,
            "-acodec", acodec,
            output_file
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            error_msg = stderr.decode("utf-8", "ignore")
            logger.error(f"[reencode_to_original_format] FFmpeg error -> {error_msg}")
            raise RuntimeError(
                f"Failed to re-encode to original container {original_container_ext}: {error_msg}"
            )
        logger.debug("[EXIT] reencode_to_original_format")

    @staticmethod
    async def shift_audio(input_file: str, output_file: str, offset_ms: int) -> None:
        """Shifts the audio track of a file either forwards or backwards by a given offset.

        Args:
            input_file (str): Path to the source video.
            output_file (str): Desired path of the shifted-output file.
            offset_ms (int): Millisecond offset to apply. Positive for forward, negative for backward.

        Raises:
            RuntimeError: If the ffmpeg operation fails or if the input file is missing.
        """
        logger.debug(
            f"[ENTER] shift_audio -> input_file='{input_file}', output_file='{output_file}', offset_ms={offset_ms}"
        )
        if not os.path.exists(input_file):
            logger.error(f"[shift_audio] Input file not found -> '{input_file}'")
            return
        audio_props = await FFmpegUtils.get_audio_properties(input_file)
        logger.debug(f"[shift_audio] audio_props -> {audio_props}")
        if audio_props is None:
            logger.error(f"[shift_audio] No audio props found in '{input_file}'")
            return
        sample_rate = int(audio_props.get("sample_rate"))
        channels = int(audio_props.get("channels"))
        codec_name = audio_props.get("codec_name")
        if offset_ms > 0:
            filter_complex = f"adelay={offset_ms}|{offset_ms},apad"
            logger.info(f"[shift_audio] Shifting audio FORWARD by {offset_ms} ms.")
        else:
            shift_abs = abs(offset_ms)
            filter_complex = f"atrim=start={shift_abs / 1000},apad"
            logger.info(f"[shift_audio] Shifting audio BACKWARD by {shift_abs} ms.")
        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_file,
            "-c", "copy",
            "-af", filter_complex,
            "-c:a", codec_name,
            "-ar", str(sample_rate),
            "-ac", str(channels),
            "-threads", "4",
            "-shortest",
            output_file
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            error_msg = stderr.decode("utf-8", "ignore")
            logger.error(f"[shift_audio] FFmpeg error -> {error_msg}")
            raise RuntimeError(f"Error shifting audio for {input_file}: {error_msg}")
        logger.debug("[EXIT] shift_audio")

    @staticmethod
    async def apply_cumulative_shift(input_file: str, final_output: str, total_shift_ms: int) -> None:
        """Copies a file into the final output directory, then applies a global audio shift.

        Args:
            input_file (str): Source file to be shifted.
            final_output (str): Desired path of the final shifted file.
            total_shift_ms (int): Total millisecond offset to shift the audio.

        Raises:
            RuntimeError: If any subprocess errors occur during the shift operation.
        """
        logger.debug(
            f"[ENTER] apply_cumulative_shift -> input_file='{input_file}', final_output='{final_output}', "
            f"total_shift_ms={total_shift_ms}"
        )
        copied_file = os.path.join(FINAL_OUTPUT_DIR, os.path.basename(input_file))
        shutil.copy(input_file, copied_file)
        logger.debug(f"[apply_cumulative_shift] Copied input -> '{copied_file}'")
        try:
            await FFmpegUtils.shift_audio(copied_file, final_output, total_shift_ms)
            logger.info(f"[apply_cumulative_shift] Completed shift. final_output='{final_output}'")
        except Exception as e:
            logger.error(f"[apply_cumulative_shift] Exception -> {str(e)}")
            raise RuntimeError(f"Could not apply cumulative shift: {e}")
        finally:
            if os.path.exists(copied_file):
                os.remove(copied_file)
                logger.debug(f"[apply_cumulative_shift] Removed temp file -> '{copied_file}'")
        logger.debug("[EXIT] apply_cumulative_shift")

    @staticmethod
    async def get_audio_properties(file_path: str) -> Optional[AudioProps]:
        """Retrieves audio properties from the given file using ffprobe.

        Args:
            file_path (str): Path to the input media file.

        Returns:
            Optional[AudioProps]: A dictionary containing audio information
            (sample_rate, channels, codec_name), or None if no audio stream is found.

        Raises:
            RuntimeError: If ffprobe fails to execute.
        """
        logger.debug(f"[ENTER] get_audio_properties -> file_path='{file_path}'")
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            file_path
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            error_msg = stderr.decode("utf-8", "ignore")
            logger.error(f"[get_audio_properties] FFprobe error -> {error_msg}")
            return None
        try:
            metadata = json.loads(stdout.decode("utf-8", "ignore"))
            streams = metadata.get("streams", [])
            for stream in streams:
                if stream.get("codec_type") == "audio":
                    audio_props: AudioProps = {
                        "sample_rate": stream.get("sample_rate"),
                        "channels": stream.get("channels"),
                        "codec_name": stream.get("codec_name")
                    }
                    logger.info(f"[get_audio_properties] Found audio props -> {audio_props}")
                    logger.debug(f"[EXIT] get_audio_properties -> {audio_props}")
                    return audio_props
            logger.error(f"[get_audio_properties] No audio stream found in '{file_path}'")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"[get_audio_properties] JSON parsing error -> {str(e)}")
            return None

    @staticmethod
    async def get_video_properties(file_path: str) -> Optional[VideoProps]:
        """Retrieves video properties from the given file using ffprobe.

        Args:
            file_path (str): Path to the input media file.

        Returns:
            Optional[VideoProps]: A dictionary containing video information
            (codec_name, avg_frame_rate, fps), or None if no video stream is found.

        Raises:
            RuntimeError: If ffprobe fails to execute.
        """
        logger.debug(f"[ENTER] get_video_properties -> file_path='{file_path}'")
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            file_path
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            error_msg = stderr.decode("utf-8", "ignore")
            logger.error(f"[get_video_properties] ffprobe error -> {error_msg}")
            return None
        try:
            metadata = json.loads(stdout.decode("utf-8", "ignore"))
            streams = metadata.get("streams", [])
            for stream in streams:
                if stream.get("codec_type") == "video":
                    avg_frame_rate = stream.get("avg_frame_rate", "0/0")
                    fps = 0.0
                    try:
                        num, den = avg_frame_rate.split("/")
                        if float(den) != 0:
                            fps = float(num) / float(den)
                    except Exception as e:
                        logger.error(f"[get_video_properties] Error parsing avg_frame_rate='{avg_frame_rate}' -> {str(e)}")
                    video_props: VideoProps = {
                        "codec_name": stream.get("codec_name"),
                        "avg_frame_rate": avg_frame_rate,
                        "fps": fps
                    }
                    logger.info(f"[get_video_properties] Found video props -> {video_props}")
                    logger.debug(f"[EXIT] get_video_properties -> {video_props}")
                    return video_props
            logger.info(f"[get_video_properties] No video stream found in '{file_path}'")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"[get_video_properties] JSON parsing error -> {str(e)}")
            return None
