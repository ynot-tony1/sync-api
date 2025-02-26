"""
Utility class for handling FFmpeg operations.
"""

import os
import logging
import shutil
from typing import Optional, Dict, Any, List

import ffmpeg

from api.config.type_settings import FINAL_OUTPUT_DIR

logger: logging.Logger = logging.getLogger("ffmpeg_logger")


class FFmpegUtils:
    @staticmethod
    def reencode_to_avi(input_file: str, output_file: str) -> None:
        """
        Re-encodes the input file to an AVI container with PCM S16LE audio.
        
        Args:
            input_file (str): Path to the input video.
            output_file (str): Path where the AVI file will be saved.
        
        Raises:
            RuntimeError: If FFmpeg fails.
        """
        logger.info(f"Re-encoding {input_file} to {output_file} as AVI with PCM audio.")
        try:
            out, err = (
                ffmpeg
                .input(input_file)
                .output(output_file, vcodec='mpeg4', acodec='pcm_s16le', strict='experimental')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            logger.debug(f"FFmpeg stdout: {out.decode('utf-8') if out else 'N/A'}")
            logger.debug(f"FFmpeg stderr: {err.decode('utf-8') if err else 'N/A'}")
        except ffmpeg.Error as e:
            error_msg: str = e.stderr.decode('utf-8') if e.stderr else str(e)
            logger.error(f"FFmpeg error while re-encoding to AVI: {error_msg}")
            raise RuntimeError(f"Failed to re-encode {input_file} to AVI: {error_msg}") from e

    @staticmethod
    def reencode_to_original_format(
        input_avi_file: str,
        output_file: str,
        original_container_ext: str,
        original_video_codec: Optional[str],
        original_audio_codec: Optional[str]
    ) -> None:
        """
        Re-encodes the corrected AVI file back to the original container format.
        
        Args:
            input_avi_file (str): Path to the corrected AVI.
            output_file (str): Path for the final output.
            original_container_ext (str): Target container extension.
            original_video_codec (Optional[str]): Original video codec.
            original_audio_codec (Optional[str]): Original audio codec.
        
        Raises:
            RuntimeError: If FFmpeg fails.
        """
        vcodec: str = original_video_codec if original_video_codec else "copy"
        acodec: str = original_audio_codec if original_audio_codec else "copy"
        logger.info(f"Re-encoding {input_avi_file} back to {output_file} using container ext {original_container_ext}.")
        try:
            out, err = (
                ffmpeg
                .input(input_avi_file)
                .output(output_file, vcodec=vcodec, acodec=acodec)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            logger.debug(f"FFmpeg stdout: {out.decode('utf-8') if out else 'N/A'}")
            logger.debug(f"FFmpeg stderr: {err.decode('utf-8') if err else 'N/A'}")
        except ffmpeg.Error as e:
            error_msg: str = e.stderr.decode('utf-8') if e.stderr else str(e)
            logger.error(f"FFmpeg error while re-encoding to original format: {error_msg}")
            raise RuntimeError(f"Failed to re-encode to original container {original_container_ext}: {error_msg}") from e

    @staticmethod
    def shift_audio(input_file: str, output_file: str, offset_ms: int) -> None:
        """
        Shifts the audio of the input file by a specified offset in milliseconds.
        
        Args:
            input_file (str): Path to the input video.
            output_file (str): Path for the output video.
            offset_ms (int): Milliseconds to shift the audio.
        
        Raises:
            RuntimeError: If FFmpeg fails.
        """
        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            return

        audio_props: Optional[Dict[str, Any]] = FFmpegUtils.get_audio_properties(input_file)
        if audio_props is None:
            logger.error(f"Failed to retrieve audio properties from {input_file}")
            return

        sample_rate: int = int(audio_props.get('sample_rate'))
        channels: int = int(audio_props.get('channels'))
        codec_name: str = audio_props.get('codec_name')

        if offset_ms > 0:
            filter_complex: str = f"adelay={offset_ms}|{offset_ms},apad"
            logger.info(f"Shifting audio forward by {offset_ms} ms.")
        else:
            shift_abs: int = abs(offset_ms)
            filter_complex = f"atrim=start={shift_abs / 1000},apad"
            logger.info(f"Shifting audio backward by {shift_abs} ms.")

        logger.debug(f"Audio shift filter: {filter_complex}")

        try:
            out, err = (
                ffmpeg
                .input(input_file)
                .output(
                    output_file,
                    **{
                        'c:v': 'copy',
                        'af': filter_complex,
                        'c:a': codec_name,
                        'ar': sample_rate,
                        'ac': channels,
                        'threads': '4',
                        'shortest': None
                    }
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            logger.debug(f"FFmpeg stdout: {out.decode('utf-8') if out else 'N/A'}")
            logger.debug(f"FFmpeg stderr: {err.decode('utf-8') if err else 'N/A'}")
            logger.info(f"Audio successfully shifted. Output saved to {output_file}")
        except ffmpeg.Error as exc:
            error_msg = exc.stderr.decode('utf-8') if exc.stderr else str(exc)
            logger.error(f"FFmpeg error: {error_msg}")
            raise RuntimeError(f"Error shifting audio for {input_file}: {error_msg}") from exc

    @staticmethod
    def apply_cumulative_shift(input_file: str, final_output: str, total_shift_ms: int) -> None:
        """
        Applies a cumulative audio shift to the input file.
        
        Args:
            input_file (str): Original input video.
            final_output (str): Path for final output.
            total_shift_ms (int): Total shift in milliseconds.
        
        Raises:
            RuntimeError: If shifting fails.
        """
        copied_file: str = os.path.join(FINAL_OUTPUT_DIR, os.path.basename(input_file))
        shutil.copy(input_file, copied_file)
        logger.info(f"Copied {input_file} to {copied_file} for shifting.")

        try:
            FFmpegUtils.shift_audio(copied_file, final_output, total_shift_ms)
            logger.info(f"Applied cumulative audio shift. Final output saved to {final_output}")
        except Exception as e:
            logger.error(f"Failed to apply cumulative shift: {e}")
            raise RuntimeError(f"Could not apply cumulative shift: {e}")
        finally:
            if os.path.exists(copied_file):
                os.remove(copied_file)
                logger.debug(f"Removed temporary file {copied_file}")

    @staticmethod
    def get_audio_properties(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves audio properties from a video file.
        
        Args:
            file_path (str): Path to the video file.
        
        Returns:
            Optional[Dict[str, Any]]: Dictionary of audio properties or None.
        """
        logger.debug(f"Probing audio properties for {file_path}")
        try:
            info: Dict[str, Any] = ffmpeg.probe(file_path)
            streams: List[Dict[str, Any]] = info.get('streams', [])
            for stream in streams:
                if stream.get('codec_type') == 'audio':
                    audio_props: Dict[str, Any] = {
                        'sample_rate': stream.get('sample_rate'),
                        'channels': stream.get('channels'),
                        'codec_name': stream.get('codec_name')
                    }
                    logger.info(f"Retrieved audio properties for {file_path}: {audio_props}")
                    return audio_props
            logger.error(f"No audio stream found in {file_path}")
            return None
        except ffmpeg.Error as e:
            error_msg: str = e.stderr.decode('utf-8') if e.stderr else str(e)
            logger.error(f"FFprobe error: {error_msg}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while retrieving audio properties for {file_path}: {e}")
            return None

    @staticmethod
    def get_video_properties(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves video properties from a video file.
        
        Args:
            file_path (str): Path to the video file.
        
        Returns:
            Optional[Dict[str, Any]]: Dictionary of video properties or None.
        """
        logger.debug(f"Probing video properties for {file_path}")
        try:
            info: Dict[str, Any] = ffmpeg.probe(file_path)
            streams: List[Dict[str, Any]] = info.get('streams', [])
            for stream in streams:
                if stream.get('codec_type') == 'video':
                    avg_frame_rate: str = stream.get('avg_frame_rate', '0/0')
                    try:
                        num, den = avg_frame_rate.split('/')
                        fps: Optional[float] = float(num) / float(den) if float(den) != 0 else None
                    except Exception as e:
                        logger.error(f"Error converting avg_frame_rate '{avg_frame_rate}' to fps: {e}")
                        fps = None
                    video_props: Dict[str, Any] = {
                        'width': stream.get('width'),
                        'height': stream.get('height'),
                        'codec_name': stream.get('codec_name'),
                        'avg_frame_rate': avg_frame_rate,
                        'fps': fps
                    }
                    logger.info(f"Retrieved video properties for {file_path}: {video_props}")
                    return video_props
            logger.info(f"No video stream found in {file_path}")
            return None
        except ffmpeg.Error as e:
            logger.error(f"Error retrieving video properties for {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while retrieving video properties for {file_path}: {e}")
            return None
