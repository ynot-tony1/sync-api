import os
import unittest
import asyncio

from api.config.settings import TEST_DATA_DIR, FINAL_OUTPUT_DIR
from api.process_video import process_video


class TestRunProcessVideo(unittest.TestCase):
    """Integration tests for the process_video function.

    This test suite validates the behavior of process_video in various scenarios:
    - Successful processing of a valid video file.
    - Handling of a video file with no audio stream.
    - Handling of an invalid (non-existent) video file.
    - Handling of an already synchronized video.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test resources for all tests in this class.

        Sets up the asyncio event loop, paths to test video files and the final output directory.
        """
        cls.loop = asyncio.get_event_loop()
        cls.test_video = os.path.join(TEST_DATA_DIR, 'example.avi')
        cls.no_audio_video = os.path.join(TEST_DATA_DIR, 'video_no_audio.avi')
        cls.nonexistent_video = os.path.join(TEST_DATA_DIR, 'nonexistent.avi')
        cls.synced_video = os.path.join(TEST_DATA_DIR, 'synced_example.avi')
        cls.final_output_dir = FINAL_OUTPUT_DIR

    def test_process_video_success(self):
        """Test processing of a valid video file.

        Verifies that process_video returns a dictionary with a success status and a valid final output path.
        Also asserts that the processed file exists, is non-empty, and that its filename starts with 'corrected_'.
        If processing is not successful, asserts that the error message contains "SyncNet pipeline failed".
        """
        result = self.loop.run_until_complete(process_video(self.test_video, 'example.avi'))
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
            self.assertIn("SyncNet pipeline failed", error_msg)

    def test_process_video_no_audio(self):
        """Test processing of a video file with no audio stream.

        Verifies that process_video returns a dictionary indicating an error condition for a video with no audio,
        including a 'no_audio' flag and an accompanying message.
        """
        result = self.loop.run_until_complete(process_video(self.no_audio_video, 'video_no_audio.avi'))
        self.assertIsInstance(result, dict, "process_video should return a dict for a video with no audio")
        self.assertTrue(result.get("no_audio"), "Result should indicate no audio stream")
        self.assertIn("message", result)

    def test_process_video_invalid_input(self):
        """Test processing of a non-existent video file.

        Verifies that process_video returns a dictionary indicating an error when an invalid input file is provided.
        The returned dict should have an 'error' or 'no_video' flag.
        """
        result = self.loop.run_until_complete(process_video(self.nonexistent_video, 'nonexistent.avi'))
        self.assertIsInstance(result, dict, "process_video should return a dict for an invalid input")
        self.assertTrue(result.get("error") or result.get("no_video"),
                        "Result should indicate an error for a non-existent input file")

    def test_process_video_already_synchronized(self):
        """Test processing of an already synchronized video.

        Verifies that process_video returns a dictionary indicating that the clip is already in sync.
        Expects the 'already_in_sync' flag to be True and the message to be 
        "Your clip is already in sync." If a final output file is provided, asserts that the file exists.
        """
        result = self.loop.run_until_complete(process_video(self.synced_video, 'synced_example.avi'))
        self.assertIsInstance(result, dict, "process_video should return a dict for an already synchronized video")
        if result.get("already_in_sync"):
            self.assertEqual(result.get("message"), "Your clip is already in sync.", "Expected message: 'Your clip is already in sync.'")
            final_output = result.get("final_output")
            if final_output:
                self.assertTrue(os.path.exists(final_output), "Final output file should exist for an already synchronized video")
                os.remove(final_output)
        else:
            error_msg = str(result.get("message", ""))
            self.assertIn("already in sync", error_msg, "Error message should indicate that the video is already in sync")

    @classmethod
    def tearDownClass(cls):
        """Clean up test artifacts after all tests have run.

        Iterates through the final output directory and removes any files that start with 'corrected_'.
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
