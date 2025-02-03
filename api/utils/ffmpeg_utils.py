import json
import os
import logging
import shutil
import subprocess
from .log_utils import LogUtils
from api.config.settings import FINAL_OUTPUT_DIR


LogUtils.configure_logging()
logger = logging.getLogger('ffmpeg_logger')  

class FFmpegUtils:
    """utility class for handling ffmpeg operations."""

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
        # make sure the input file exists by checking with os's path.exists method
        if not os.path.exists(input_file):
            # if not, log the error and return
            logger.error(f"input file not found: {input_file}")
            return

        # passing the path of the input file into one of the ffprobe functions and store the dict in 'audio_props'
        audio_props = FFmpegUtils.get_audio_properties(input_file)

        # if the audio_props string dict is not returned or empty, log an error and return
        if audio_props is None:
            logger.error(f"failed to retrieve audio properties from {input_file}")
            return

        # defining these three variables, casting the sample rate and channels as ints
        sample_rate = int(audio_props.get('sample_rate'))
        channels = int(audio_props.get('channels'))
        codec_name = audio_props.get('codec_name')

        # if the offset is greater than 0, the audio is behind the video, so the audio stream needs to be shifted forward by that many ms
        if offset_ms > 0:
            # defining a filter complex that delays the audio by the offset in ms for both channels and pads the start with whatever offset ms of silence
            filter_complex = f"adelay={offset_ms}|{offset_ms},apad"
            # log the shift direction and amount
            logger.info(f"shifting audio forward by {offset_ms} ms.")
        else:
            shift_abs = abs(offset_ms)
            # defines a filter complex that trims the beginning of the audio again by whatever ms the offset is and and pads the end with silence, the 1000 here is 
            # divides the shift by 1000 to convert from ms, as ffmpeg expects time values in seconds 
            filter_complex = f"atrim=start={shift_abs / 1000},apad"
            logger.info(f"shifting audio backward by {shift_abs} ms.")
        
        # build the ffmpeg command to shift the audio precisely
        cmd = [
            'ffmpeg', '-y',          # overwrites output files without prompting for confirmation
            '-i', input_file,        # specifies the input video file
            '-c:v', 'copy',          # copies the video stream exactly without re-encoding it
            '-af', filter_complex,   # applies the audio filter complex that was defined above
            '-c:a', codec_name,      # re-encodes the audio stream using the original audio codec from audio_props
            '-ar', str(sample_rate), # sets the audio sample rate to match the original video's sample rate
            '-ac', str(channels),    # sets the number of audio channels to match the original video's channel count
            '-threads', '4',         # utilizes 4 threads for encoding, enhancing performance by parallelizing processing
            '-shortest',             # ensures the output duration matches the shortest stream (typically the video stream)
            output_file              # specifies the output file path as ffmpeg can't modify files in place
        ]

        logger.debug(f"audio shift command string is : {cmd}")

        try:
            # runs the ffmpeg command using subprocess.run which captures its standard output and stderr so they can be redirected to to my ffmpeg.log 
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # logging FFmpeg's stdout and stderr to ffmpeg.log
            if result.stdout:
                logger.debug(f"FFmpeg stdout: {result.stdout}")
            if result.stderr:
                logger.debug(f"FFmpeg stderr: {result.stderr}")
            logger.info(f"Audio successfully shifted. Output saved to {output_file}")
        except subprocess.CalledProcessError as exc:
            # logs ffmpegs standard error output to ffmpeg.log
            logger.error(f"FFmpeg error stderr: {exc.stderr}")
            # raises a runtime error if the ffmpeg command returns a non-zero exit status
            # The error message includes stderr from ffmpeg for debugging
            raise RuntimeError(f"Error shifting audio for {input_file}: {exc.stderr}") from exc


    @staticmethod
    def apply_cumulative_shift(input_file, final_output, total_shift_ms):
        """
        Applies the total audio shift to the original input file.

        Args:
            input_file (str): Path to the original input video.
            final_output (str): Path where the final synchronized video will be saved.
            total_shift_ms (int): Total audio shift in milliseconds.
        """
        # creating the path for the copied file
        copied_file = os.path.join(FINAL_OUTPUT_DIR, os.path.basename(input_file))
        
        # copying the original input file to the final output directory
        shutil.copy(input_file, copied_file)


        # applying the cumulative audio shift with the total amount of ms
        try:
            FFmpegUtils.shift_audio(copied_file, final_output, total_shift_ms)
            logger.info(f"Applied cumulative audio shift. Final output saved to {final_output}")
        except Exception as e:
            logger.error(f"Failed to apply cumulative shift: {e}")
            raise RuntimeError(f"Could not apply cumulative shift: {e}")
        
        # remove the temporary file
        os.remove(copied_file)


    @staticmethod
    def get_video_fps(file_path):
        """
        Retrieves the frames per second (fps) of a video file using ffprobe with JSON output.

        Args:
            file_path (str): Path to the video file.

        Returns:
            float or None: FPS of the video if successful; otherwise, None.
        """

        # ffprobe command to extract the frame rate of the first video stream in JSON format
        cmd = [
            'ffprobe',
            '-v', 'error',                           # suppresses all logs except errors
            '-select_streams', 'v:0',                # selects the first video stream
            '-show_entries', 'stream=r_frame_rate',  # show only the r_frame_rate entry
            '-of', 'json',                           # output format as JSON
            file_path                                # path to the file thats being probed
        ]
        
        try:
            # run the ffprobe command and capture the output
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # loging ffprobe's standard outputt and standard errors to ffmpeg.log
            if result.stdout:
                logger.debug(f"FFprobe stdout: {result.stdout}")
            if result.stderr:
                logger.debug(f"FFprobe stderr: {result.stderr}")

            # parses the JSON output from ffprobe
            data = json.loads(result.stdout)

            # extracting value of the frame rate from the first video stream
            fps_str = data['streams'][0].get('r_frame_rate')

            # They're expressed as fractions (numerator/denominator) to allow precise representation of variable or non-integer frame rates,
            # so split them from the division operator to work with them
            num, den = map(int, fps_str.split('/'))

            # calculate the fps by dividing the numerator (number of frames) by the denominator (seconds)      
            fps = num / den

            logger.info(f"Got the fps for {file_path}: {fps}")
            return fps
        
        except subprocess.CalledProcessError as e:
            # log the error details if ffprobe fails to run properly
            logger.error(f"FFprobe error standard error: {e.stderr}")
            logger.error(f"ffprobe has failed for {file_path}")
            return None
        except Exception as e:
            # catch any other exceptions and log them
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

        # building the ffprobe command to retrieve the sample rate, codec, and number of channels from a file and store it in a json
        cmd = [
            'ffprobe', '-v', 'error', '-select_streams', 'a:0',
            '-show_entries', 'stream=sample_rate,channels,codec_name',
            '-of', 'json', file_path
        ]
        try:
            # executing the ffprobe command and capturing the output in 'result'
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # logging ffprobe's stdout and stderr to ffmpeg.log
            if result.stdout:
                logger.debug(f"FFprobe stdout: {result.stdout}")
            if result.stderr:
                logger.debug(f"FFprobe stderr: {result.stderr}")

            # parsing the JSON output from ffprobe
            data = json.loads(result.stdout)

            # getting the first audio stream from the data
            stream = data['streams'][0]

            # extracting the sample_rate, channels and the codec_name 
            audio_props = {
                'sample_rate': stream.get('sample_rate'),
                'channels': stream.get('channels'),
                'codec_name': stream.get('codec_name')
            }

            logger.info(f"retrieved audio properties for {file_path}: {audio_props}")
            return audio_props
        
        except subprocess.CalledProcessError as e:
            # logging ffprobe's stderr to ffmpeg.log
            logger.error(f"FFprobe error stderr: {e.stderr}")
            # logging the error and return None if the command fails
            logger.error(f"failed to get audio properties for {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"FFprobe unexpected error: {e}")
            logger.error(f"failed to get audio properties for {file_path}: {e}")
            return None
