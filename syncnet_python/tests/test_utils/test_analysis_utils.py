import unittest
import os
import tempfile
from utils.analysis_utils import AnalysisUtils

class TestAnalysisUtils(unittest.TestCase):

    # testing for valid contents
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

if __name__ == '__main__':
    unittest.main()