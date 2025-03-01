"""
Module: test_analysis_utils
Description:
    This module contains unit tests for the AnalysisUtils class, which provides asynchronous log
    analysis utilities. The tests cover functions that aggregate confidence values and extract
    offset-confidence pairs from log content, as well as verifying the overall log analysis functionality.
    
    The tests use Python's built-in unittest framework and asyncio for running asynchronous code.
"""

import unittest
import os
import tempfile
from api.utils.analysis_utils import AnalysisUtils
import asyncio

class TestAnalysisUtils(unittest.TestCase):
    """Unit tests for the AnalysisUtils class.

    This test suite validates the following functionalities:
      - Aggregation of offset and confidence pairs into a dictionary.
      - Analysis of SyncNet log files to determine the final audio-video offset.
      - Extraction of offset and confidence pairs from raw log text.
    
    Attributes:
        loop (asyncio.AbstractEventLoop): The asyncio event loop used for running asynchronous tests.
    """

    def setUp(self):
        """Set up the test environment.

        Creates a new asyncio event loop and sets it as the current event loop. This loop is used to
        run all asynchronous test code.
        """
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def _run_async(self, coro):
        """Run an asynchronous coroutine until completion.

        Args:
            coro (coroutine): The asynchronous coroutine to run.

        Returns:
            The result of the coroutine.
        """
        return self.loop.run_until_complete(coro)

    def test_aggregate_confidence_empty_pairs(self):
        """Test aggregate_confidence with an empty list of pairs.

        Verifies that when provided an empty list, the aggregate_confidence function returns an empty dictionary.

        Expected Output:
            {} (empty dictionary)
        """
        pairs = []
        expected = {}
        result = AnalysisUtils.aggregate_confidence(pairs)
        self.assertEqual(result, expected, "Expects an empty dictionary for an empty input.")

    def test_aggregate_confidence_single_pair(self):
        """Test aggregate_confidence with a single offset and confidence pair.

        Verifies that the function returns a dictionary with the correct key and aggregated value when a
        single pair is provided.

        Expected Output:
            {10: 2.5}
        """
        pairs = [(10, 2.5)]
        expected = {10: 2.5}
        result = AnalysisUtils.aggregate_confidence(pairs)
        self.assertEqual(result, expected, "Expects a dictionary with a single pair in it.")

    def test_aggregate_confidence_zero_confidence(self):
        """Test aggregate_confidence with pairs having zero confidence.

        Verifies that the function correctly aggregates multiple pairs where all confidence values are zero.

        Expected Output:
            {1: 0.0, 2: 0.0, 3: 0.0}
        """
        pairs = [(1, 0.0), (2, 0.0), (3, 0.0)]
        expected = {1: 0.0, 2: 0.0, 3: 0.0}
        result = AnalysisUtils.aggregate_confidence(pairs)
        self.assertEqual(result, expected, "Expecting zero confidence for all of the offsets.")

    def test_aggregate_confidence_negative_confidence(self):
        """Test aggregate_confidence with pairs including negative confidence values.

        Verifies that the function skips or handles negative confidence values correctly and aggregates
        only valid (non-negative) contributions.

        Expected Output:
            {10: 2.0, 20: 3.5}
        """
        pairs = [(10, -1.0), (10, 2.0), (20, -3.5), (20, 3.5)]
        expected = {10: 2.0, 20: 3.5}
        result = AnalysisUtils.aggregate_confidence(pairs)
        self.assertEqual(result, expected)

    def test_analyze_syncnet_log_valid_log_content(self):
        """Test analyze_syncnet_log with valid log content.

        Verifies that the analyze_syncnet_log function correctly parses a valid log file, extracts
        the offset and confidence pairs, aggregates the results, and computes the correct offset in milliseconds.

        Test Log Content:
            Contains multiple lines with valid "AV offset" and "Confidence" entries.
        Expected Output:
            The computed offset in ms is -280 when the fps is 25.0.
        """
        valid_log_content = """\
        AV offset:   15
        Confidence:  0.116
        AV offset:   14
        Confidence:  0.661
        AV offset:   -7
        Confidence:  3.162
        AV offset:   15
        Confidence:  0.412
        AV offset:   -6
        Confidence:  8.271
        AV offset:   -7
        Confidence:  8.789
        AV offset:   11
        Confidence:  0.466
        AV offset:   -7
        Confidence:  7.931
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_log:
            tmp_log.write(valid_log_content)
            tmp_log_path = tmp_log.name
        try:
            log_filename = tmp_log_path
            fps = 25.0
            expected_offset_ms = -280
            result = self._run_async(AnalysisUtils.analyze_syncnet_log(log_filename, fps))
            self.assertEqual(result, expected_offset_ms, "Was expecting the correct offset in ms.")
        finally:
            os.remove(tmp_log_path)

    def test_analyze_syncnet_log_invalid_log_content(self):
        """Test analyze_syncnet_log with invalid log content.

        Verifies that when the log content contains no valid offset or confidence pairs, the function returns 0.
        It also checks that a warning is logged.

        Expected Output:
            0 (zero milliseconds offset)
        """
        invalid_log_content = """\
        AV offset:   tryh5e6d/hg
        Confidence:  rdhrtht.546
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_log:
            tmp_log.write(invalid_log_content)
            tmp_log_path = tmp_log.name
        try:
            log_filename = tmp_log_path
            fps = 30.0
            result = self._run_async(AnalysisUtils.analyze_syncnet_log(log_filename, fps))
            self.assertEqual(result, 0, "was expecting 0 ms when no valid pairs are found.")
        finally:
            os.remove(tmp_log_path)

    def test_analyze_syncnet_log_empty_log_content(self):
        """Test analyze_syncnet_log with empty log content.

        Verifies that if the log file is empty, the function returns 0 and logs a warning.

        Expected Output:
            0 (zero milliseconds offset)
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_log:
            tmp_log.write("")
            tmp_log_path = tmp_log.name
        try:
            log_filename = tmp_log_path
            fps = 25.0
            result = self._run_async(AnalysisUtils.analyze_syncnet_log(log_filename, fps))
            self.assertEqual(result, 0, "Expected 0 ms for empty log content.")
        finally:
            os.remove(tmp_log_path)

    def test_extract_offset_confidence_pairs_valid_log_content(self):
        """Test extract_offset_confidence_pairs with valid log content.

        Verifies that the function correctly extracts all offset and confidence pairs from the provided
        valid log text.

        Expected Output:
            A list of tuples containing offset and confidence values.
        """
        valid_log = """\
        AV offset:   15
        Confidence:  0.116
        AV offset:   14
        Confidence:  0.661
        AV offset:   -7
        Confidence:  3.162
        AV offset:   15
        Confidence:  0.412
        AV offset:   -6
        Confidence:  8.271
        AV offset:   -7
        Confidence:  8.789
        AV offset:   11
        Confidence:  0.466
        AV offset:   -7
        Confidence:  7.931
        """
        expected_pairs = [
            (15, 0.116),
            (14, 0.661),
            (-7, 3.162),
            (15, 0.412),
            (-6, 8.271),
            (-7, 8.789),
            (11, 0.466),
            (-7, 7.931)
        ]
        result = AnalysisUtils.extract_offset_confidence_pairs(valid_log)
        self.assertEqual(result, expected_pairs, "The function should properly extract all valid offset and confidence pairs.")

    def test_extract_offset_confidence_pairs_invalid_log_content(self):
        """Test extract_offset_confidence_pairs with invalid log content.

        Verifies that when the log text contains no valid offset and confidence pairs, the function returns
        an empty list.

        Expected Output:
            [] (empty list)
        """
        invalid_log = """\
        AV offset:   tryh5e6d/hg
        Confidence:  rdhrtht.546
        ghdtrdhfrdthfdhndhrtdjtr
        gt878dg7fdgd78ddf87hfd8h
        """
        expected_pairs = []
        result = AnalysisUtils.extract_offset_confidence_pairs(invalid_log)
        self.assertEqual(result, expected_pairs, "The function should return an empty list when no valid pairs are found.")

    def test_extract_offset_confidence_pairs_empty_log_content(self):
        """Test extract_offset_confidence_pairs with empty log content.

        Verifies that if the input log content is an empty string, the function returns an empty list.

        Expected Output:
            [] (empty list)
        """
        empty_log = ""
        expected_pairs = []
        result = AnalysisUtils.extract_offset_confidence_pairs(empty_log)
        self.assertEqual(result, expected_pairs, "The function should return an empty list for empty log content.")

if __name__ == '__main__':
    unittest.main()
