import unittest
import os
from api.config.settings import TEST_DATA_DIR, FINAL_OUTPUT_DIR
from syncnet_python.run_postline import process_video

class TestRunPostline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        cls.test_video = os.path.join(TEST_DATA_DIR, 'example.avi')
        cls.no_audio_video = os.path.join(TEST_DATA_DIR, 'video_no_audio.avi')
        cls.nonexistent_video = os.path.join(TEST_DATA_DIR, 'nonexistent.avi')
        cls.synced_video = os.path.join(TEST_DATA_DIR, 'synced_example.avi') 
        cls.final_output_dir = FINAL_OUTPUT_DIR

    def test_process_video_success(self):
        """Test processing a valid video file."""
        result = process_video(self.test_video, 'example.avi')
        self.assertIsNotNone(result, "process_video returned None for a valid input.")
        self.assertTrue(os.path.exists(result), f"Processed file does not exist at {result}.")
        self.assertGreater(os.path.getsize(result), 0, "Processed file is empty.")
        expected_prefix = 'corrected_'
        self.assertTrue(os.path.basename(result).startswith(expected_prefix),
                        f"Processed filename does not start with '{expected_prefix}'.")
        os.remove(result)

    def test_process_video_no_audio(self):
        """Test processing a video file without an audio stream."""
        result = process_video(self.no_audio_video, 'video_no_audio.avi')
        self.assertIsNone(result, "process_video should return None for a video with no audio.")

    def test_process_video_invalid_input(self):
        """Test processing a non-existent video file."""
        result = process_video(self.nonexistent_video, 'nonexistent.avi')
        self.assertIsNone(result, "process_video should return None for a non-existent input file.")

    def test_process_video_already_synchronized(self):
        """Test processing a video that's already synchronized."""
        if not os.path.exists(self.synced_video):
            self.skipTest("synced_example.avi does not exist. Skipping test.")
        
        result = process_video(self.synced_video, 'synced_example.avi')
        self.assertIsNotNone(result, "process_video returned None for an already synchronized video.")
        self.assertTrue(os.path.exists(result), f"Processed file does not exist at {result}.")
        self.assertGreater(os.path.getsize(result), 0, "Processed file is empty.")
        os.remove(result)

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
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
