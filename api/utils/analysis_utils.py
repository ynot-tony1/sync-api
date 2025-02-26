"""
Utility class for analyzing SyncNet log output.
"""

import re
import logging
from typing import List, Tuple, Dict, Union

from api.utils.file_utils import FileUtils

logger: logging.Logger = logging.getLogger('analysis_logger')


class AnalysisUtils:
    @staticmethod
    def analyze_syncnet_log(log_filename: str, fps: Union[int, float]) -> int:
        """
        Analyzes the SyncNet log file and determines the synchronization offset.
        
        Args:
            log_filename (str): Path to the log file.
            fps (int | float): Frames per second.
        
        Returns:
            int: Offset in milliseconds.
        """
        log_content: Union[str, None] = FileUtils.read_log_file(log_filename)
        if not log_content:
            logger.warning(f"No content inside this log file: {log_filename}")
            return 0

        pairs: List[Tuple[int, float]] = AnalysisUtils.extract_offset_confidence_pairs(log_content)
        if not pairs:
            logger.warning("Couldn't find any pairs in the SyncNet log.")
            return 0

        offset_conf: Dict[int, float] = AnalysisUtils.aggregate_confidence(pairs)
        if not offset_conf:
            logger.warning("Couldn't add up confidence scores.")
            return 0

        best_offset: int = max(offset_conf, key=offset_conf.get)
        offset_ms: int = AnalysisUtils.convert_frames_to_ms(best_offset, fps)
        logger.info(f"The offset would be: {best_offset} frames ({offset_ms} ms)")
        return offset_ms

    @staticmethod
    def extract_offset_confidence_pairs(log_text: str) -> List[Tuple[int, float]]:
        """
        Extracts offset and confidence pairs from log text.
        
        Args:
            log_text (str): Content of the log file.
        
        Returns:
            List[Tuple[int, float]]: List of (offset, confidence) tuples.
        """
        pattern: str = r'AV offset:\s*([-+]?\d+).*?Confidence:\s*([\d.]+)'
        matches: List[Tuple[str, str]] = re.findall(pattern, log_text, re.DOTALL)
        pairs: List[Tuple[int, float]] = []
        for offset_str, conf_str in matches:
            pairs.append((int(offset_str), float(conf_str)))
        logger.debug(f"Extracted pairs: {pairs}")
        return pairs

    @staticmethod
    def aggregate_confidence(pairs: List[Tuple[int, float]]) -> Dict[int, float]:
        """
        Aggregates confidence scores for each offset.
        
        Args:
            pairs (List[Tuple[int, float]]): List of (offset, confidence) tuples.
        
        Returns:
            Dict[int, float]: Mapping of offset to total confidence.
        """
        confidence_map: Dict[int, float] = {}
        for offset, confidence in pairs:
            confidence_map[offset] = confidence_map.get(offset, 0) + confidence
        return confidence_map

    @staticmethod
    def convert_frames_to_ms(frames: int, fps: Union[int, float]) -> int:
        """
        Converts frame count to milliseconds.
        
        Args:
            frames (int): Number of frames.
            fps (int | float): Frames per second.
        
        Returns:
            int: Time in milliseconds.
        
        Raises:
            ValueError: If fps is 0 or None.
        """
        if fps:
            duration_per_frame_ms: float = 1000 / fps
        else:
            logger.error("fps value is missing. Can't convert frames to milliseconds.")
            raise ValueError("fps must be provided and cannot be None.")
        return int(frames * duration_per_frame_ms)
