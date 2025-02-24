import os
import logging
import shutil
import ffmpeg
from api.config.settings import FINAL_OUTPUT_DIR

logger = logging.getLogger("ffmpeg_logger")


class FFmpegUtils:
    """Utility class for handling FFmpeg operations."""

    @staticmethod
    def reencode_to_avi(input_file: str, output_file: str) -> None:
        """
        Re-encodes the input file to an .avi container with PCM S16LE audio.

        The video is re-encoded to a generically safe codec ('mpeg4') suitable for the AVI container.
        This method uses FFmpeg to convert the input file, setting the video codec to 'mpeg4' and the audio
        codec to 'pcm_s16le'. It overwrites any existing output file and logs the FFmpeg standard output and error.
        If FFmpeg fails, a RuntimeError is raised with the error message.

        Args:
            input_file (str): Path to the user's original video.
            output_file (str): Path where the .avi file will be created.

        Raises:
            RuntimeError: If FFmpeg fails during the re-encoding process.
        """
        logger.info(f"Re-encoding {input_file} to {output_file} as AVI with PCM audio.")
        try:
            out, err = (
                ffmpeg
                .input(input_file)
                .output(
                    output_file,
                    vcodec='mpeg4',
                    acodec='pcm_s16le',
                    strict='experimental'
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            logger.debug(f"FFmpeg stdout: {out.decode('utf-8') if out else 'N/A'}")
            logger.debug(f"FFmpeg stderr: {err.decode('utf-8') if err else 'N/A'}")
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            logger.error(f"FFmpeg error while re-encoding to AVI: {error_msg}")
            raise RuntimeError(f"Failed to re-encode {input_file} to AVI: {error_msg}") from e

    @staticmethod
    def reencode_to_original_format(
        input_avi_file: str,
        output_file: str,
        original_container_ext: str,
        original_video_codec: str,
        original_audio_codec: str
    ) -> None:
        """
        Converts the final corrected .avi back into the original container format using the original codecs.

        This method takes a corrected .avi file and re-encodes it into the original container format
        (e.g., .mp4, .mov) using the specified original video and audio codecs. If the original codecs
        are not provided, it defaults to copying the respective streams. The output file is overwritten
        if it exists. Any FFmpeg errors encountered during the process will result in a RuntimeError.

        Args:
            input_avi_file (str): Path to the corrected .avi file from the pipeline.
            output_file (str): Path to the final re-encoded file (including the correct extension).
            original_container_ext (str): The target container extension (e.g., ".mp4", ".mov").
            original_video_codec (str): The original video codec from the input file, if known.
            original_audio_codec (str): The original audio codec from the input file, if known.

        Raises:
            RuntimeError: If FFmpeg fails during the re-encoding process.
        """
        vcodec = original_video_codec if original_video_codec else "copy"
        acodec = original_audio_codec if original_audio_codec else "copy"

        logger.info(
            f"Re-encoding {input_avi_file} back to {output_file} "
            f"using container ext {original_container_ext}."
        )
        try:
            out, err = (
                ffmpeg
                .input(input_avi_file)
                .output(
                    output_file,
                    vcodec=vcodec,
                    acodec=acodec
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            logger.debug(f"FFmpeg stdout: {out.decode('utf-8') if out else 'N/A'}")
            logger.debug(f"FFmpeg stderr: {err.decode('utf-8') if err else 'N/A'}")
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            logger.error(f"FFmpeg error while re-encoding to original format: {error_msg}")
            raise RuntimeError(
                f"Failed to re-encode to original container {original_container_ext}: {error_msg}"
            ) from e

    @staticmethod
    def shift_audio(input_file, output_file, offset_ms):
        """
        Shifts the audio of the input video by a specified millisecond offset.

        This method adjusts the audio track of the provided video file by the given offset.
        A positive offset shifts the audio forward, whereas a negative offset shifts it backward.
        It preserves the original video stream and uses the same audio codec. The function retrieves
        the audio properties from the input file and constructs an FFmpeg filter accordingly. If the
        input file does not exist or audio properties cannot be retrieved, an error is logged. FFmpeg is
        then used to apply the audio shift, and any errors during this process will result in a RuntimeError.

        Args:
            input_file (str): The path to the input video file.
            output_file (str): The path for the output video with shifted audio.
            offset_ms (int): The number of milliseconds to shift the audio. Positive values shift
                             the audio forward; negative values shift it backward.

        Raises:
            RuntimeError: If the FFmpeg command fails or an error occurs during processing.
        """
        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            return

        audio_props = FFmpegUtils.get_audio_properties(input_file)
        if audio_props is None:
            logger.error(f"Failed to retrieve audio properties from {input_file}")
            return

        sample_rate = int(audio_props.get('sample_rate'))
        channels = int(audio_props.get('channels'))
        codec_name = audio_props.get('codec_name')

        if offset_ms > 0:
            filter_complex = f"adelay={offset_ms}|{offset_ms},apad"
            logger.info(f"Shifting audio forward by {offset_ms} ms.")
        else:
            shift_abs = abs(offset_ms)
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
    def apply_cumulative_shift(input_file, final_output, total_shift_ms):
        """
        Applies a cumulative audio shift to the original input file.

        This method creates a temporary copy of the input video in the FINAL_OUTPUT_DIR,
        applies an audio shift to the copied file using the specified total shift in milliseconds,
        and then cleans up the temporary file after processing. The final synchronized video is saved
        to the provided output path. Any errors during the shifting process will result in a RuntimeError.

        Args:
            input_file (str): Path to the original input video.
            final_output (str): Path where the final synchronized video will be saved.
            total_shift_ms (int): Total audio shift in milliseconds to be applied.

        Raises:
            RuntimeError: If the cumulative audio shift process fails.
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
        Retrieves the frames per second (FPS) of a video file.

        This function uses FFprobe to extract the FPS value from the video stream of the specified file.
        It probes the file for stream information and retrieves the 'r_frame_rate' from the first stream.
        The FPS is calculated by dividing the numerator by the denominator from the 'r_frame_rate' string.
        If no streams are found or an error occurs, the function logs an error and returns None.

        Args:
            file_path (str): The path to the video file.

        Returns:
            float or None: The FPS of the video if successfully retrieved; otherwise, None.
        """
        try:
            logger.debug(f"Probing video FPS for {file_path}")
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
            logger.info(f"Obtained FPS for {file_path}: {fps}")
            return fps
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            logger.error(f"FFprobe error: {error_msg}")
            logger.error(f"FFprobe has failed for {file_path}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while retrieving FPS for {file_path}: {e}")
            return None

    @staticmethod
    def get_audio_properties(file_path):
        """
        Retrieves audio properties from a video file.

        This method uses FFprobe to extract audio properties such as sample rate, number of channels,
        and the audio codec from the provided video file. It iterates through the streams until it finds
        one with the 'audio' codec type. If an audio stream is found, a dictionary containing the audio
        properties is returned. If no audio stream is found or an error occurs, the function logs an error
        and returns None.

        Args:
            file_path (str): The path to the video file.

        Returns:
            dict or None: A dictionary containing audio properties if an audio stream is found; otherwise, None.
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
                    logger.info(f"Retrieved audio properties for {file_path}: {audio_props}")
                    return audio_props
            logger.error(f"No audio stream found in {file_path}")
            return None
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            logger.error(f"FFprobe error: {error_msg}")
            logger.error(f"Failed to get audio properties for {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while retrieving audio properties for {file_path}: {e}")
            return None

    @staticmethod
    def get_video_properties(file_path):
        """
        Retrieves video properties from a video file.

        This function uses FFprobe to extract key video properties such as width, height, codec name,
        average frame rate, and the calculated FPS from the provided video file. It searches through the
        streams for one with the 'video' codec type and attempts to convert the 'avg_frame_rate' to FPS.
        If a video stream is found, a dictionary containing the video properties is returned; otherwise, None.

        Args:
            file_path (str): The path to the video file.

        Returns:
            dict or None: A dictionary containing video properties if a video stream is found; otherwise, None.
        """
        logger.debug(f"Probing video properties for {file_path}")
        try:
            info = ffmpeg.probe(file_path)
            streams = info.get('streams', [])
            for stream in streams:
                if stream.get('codec_type') == 'video':
                    avg_frame_rate = stream.get('avg_frame_rate')
                    try:
                        num, den = avg_frame_rate.split('/')
                        fps = float(num) / float(den) if float(den) != 0 else None
                    except Exception as e:
                        logger.error(f"Error converting avg_frame_rate '{avg_frame_rate}' to fps: {e}")
                        fps = None
                    video_props = {
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
