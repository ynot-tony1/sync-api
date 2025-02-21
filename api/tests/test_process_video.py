import os
import unittest
from api.config.settings import TEST_DATA_DIR, FINAL_OUTPUT_DIR
from api.process_video import process_video

class TestRunProcessVideo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up paths to the test video files."""
        cls.test_video = os.path.join(TEST_DATA_DIR, 'example.avi')
        cls.no_audio_video = os.path.join(TEST_DATA_DIR, 'video_no_audio.avi')
        cls.nonexistent_video = os.path.join(TEST_DATA_DIR, 'nonexistent.avi')
        cls.synced_video = os.path.join(TEST_DATA_DIR, 'synced_example.avi')
        cls.final_output_dir = FINAL_OUTPUT_DIR

    def test_process_video_success(self):
        """Test processing a valid video file."""
        result = process_video(self.test_video, 'example.avi')
        self.assertIsNotNone(result, "process_video returned None for a known input")
        self.assertTrue(os.path.exists(result), f"File does not exist at {result}")
        self.assertGreater(os.path.getsize(result), 0, "Processed file is empty")
        expected_prefix = 'corrected_'
        self.assertTrue(os.path.basename(result).startswith(expected_prefix),
                        f"Processed filename doesn't start with '{expected_prefix}'")
        # Clean up the processed file.
        os.remove(result)

    def test_process_video_no_audio(self):
        """Test processing a video file without an audio stream."""
        result = process_video(self.no_audio_video, 'video_no_audio.avi')
        self.assertIsInstance(result, dict, "process_video should return a dict for a video with no audio")
        self.assertTrue(result.get("no_audio"), "process_video should indicate no audio stream in the returned dict")
        self.assertIn("message", result, "The returned dict should contain a 'message' key")

    def test_process_video_invalid_input(self):
        """Test processing a non-existent video file."""
        result = process_video(self.nonexistent_video, 'nonexistent.avi')
        self.assertIsNone(result, "process_video should return None for a non-existent input file")

    def test_process_video_already_synchronized(self):
        """Test processing a video that is already synchronized."""
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
        """Clean up any files created in the final output directory."""
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
