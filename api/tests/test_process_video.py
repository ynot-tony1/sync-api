import unittest
import os
from api.config.settings import TEST_DATA_DIR, FINAL_OUTPUT_DIR
from api.process_video import process_video

class TestRunProcessVideo(unittest.TestCase):
    # setting up paths and variables for test data to be used class wide with self
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
        # calling process_video with the known valid video file
        result = process_video(self.test_video, 'example.avi')
        self.assertIsNotNone(result, "process_video returned None for a known input")
        self.assertTrue(os.path.exists(result), f"file doesn't exist at {result}.")
        # asserting that the processed file is not empty/if its size is bigger than 0 bytes
        self.assertGreater(os.path.getsize(result), 0, "Processed file is empty.")
        # expecting that the filename will start with 'corrected_'
        expected_prefix = 'corrected_'
        self.assertTrue(os.path.basename(result).startswith(expected_prefix),
                        f"Processed filename doesn't start with '{expected_prefix}'.")
        # delete the processed file
        os.remove(result)

    def test_process_video_no_audio(self):
        """Test processing a video file without an audio stream."""
        result = process_video(self.no_audio_video, 'video_no_audio.avi')
        # asserting that process_video returns none when given a file without an audio stream
        self.assertIsNone(result, "process_video should return None for a video with no audio.")

    def test_process_video_invalid_input(self):
        """Test processing a non-existent video file."""
        result = process_video(self.nonexistent_video, 'nonexistent.avi')
         # asserting that process_video returns none when given a non-existent filepath

        self.assertIsNone(result, "process_video should return None for a non-existent input file.")

    def test_process_video_already_synchronized(self):
        """Test processing a video that's already synchronized."""
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
