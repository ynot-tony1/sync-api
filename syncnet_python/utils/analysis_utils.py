import os
import re
import logging
from syncnet_python.utils.file_utils import FileUtils
from syncnet_python.utils.syncnet_utils import SyncNetUtils
from syncnet_python.utils.log_utils import LogUtils
from api.config.settings import FINAL_LOGS_DIR



LogUtils.configure_logging()
logger = logging.getLogger('analysis_logger')

class AnalysisUtils:
    """Utility class for analyzing SyncNet's output logs. """

    @staticmethod
    def analyze_syncnet_log(log_filename, fps):

        """
        Analyzes the SyncNet log file to determine the synchronization offset.

        Args:
            log_filename (path) : the path to the SyncNet log file.
            fps (int) : frames per second of the video.

        Returns:
            offset_ms (int): Offset in milliseconds.
        """

        # passing the filename of the log into my file utility function and storing the output in the new variable 'log_content'
        log_content = FileUtils.read_log_file(log_filename)
        
        # checks if log content has been successfully read in
        if not log_content:

            # sending a warning to the logger with the full path of the log file if not found
            logger.warning(f"No content inside this log file: {log_filename}")

            # returns a 0 offset if there is no content found
            return 0

        # passing the log content into the regex finder function to parse the pairs, 
        # containing the offset and their corresponding condfidence scores, from the log into a new list 'pairs'
        pairs = AnalysisUtils.extract_offset_confidence_pairs(log_content)


        # if no pairs are shown, log that info and return 0 for the offset
        if not pairs:
            logger.warning("Couldn't find any pairs in the SyncNet log.")
            return 0

        # pass list of pairs into aggregate confidence function and store the values in a new defaultDict called offset_conf
        offset_conf = AnalysisUtils.aggregate_confidence(pairs)

        # if no offset_conf is created or it is empty, log that fact and return 0 for the offset
        if not offset_conf:
            logger.warning("Couldnt add up confidence scores.")
            return 0

        # using the max method on offset_conf dictionary to find the offset with the highest aggregated confidence score     
        best_offset = max(offset_conf, key=offset_conf.get)

        # passing the best_offset int and the fps into my conversion function and store the output in ms inside an new variable called offset_ms
        offset_ms = AnalysisUtils.convert_frames_to_ms(best_offset, fps) 

        # logging the best offset in frames and ms
        logger.info(f"The best offset would be: {best_offset} frames ({offset_ms} ms)")

        # returs the offset in ms
        return offset_ms


    @staticmethod
    def extract_offset_confidence_pairs(log_text):
        """
        Extracts offset and confidence pairs from the log text.

        Args:
            log_text (str): content of the SyncNet log file.

        Returns:
            pairs (list): list of tuples containing offset and confidence.
        """
        # declares a regex pattern that matches "AV offset:" followed by an optional sign and integer,
        # then non-greedily matches any characters until "Confidence:" followed by a floating-point number.
        pattern = r'AV offset:\s*([-+]?\d+).*?Confidence:\s*([\d.]+)'

        # using re.findall to retrieve all matching (offset, confidence) tuples.
        # The re.DOTALL flag allows '.' to match newline characters, enabling multi-line pattern matching, pretty handy considering the two values are on different lines within the log files.
        matches = re.findall(pattern, log_text, re.DOTALL)

        # initialize an empty list to store the tuples
        pairs = []

        # iterate throgh each pair in 'matches'
        for offset, confidence in matches:
            # cast 'offset' to an integer and 'confidence' to a float
            converted_offset = int(offset)
            converted_confidence = float(confidence)
            
            # making a new tuple for each of the values
            converted_pair = (converted_offset, converted_confidence)
            
            # appending the converted tuple to the 'pairs' list
            pairs.append(converted_pair)
        # Returns the list of tuples
        logger.debug(f"Extracted pairs: {pairs}")
        return pairs

    @staticmethod
    def aggregate_confidence(pairs):
        """
        Aggregates confidence scores for each synchronization offset.

        Args:
            pairs (list of tuples): A list where each tuple contains: offset (int) and confidence (float):


        Returns:
            dict: A dictionary mapping each offset (int) to its aggregated confidence score (float).

        """
        # initialize a dictionary to accumulate confidence scores for each offset
        confidence_map = {}

        # iterate through each pair
        for offset, confidence in pairs:
            if offset in confidence_map:
                # if the offset already exists, adds the confidence score to the existing total
                confidence_map[offset] += confidence
            else:
                # if the offset doesn't exist, it gets initialized with the current confidence score
                confidence_map[offset] = confidence

        # Return the aggregated confidence map
        return confidence_map
    
    @staticmethod
    def convert_frames_to_ms(frames, fps):
        """
        Converts frame counts to milliseconds.

        Args:
            frames (int): Number of frames.
            fps (float): Frames per second.

        Returns:
            int: Time in ms.

        Raises:
            ValueError: If `fps` is missing or invalid.
        """
        # checking if fps is provided
        if fps:
            # calculate duration per frame in ms
            duration_per_frame_ms = 1000 / fps
        else:
            logger.error("fps value is missing. Can't convert frames to milliseconds.")
            raise ValueError("fps must be provided and can't be None.")

        # calculate total time in milliseconds, cast it as an int and return it
        return int(frames * duration_per_frame_ms)
    
    @staticmethod
    def verify_synchronization(final_path, ref_str, fps, tol_ms):
        """
        Verifies that the final synchronized video is within the tolerance.

        Args:
            final_path (str): Path to the final synchronized video.
            ref_str (str): Reference string identifier.
            fps (float): Frames per second of the video.
            tol_ms (int): Tolerance in milliseconds.
        """
        logger.info("Starting final synchronization verification...")

        # runs the file through the pipeline using its path and reference string
        SyncNetUtils.run_pipeline(final_path, ref_str)

        # define the path of the final log and store in a new variable
        final_log = os.path.join(FINAL_LOGS_DIR, f"final_output_{ref_str}.log")


        # passing the reference and the path of the final log dir into my run_syncnet function which builds a command to run the model with them
        SyncNetUtils.run_syncnet(ref_str, final_log)

        # shows the final verified offset by passing the final log and the fps into the helper function for analysis
        final_offset = AnalysisUtils.analyze_syncnet_log(final_log, fps)

        logger.info(f"Final offset: {final_offset} ms")

        # ensures the final offset is within 10ms tolerance (anything below 20ms is invisible to the human eye)
        if abs(final_offset) <= tol_ms:
            logger.info("Final synchronization is within the acceptable tolerance!")
            logger.info("It's done!!")

        else:
        # if its still out of sync, log the offset
            logger.info(f"Final synchronization has exceeded the tolerance by {final_offset} ms.")
    