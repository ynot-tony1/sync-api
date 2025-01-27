import unittest
import os
from api.config.settings import TEST_DATA_DIR, FINAL_OUTPUT_DIR
from syncnet_python.run_postline import process_video

class TestRunPostline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """set up the test environment."""
        cls.test_video = os.path.join(TEST_DATA_DIR, 'example.avi')
        cls.no_audio_video = os.path.join(TEST_DATA_DIR, 'video_no_audio.avi')
        cls.nonexistent_video = os.path.join(TEST_DATA_DIR, 'nonexistent.avi')
        cls.synced_video = os.path.join(TEST_DATA_DIR, 'synced_example.avi') 
        cls.final_output_dir = FINAL_OUTPUT_DIR

    def test_process_video_success(self):
        """test processing a valid video file."""
        # processing the video and retrieve the result tuple
        result = process_video(self.test_video, 'example.avi')
        # asserting that the result is not None
        self.assertIsNotNone(result, "process_video returned None for a valid input.")
        final_output_path, total_shift_ms = result
        # asserting that the output file exists
        self.assertTrue(os.path.exists(final_output_path), f"Processed file does not exist at {final_output_path}.")
        # asserting that the output file is not empty
        self.assertGreater(os.path.getsize(final_output_path), 0, "Processed file is empty.")
        # asserting that the filename starts with the expected prefix
        self.assertTrue(os.path.basename(final_output_path).startswith('corrected_'),
                        f"Processed filename does not start with '{'corrected_'}'.")
        # defining the expected total  from manually tested data in ms
        expected_shift_ms = 120
        # asserting that the total_shift_ms matches the expected value
        self.assertEqual(total_shift_ms, expected_shift_ms,
                         f"Expected total_shift_ms to be {expected_shift_ms}, got {total_shift_ms}.")
        os.remove(final_output_path)
    # testing with a file with no audio stream
    def test_process_video_no_audio(self):
        """test processing a video file without an audio stream."""
        result = process_video(self.no_audio_video, 'video_no_audio.avi')
        self.assertIsNone(result, "process_video should return None for a video with no audio.")

    # testing with a non existent file
    def test_process_video_invalid_input(self):
        """test processing a non-existent video file."""
        result = process_video(self.nonexistent_video, 'nonexistent.avi')
        self.assertIsNone(result, "process_video should return None for a non-existent input file.")

    # testing with a file which has been manually synchronised already
    def test_process_video_already_synchronized(self):
        """test processing a video that's already synchronized."""
        result = process_video(self.synced_video, 'synced_example.avi')
        self.assertIsNotNone(result, "process_video returned None for an already synchronized video.")
        final_output_path, total_shift_ms = result
        self.assertTrue(os.path.exists(final_output_path), f"Processed file does not exist at {final_output_path}.")
        self.assertGreater(os.path.getsize(final_output_path), 0, "Processed file is empty.")
        expected_shift_ms = 0
        self.assertEqual(total_shift_ms, expected_shift_ms,
                         f"Expected total_shift_ms to be {expected_shift_ms}, got {total_shift_ms}.")
        os.remove(final_output_path)

if __name__ == '__main__':
    unittest.main()
