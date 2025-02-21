import os
import logging
import shutil
import ffmpeg
from api.config.settings import FINAL_OUTPUT_DIR

logger = logging.getLogger("ffmpeg_logger")

class FFmpegUtils:
    """Utility class for handling FFmpeg operations."""

import os
import json
import logging
import shutil
import ffmpeg
from .log_utils import LogUtils
from api.config.settings import FINAL_OUTPUT_DIR

logger = logging.getLogger("ffmpeg_logger")

class FFmpegUtils:
    """Utility class for handling FFmpeg operations."""

    @staticmethod
    def shift_audio(input_file, output_file, offset_ms):
        """
        shifts the audio of the input video by a given millisecond offset,
        preserving original video properties and using the original audio codec.

        args:
            input_file (str): the path to the input video file.
            output_file (str): the path for the shifted output file.
            offset_ms (int): milliseconds to shift the audio. positive => forward, negative => backward.

        raises:
            RuntimeError: if the ffmpeg command fails.
        """
        if not os.path.exists(input_file):
            logger.error(f"input file not found: {input_file}")
            return

        audio_props = FFmpegUtils.get_audio_properties(input_file)
        if audio_props is None:
            logger.error(f"failed to retrieve audio properties from {input_file}")
            return

        sample_rate = int(audio_props.get('sample_rate'))
        channels = int(audio_props.get('channels'))
        codec_name = audio_props.get('codec_name')

        if offset_ms > 0:
            filter_complex = f"adelay={offset_ms}|{offset_ms},apad"
            logger.info(f"shifting audio forward by {offset_ms} ms.")
        else:
            shift_abs = abs(offset_ms)
            filter_complex = f"atrim=start={shift_abs / 1000},apad"
            logger.info(f"shifting audio backward by {shift_abs} ms.")

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
            logger.error(f"FFmpeg error stderr: {error_msg}")
            raise RuntimeError(f"Error shifting audio for {input_file}: {error_msg}") from exc

    @staticmethod
    def apply_cumulative_shift(input_file, final_output, total_shift_ms):
        """
        Applies the total audio shift to the original input file.

        Args:
            input_file (str): Path to the original input video.
            final_output (str): Path where the final synchronized video will be saved.
            total_shift_ms (int): Total audio shift in milliseconds.
        """
        copied_file = os.path.join(FINAL_OUTPUT_DIR, os.path.basename(input_file))
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
    def get_video_fps(file_path):
        """
        Retrieves the frames per second (fps) of a video file using ffprobe with JSON output.

        Args:
            file_path (str): Path to the video file.

        Returns:
            float or None: FPS of the video if successful; otherwise, None.
        """
        try:
            logger.debug(f"Probing video fps for {file_path}")
            info = ffmpeg.probe(file_path)
            streams = info.get('streams', [])
            if not streams:
                logger.error(f"No streams found in {file_path}")
                return None

            fps_str = streams[0].get('r_frame_rate')
            if not fps_str:
                logger.error(f"No r_frame_rate found for {file_path}")
                return None

            num, den = map(int, fps_str.split('/'))
            fps = num / den if den else 0
            logger.info(f"Got the fps for {file_path}: {fps}")
            return fps
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            logger.error(f"FFprobe error standard error: {error_msg}")
            logger.error(f"ffprobe has failed for {file_path}")
            return None
        except Exception as e:
            logger.error(f"FFprobe had an unexpected error: {e}")
            logger.error(f"An unexpected error has occurred while getting the fps for {file_path}: {e}")
            return None

    @staticmethod
    def get_audio_properties(file_path):
        """
        retrieves audio properties of a video file using ffprobe.

        args:
            file_path (str): path to the video file.

        returns:
            dict or None: dictionary containing audio properties; otherwise, None.
        """
        logger.debug(f"Probing audio properties for {file_path}")
        try:
            info = ffmpeg.probe(file_path)
            streams = info.get('streams', [])
            for stream in streams:
                if stream.get('codec_type') == 'audio':
                    audio_props = {
                        'sample_rate': stream.get('sample_rate'),
                        'channels': stream.get('channels'),
                        'codec_name': stream.get('codec_name')
                    }
                    logger.info(f"retrieved audio properties for {file_path}: {audio_props}")
                    return audio_props
            logger.error(f"No audio stream found in {file_path}")
            return None
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            logger.error(f"FFprobe error stderr: {error_msg}")
            logger.error(f"failed to get audio properties for {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"FFprobe unexpected error: {e}")
            logger.error(f"failed to get audio properties for {file_path}: {e}")
            return None

    @staticmethod
    def get_video_properties(file_path):
        """
        Retrieves video properties of a file using ffprobe.

        Args:
            file_path (str): Path to the video file.

        Returns:
            dict or None: Dictionary containing video properties (width, height, codec, avg_frame_rate)
                          if a video stream exists; otherwise, None.
        """
        logger.debug(f"Probing video properties for {file_path}")
        try:
            info = ffmpeg.probe(file_path)
            streams = info.get('streams', [])
            for stream in streams:
                if stream.get('codec_type') == 'video':
                    video_props = {
                        'width': stream.get('width'),
                        'height': stream.get('height'),
                        'codec_name': stream.get('codec_name'),
                        'avg_frame_rate': stream.get('avg_frame_rate')
                    }
                    logger.info(f"Retrieved video properties for {file_path}: {video_props}")
                    return video_props
            logger.info(f"No video stream found in {file_path}")
            return None
        except ffmpeg.Error as e:
            logger.error(f"Error retrieving video properties for {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while retrieving video properties: {e}")
            return None
