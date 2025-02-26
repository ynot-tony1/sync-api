import os
import unittest
from api.config.type_settings import TEST_DATA_DIR, FINAL_OUTPUT_DIR
from api.process_video import process_video


class TestRunProcessVideo(unittest.TestCase):
    """Integration tests for the process_video function.

    These tests validate the behavior of process_video under various scenarios,
    including processing a valid video file, a video file without an audio stream,
    a non-existent file, and a video that is already synchronized.
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
        a valid final_output file path, and that the final output file exists and is non-empty.
        If an error occurs, the error message (converted to a string) must indicate a pipeline failure.
        
        Raises:
            AssertionError: If any expected outcome is not met.
        """
        result = process_video(self.test_video, 'example.avi')
        self.assertIsInstance(result, dict, "process_video should return a dict")
        if result.get("status") == "success":
            final_output = result.get("final_output")
            self.assertIsNotNone(final_output, "final_output key must be present")
            self.assertTrue(os.path.exists(final_output), f"File does not exist at {final_output}")
            self.assertGreater(os.path.getsize(final_output), 0, "Processed file is empty")
            self.assertTrue(os.path.basename(final_output).startswith("corrected_"),
                            "Final output filename should start with 'corrected_'")
            os.remove(final_output)
        else:
            error_msg = str(result.get("message", ""))
            self.assertIn("SyncNet pipeline failed", error_msg,
                          "Error message should indicate pipeline failure")

    def test_process_video_no_audio(self):
        """Test processing a video file without an audio stream.

        Ensures that process_video returns a dictionary indicating an error
        specific to the absence of an audio stream.
        
        Raises:
            AssertionError: If the returned dict does not indicate the lack of audio.
        """
        result = process_video(self.no_audio_video, 'video_no_audio.avi')
        self.assertIsInstance(result, dict, "process_video should return a dict for a video with no audio")
        self.assertTrue(result.get("no_audio"), "Result should indicate no audio stream")
        self.assertIn("message", result, "The returned dict should contain a 'message' key")
    
    def test_process_video_invalid_input(self):
        """Test processing a non-existent video file.

        Verifies that process_video returns an error dictionary when a non-existent file is provided.
        
        Raises:
            AssertionError: If the returned dict does not indicate an error.
        """
        result = process_video(self.nonexistent_video, 'nonexistent.avi')
        self.assertIsInstance(result, dict, "process_video should return a dict for an invalid input")
        self.assertTrue(result.get("error") or result.get("no_video"),
                        "Result should indicate an error for a non-existent input file")
    
    def test_process_video_already_synchronized(self):
        """Test processing a video that is already synchronized.

        Checks that process_video returns a dictionary with the 'already_in_sync'
        key set to True and the expected message if the video is already synchronized.
        If an error occurs, the error message (converted to a string) must indicate a pipeline failure.
        
        Raises:
            AssertionError: If the returned dict does not indicate either an already synchronized state or a pipeline error.
        """
        result = process_video(self.synced_video, 'synced_example.avi')
        self.assertIsInstance(result, dict, "process_video should return a dict for an already synchronized video")
        if result.get("already_in_sync"):
            self.assertEqual(result.get("message"), "already in sync", "Expected message: 'already in sync'")
            final_output = result.get("final_output")
            if final_output:
                self.assertTrue(os.path.exists(final_output),
                                "Final output file should exist for an already synchronized video")
                os.remove(final_output)
        else:
            error_msg = str(result.get("message", ""))
            self.assertIn("SyncNet pipeline failed", error_msg,
                          "Error message should indicate pipeline failure")

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
