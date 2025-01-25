import unittest
import os
import tempfile
from utils.analysis_utils import AnalysisUtils

class TestAnalysisUtils(unittest.TestCase):

    # ------------------ aggregate_confidence unit tests ------------------ #

    # testing aggregate_confidence with empty pairs
    def test_aggregate_confidence_empty_pairs(self):
        """
        Testing the aggregate_confidence with an empty list of pairs.
        Expecting an empty dictionary as a result.
        """
        pairs = []
        expected = {}
        result = AnalysisUtils.aggregate_confidence(pairs)
        self.assertEqual(result, expected, "Expects an empty dictionary for an empty input.")
        
	# testing aggregate_confidence with a single pair
    def test_aggregate_confidence_single_pair(self):
        """
        Testing the aggregate_confidence function with a single offset and confidence pair.
        """
        pairs = [(10, 2.5)]
        expected = {10: 2.5}
        result = AnalysisUtils.aggregate_confidence(pairs)
        self.assertEqual(result, expected, "Expected a dictionary with a single pair.")
    # testing aggregate_confidence with a zero confidence
    def test_aggregate_confidence_zero_confidence(self):
        """
        Test aggregate_confidence with pairs that have zero confidence.
        """
        pairs = [(1, 0.0), (2, 0.0), (3, 0.0)]
        expected = {1: 0.0, 2: 0.0, 3: 0.0}
        result = AnalysisUtils.aggregate_confidence(pairs)
        self.assertEqual(result, expected, "Expected zero confidence for all offsets.")
    # testing aggregate_confidence with negative confidence
    def test_aggregate_confidence_negative_confidence(self):
        """
        Test aggregate_confidence with pairs that have negative confidence values.
        """
        pairs = [(10, -1.0), (10, 2.0), (20, -3.5), (20, 3.5)]
        expected = {10: 1.0, 20: 0.0}  # (-1.0 + 2.0) = 1.0 and (-3.5 + 3.5) = 0.0
        result = AnalysisUtils.aggregate_confidence(pairs)
        self.assertEqual(result, expected, "Expected correct aggregation with negative confidences.")


    # ------------------ analyze_syncnet_log unit tests --------------------- #

    # testing analyze_syncnet_log with valid contents
    def test_analyze_syncnet_log_valid_log_content(self):
        """
        Testing analyze_syncnet_log with valid log contents.
        Expecting the function to return the correct offset in ms.
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
            result = AnalysisUtils.analyze_syncnet_log(log_filename, fps)
            self.assertEqual(result, expected_offset_ms, "Was expecting the correct offset in ms.")
        finally:
            os.remove(tmp_log_path)
    # testing analyze_syncnet_log with invalid contents
    def test_analyze_syncnet_log_invalid_log_content(self):
        """
        Testing analyze_syncnet_log with log content that has no valid offset and confidence pairs.
        Expecting the function to return 0 and to log a warning.
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
            result = AnalysisUtils.analyze_syncnet_log(log_filename, fps)
            self.assertEqual(result, 0, "was expecting 0 ms when no valid pairs are found.")
        finally:
            os.remove(tmp_log_path)
    # testing analyze_syncnet_log with empty log content
    def test_analyze_syncnet_log_empty_log_content(self):
        """
        Testing analyze_syncnet_log with no contents.
        Expecting it to return 0 and a warning log.
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_log:
            tmp_log.write("")
            tmp_log_path = tmp_log.name
        try:
            log_filename = tmp_log_path
            fps = 25.0
            result = AnalysisUtils.analyze_syncnet_log(log_filename, fps)
            self.assertEqual(result, 0, "Expected 0 ms for empty log content.")
        finally:
            os.remove(tmp_log_path)

            

    
    
if __name__ == '__main__':
    unittest.main()