import os
import re
import logging
from .file_utils import FileUtils
from .log_utils import LogUtils
from api.config.settings import FINAL_LOGS_DIR

LogUtils.configure_logging()
logger = logging.getLogger('analysis_logger')


class AnalysisUtils:
    """Utility class for analyzing SyncNet's output logs."""

    @staticmethod
    def analyze_syncnet_log(log_filename, fps):
        """
        Analyzes the SyncNet log file to determine the synchronization offset.

        This function reads the log file specified by `log_filename` using the file utility,
        then extracts offset and confidence pairs from the log content via a regular expression.
        It verifies that the log content exists and logs a warning with the full path of the log file
        if no content is found, returning an offset of 0. If valid offset-confidence pairs are found,
        it aggregates the confidence scores for each offset. If no pairs are found or the aggregation
        is empty, it logs the appropriate warning and returns 0. Finally, it identifies the offset with the
        highest aggregated confidence score, converts this offset from frames to milliseconds using the
        provided `fps`, logs the best offset in frames and milliseconds, and returns the resulting value.

        Args:
            log_filename (str): The path to the SyncNet log file.
            fps (int or float): Frames per second of the video.

        Returns:
            int: Offset in milliseconds. Returns 0 if the log file has no content or no valid offset-confidence pairs.
        """
        log_content = FileUtils.read_log_file(log_filename)
        if not log_content:
            logger.warning(f"No content inside this log file: {log_filename}")
            return 0

        pairs = AnalysisUtils.extract_offset_confidence_pairs(log_content)
        if not pairs:
            logger.warning("Couldn't find any pairs in the SyncNet log.")
            return 0

        offset_conf = AnalysisUtils.aggregate_confidence(pairs)
        if not offset_conf:
            logger.warning("Couldnt add up confidence scores.")
            return 0

        best_offset = max(offset_conf, key=offset_conf.get)
        offset_ms = AnalysisUtils.convert_frames_to_ms(best_offset, fps)
        logger.info(f"The offset would be: {best_offset} frames ({offset_ms} ms)")
        return offset_ms

    @staticmethod
    def extract_offset_confidence_pairs(log_text):
        """
        Extracts offset and confidence pairs from the provided log text.

        This function declares a regex pattern that matches "AV offset:" followed by an optional sign
        and an integer, then non-greedily matches any characters until "Confidence:" followed by a floating-point
        number. It uses `re.findall` with the `re.DOTALL` flag to retrieve all matching (offset, confidence)
        tuples from the log text. Each offset is cast to an integer and each confidence to a float before
        being stored as a tuple in a list, which is then returned.

        Args:
            log_text (str): The content of the SyncNet log file.

        Returns:
            list of tuples: A list where each tuple contains an offset (int) and its corresponding confidence (float).
        """
        pattern = r'AV offset:\s*([-+]?\d+).*?Confidence:\s*([\d.]+)'
        matches = re.findall(pattern, log_text, re.DOTALL)
        pairs = []
        for offset, confidence in matches:
            converted_offset = int(offset)
            converted_confidence = float(confidence)
            converted_pair = (converted_offset, converted_confidence)
            pairs.append(converted_pair)
        logger.debug(f"Extracted pairs: {pairs}")
        return pairs

    @staticmethod
    def aggregate_confidence(pairs):
        """
        Aggregates confidence scores for each synchronization offset.

        This function initializes a dictionary to accumulate confidence scores for each offset.
        It iterates through the provided list of (offset, confidence) pairs. For each pair, if the offset
        already exists in the dictionary, it adds the confidence score to the existing total; otherwise,
        it initializes the offset with the current confidence score.

        Args:
            pairs (list of tuples): A list where each tuple contains an offset (int) and a confidence (float).

        Returns:
            dict: A dictionary mapping each offset (int) to its aggregated confidence score (float).
        """
        confidence_map = {}
        for offset, confidence in pairs:
            if offset in confidence_map:
                confidence_map[offset] += confidence
            else:
                confidence_map[offset] = confidence
        return confidence_map

    @staticmethod
    def convert_frames_to_ms(frames, fps):
        """
        Converts a number of frames to milliseconds based on the frames per second (fps).

        This function calculates the duration per frame in milliseconds by dividing 1000 by the fps value.
        It then multiplies the number of frames by the duration per frame and returns the result as an integer.
        If the fps value is missing or invalid, it logs an error and raises a ValueError.

        Args:
            frames (int): The number of frames.
            fps (float): Frames per second.

        Returns:
            int: The total time in milliseconds corresponding to the given number of frames.

        Raises:
            ValueError: If `fps` is missing or invalid.
        """
        if fps:
            duration_per_frame_ms = 1000 / fps
        else:
            logger.error("fps value is missing. Can't convert frames to milliseconds.")
            raise ValueError("fps must be provided and can't be None.")
        return int(frames * duration_per_frame_ms)
