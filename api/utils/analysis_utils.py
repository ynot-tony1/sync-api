"""
Async log analysis utilities with hybrid async/threaded processing for SyncNet log analysis.
"""

import re
import logging
import asyncio
from typing import List, Tuple, Dict, Union
from api.utils.file_utils import FileUtils

logger: logging.Logger = logging.getLogger('analysis_logger')

class AnalysisUtils:
    """Provides static methods for asynchronous log analysis using a hybrid async/threaded approach.
    
    This class combines asynchronous I/O operations with threaded CPU-bound processing to efficiently
    analyze SyncNet log files while maintaining responsive performance.
    """

    @staticmethod
    async def analyze_syncnet_log(log_filename: str, fps: Union[int, float]) -> int:
        """Asynchronous pipeline for analyzing SyncNet log files.

        Performs the complete analysis workflow:
        1. Read log file asynchronously
        2. Extract offset/confidence pairs
        3. Aggregate confidence values
        4. Determine optimal offset
        5. Convert frames to milliseconds

        Args:
            log_filename: Path to the SyncNet log file to analyze
            fps: Video frames per second for milliseconds conversion

        Returns:
            int: Best offset in milliseconds. Returns 0 for empty files,
                no valid pairs, or processing errors.

        Raises:
            Exception: Captures and logs any unexpected errors during processing

        Example:
            >>> best_offset = await AnalysisUtils.analyze_syncnet_log('sync.log', 29.97)
            >>> print(f"Optimal sync offset: {best_offset}ms")
        """
        logger.debug(f"Analyzing SyncNet log: {log_filename}")
        
        try:
            log_content = await FileUtils.read_file(log_filename)
            if not log_content:
                logger.warning(f"Empty log file: {log_filename}")
                return 0

            pairs = await asyncio.get_running_loop().run_in_executor(
                None, 
                AnalysisUtils.extract_offset_confidence_pairs,
                log_content
            )
            
            if not pairs:
                logger.warning("No offset/confidence pairs found")
                return 0

            confidence_map = await asyncio.get_running_loop().run_in_executor(
                None,
                AnalysisUtils.aggregate_confidence,
                pairs
            )

            if not confidence_map:
                return 0

            best_offset = max(confidence_map, key=confidence_map.get)
            return AnalysisUtils.convert_frames_to_ms(best_offset, fps)
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            return 0

    @staticmethod
    def extract_offset_confidence_pairs(log_text: str) -> List[Tuple[int, float]]:
        """Extracts offset and confidence pairs from SyncNet log content.

        Uses regular expressions to find patterns matching:
        'AV offset: [number] Confidence: [decimal]'

        Args:
            log_text: Raw text content from SyncNet log file

        Returns:
            List of tuples containing (offset, confidence) pairs.
            Returns empty list if no valid matches found.

        Example:
            >>> pairs = AnalysisUtils.extract_offset_confidence_pairs(log_content)
            >>> print(pairs)
            [(-2, 5.43), (3, 7.21), ...]
        """
        pairs = []
        pattern = r'AV offset:\s*(-?\d+).*?Confidence:\s*([\d.]+)'
        matches = re.findall(pattern, log_text, re.DOTALL)
        for offset_str, confidence_str in matches:
            try:
                offset = int(offset_str)
                confidence = float(confidence_str)
                pairs.append((offset, confidence))
            except (ValueError, TypeError):
                logger.debug(f"Skipping invalid pair: {offset_str}, {confidence_str}")
                continue
        return pairs

    @staticmethod
    def aggregate_confidence(pairs: List[Tuple[int, float]]) -> Dict[int, float]:
        """Aggregates confidence values for each unique offset.

        Processes a list of (offset, confidence) pairs to create:
        - Summed confidence values per offset
        - Filters out negative confidence values

        Args:
            pairs: List of (offset, confidence) tuples

        Returns:
            Dictionary mapping offsets to total confidence.
            Returns empty dict if no valid pairs provided.

        Example:
            >>> confidence_map = AnalysisUtils.aggregate_confidence(pairs)
            >>> print(confidence_map)
            {-2: 12.84, 3: 24.56, ...}
        """
        confidence_map = {}
        for offset, confidence in pairs:
            if confidence < 0:
                logger.debug(f"Skipping negative confidence: {confidence}")
                continue
            confidence_map[offset] = confidence_map.get(offset, 0.0) + confidence
        return confidence_map

    @staticmethod
    def convert_frames_to_ms(frames: int, fps: Union[int, float]) -> int:
        """Converts frame offset to milliseconds using video FPS."""
        try:
            if fps == 0:  # Explicit check first
                return 0
                
            return int((frames * 1000) / fps)
            
        except Exception as error:
            logger.debug(f"Conversion error: {error} (frames={frames}, fps={fps})")
            return 0