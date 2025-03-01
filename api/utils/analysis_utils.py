import re
import logging
from typing import List, Tuple, Dict, Union
from api.utils.file_utils import FileUtils

logger: logging.Logger = logging.getLogger('analysis_logger')

class AnalysisUtils:
    @staticmethod
    def analyze_syncnet_log(log_filename: str, fps: Union[int, float]) -> int:
        logger.debug(
            f"[ENTER] analyze_syncnet_log -> log_filename='{log_filename}', fps={fps}"
        )
        log_content: Union[str, None] = FileUtils.read_file(log_filename)
        if not log_content:
            logger.warning(f"[analyze_syncnet_log] No content in log file -> {log_filename}")
            logger.debug("[EXIT] analyze_syncnet_log -> returning offset=0")
            return 0

        pairs: List[Tuple[int, float]] = AnalysisUtils.extract_offset_confidence_pairs(log_content)
        logger.debug(f"[analyze_syncnet_log] offset/conf pairs -> {pairs}")
        if not pairs:
            logger.warning("[analyze_syncnet_log] No offset/confidence pairs found -> returning 0")
            logger.debug("[EXIT] analyze_syncnet_log -> returning offset=0")
            return 0

        offset_conf: Dict[int, float] = AnalysisUtils.aggregate_confidence(pairs)
        logger.debug(f"[analyze_syncnet_log] aggregated confidence -> {offset_conf}")
        if not offset_conf:
            logger.warning("[analyze_syncnet_log] No offset_conf -> returning 0")
            logger.debug("[EXIT] analyze_syncnet_log -> returning offset=0")
            return 0

        best_offset: int = max(offset_conf, key=offset_conf.get)
        offset_ms: int = AnalysisUtils.convert_frames_to_ms(best_offset, fps)
        logger.info(
            f"[analyze_syncnet_log] Best offset -> {best_offset} frames => {offset_ms} ms"
        )

        logger.debug(f"[EXIT] analyze_syncnet_log -> {offset_ms}")
        return offset_ms

    @staticmethod
    def extract_offset_confidence_pairs(log_text: str) -> List[Tuple[int, float]]:
        logger.debug("[ENTER] extract_offset_confidence_pairs")
        pattern: str = r'AV offset:\s*([-+]?\d+).*?Confidence:\s*([\d.]+)'
        matches = re.findall(pattern, log_text, re.DOTALL)
        pairs: List[Tuple[int, float]] = [
            (int(offset_str), float(conf_str)) for offset_str, conf_str in matches
        ]
        logger.debug(f"[extract_offset_confidence_pairs] found pairs={pairs}")
        logger.debug("[EXIT] extract_offset_confidence_pairs")
        return pairs

    @staticmethod
    def aggregate_confidence(pairs: List[Tuple[int, float]]) -> Dict[int, float]:
        logger.debug(f"[ENTER] aggregate_confidence -> pairs={pairs}")
        confidence_map: Dict[int, float] = {}
        for offset, confidence in pairs:
            confidence_map[offset] = confidence_map.get(offset, 0) + confidence
        logger.debug(f"[EXIT] aggregate_confidence -> {confidence_map}")
        return confidence_map

    @staticmethod
    def convert_frames_to_ms(frames: int, fps: Union[int, float]) -> int:
        logger.debug(f"[ENTER] convert_frames_to_ms -> frames={frames}, fps={fps}")
        if not fps:
            logger.error("[convert_frames_to_ms] fps is zero/None -> can't convert!")
            raise ValueError("fps must be provided and cannot be None.")
        ms = int((1000 / fps) * frames)
        logger.debug(f"[EXIT] convert_frames_to_ms -> offset_ms={ms}")
        return ms