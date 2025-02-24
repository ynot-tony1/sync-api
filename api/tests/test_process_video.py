import os
import unittest
from api.config.settings import TEST_DATA_DIR, FINAL_OUTPUT_DIR
from api.process_video import process_video


class TestRunProcessVideo(unittest.TestCase):
    """Integration tests for the process_video function.

    Unit test aim to validate the behavior of process_video under various scenarios,
    including a valid video file, a video file without an audio stream, a non-existent
    file, and a video that is already synchronized. The tests assume that process_video
    returns a dictionary that contains status and error information.
    """

    @classmethod
    def setUpClass(cls):
        """Set up paths to the test video files used in all tests.

        Attributes:
            test_video (str): Path to a valid video file with audio.
            no_audio_video (str): Path to a video file that lacks an audio stream.
            nonexistent_video (str): Path to a non-existent video file.
            synced_video (str): Path to a video file that is already synchronized.
            final_output_dir (str): Directory where final output files are saved.
        """
        cls.test_video = os.path.join(TEST_DATA_DIR, 'example.avi')
        cls.no_audio_video = os.path.join(TEST_DATA_DIR, 'video_no_audio.avi')
        cls.nonexistent_video = os.path.join(TEST_DATA_DIR, 'nonexistent.avi')
        cls.synced_video = os.path.join(TEST_DATA_DIR, 'synced_example.avi')
        cls.final_output_dir = FINAL_OUTPUT_DIR

    def test_process_video_success(self):
        """Test processing a valid video file.

        Verifies that process_video returns a dictionary with a success status,
        a valid final_output file path, and a filename that starts with the expected
        prefix. The final output file is also checked for existence and non-zero size.
        
        Raises:
            AssertionError: If any of the expectations are not met.
        """
        result = process_video(self.test_video, 'example.avi')
        self.assertIsInstance(result, dict, "process_video should return a dict on success")
        self.assertEqual(result.get("status"), "success", "Status should be 'success'")
        final_output = result.get("final_output")
        self.assertIsNotNone(final_output, "final_output key must be present")
        self.assertTrue(os.path.exists(final_output), f"File does not exist at {final_output}")
        self.assertGreater(os.path.getsize(final_output), 0, "Processed file is empty")
        expected_prefix = 'corrected_'
        self.assertTrue(result.get("filename", "").startswith(expected_prefix),
                        f"Filename doesn't start with '{expected_prefix}'")
        os.remove(final_output)

    def test_process_video_no_audio(self):
        """Test processing a video file without an audio stream.

        Ensures that process_video returns a dictionary indicating an error
        specific to the absence of an audio stream. It checks for the presence of the
        'no_audio' key and a descriptive message.
        
        Raises:
            AssertionError: If the return dict does not indicate the lack of audio.
        """
        result = process_video(self.no_audio_video, 'video_no_audio.avi')
        self.assertIsInstance(result, dict, "process_video should return a dict for a video with no audio")
        self.assertTrue(result.get("no_audio"), "Result should indicate no audio stream")
        self.assertIn("message", result, "The returned dict should contain a 'message' key")
    
    def test_process_video_invalid_input(self):
        """Test processing a non-existent video file.

        Verifies that process_video returns an error dictionary when a non-existent
        file is provided. The dictionary should indicate an error (via either an 'error'
        or 'no_video' key).
        
        Raises:
            AssertionError: If the return dict does not indicate an error.
        """
        result = process_video(self.nonexistent_video, 'nonexistent.avi')
        self.assertIsInstance(result, dict, "process_video should return a dict for an invalid input")
        self.assertTrue(result.get("error") or result.get("no_video"),
                        "Result should indicate an error for a non-existent input file")
    
    def test_process_video_already_synchronized(self):
        """Test processing a video that is already synchronized.

        Checks that process_video returns a dictionary with the 'already_in_sync'
        key set to True and the expected message. If a final output is provided,
        the test confirms that the file exists.
        
        Raises:
            AssertionError: If the return dict does not indicate an already synchronized file.
        """
        result = process_video(self.synced_video, 'synced_example.avi')
        self.assertIsInstance(result, dict, "process_video should return a dict for an already synchronized video")
        self.assertTrue(result.get("already_in_sync"), "Returned dict should have 'already_in_sync' set to True")
        self.assertIn("message", result, "Returned dict should contain a 'message' key")
        expected_message = "already in sync"
        self.assertEqual(result.get("message"), expected_message,
                         f"Expected message: '{expected_message}'")
        final_output = result.get("final_output")
        if final_output:
            self.assertTrue(os.path.exists(final_output),
                            "Final output file should exist for an already synchronized video")
            os.remove(final_output)

    @classmethod
    def tearDownClass(cls):
        """Clean up any files created in the final output directory after tests complete.

        Iterates through the final output directory and removes any files that start with
        'corrected_' to avoid cluttering the test environment.
        """
        if os.path.exists(cls.final_output_dir):
            processed_files = [
                os.path.join(cls.final_output_dir, f)
                for f in os.listdir(cls.final_output_dir)
                if f.startswith('corrected_')
            ]
            for file_path in processed_files:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error removing file {file_path}: {e}")


if __name__ == '__main__':
    unittest.main()
