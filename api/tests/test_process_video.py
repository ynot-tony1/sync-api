"""
Module: test_process_video
Description:
    Integration tests for the process_video function.

    This test suite validates the behavior of process_video in various scenarios:
      - Successful processing of a valid video file.
      - Handling of a video file with no audio stream.
      - Handling of a non-existent (invalid) video file.
      - Handling of an already synchronized video.

    The tests use Python's built-in unittest framework and asyncio to run asynchronous code.
"""

import os
import unittest
import asyncio

from api.config.settings import TEST_DATA_DIR, FINAL_OUTPUT_DIR
from api.process_video import process_video
from api.types.props import ProcessSuccess, ProcessError


class TestRunProcessVideo(unittest.TestCase):
    """Integration tests for the process_video function.

    This test suite validates the behavior of process_video in various scenarios:
      - Successful processing of a valid video file.
      - Handling of a video file with no audio stream.
      - Handling of a non-existent (invalid) video file.
      - Handling of an already synchronized video.

    Attributes:
        loop (asyncio.AbstractEventLoop): The asyncio event loop used for running asynchronous tests.
        test_video (str): Path to a valid test video file.
        no_audio_video (str): Path to a test video file that lacks an audio stream.
        nonexistent_video (str): Path to a non-existent video file.
        synced_video (str): Path to a test video file that is already synchronized.
        final_output_dir (str): Directory path where final output files are stored.
    """

    @classmethod
    def setUpClass(cls):
        """Sets up test resources for all tests in this class.

        This method creates the asyncio event loop and defines file paths for various test cases.
        """
        cls.loop = asyncio.get_event_loop()
        cls.test_video = os.path.join(TEST_DATA_DIR, 'example.avi')
        cls.no_audio_video = os.path.join(TEST_DATA_DIR, 'video_no_audio.avi')
        cls.nonexistent_video = os.path.join(TEST_DATA_DIR, 'nonexistent.avi')
        cls.synced_video = os.path.join(TEST_DATA_DIR, 'synced_example.avi')
        cls.final_output_dir = FINAL_OUTPUT_DIR

    def test_process_video_success(self):
        """Tests processing of a valid video file.

        Verifies that process_video returns a ProcessSuccess instance with:
          - "status" equal to "success".
          - A non-empty "final_output" path whose basename starts with "corrected_".
          - A message indicating successful processing.
        Also confirms that the final output file exists and is not empty, then cleans up the file.

        Raises:
            AssertionError: If any expected condition is not met.
        """
        result = self.loop.run_until_complete(process_video(self.test_video, 'example.avi'))
        self.assertIsInstance(result, ProcessSuccess,
                              "process_video should return a ProcessSuccess instance for a valid video")
        result_dict = result.dict()
        self.assertEqual(result_dict.get("status"), "success",
                         "The status should be 'success' for a processed video")
        final_output = result_dict.get("final_output")
        self.assertIsNotNone(final_output, "final_output key must be present in the success response")
        self.assertTrue(os.path.exists(final_output), f"File does not exist at {final_output}")
        self.assertGreater(os.path.getsize(final_output), 0, "Processed file is empty")
        self.assertTrue(os.path.basename(final_output).startswith("corrected_"),
                        "Final output filename should start with 'corrected_'")
        os.remove(final_output)

    def test_process_video_no_audio(self):
        """Tests processing of a video file with no audio stream.

        Verifies that process_video returns a ProcessError instance indicating that the video has no audio stream.
        The returned error should have the "no_audio" flag set to True and include an appropriate message.

        Raises:
            AssertionError: If any expected condition is not met.
        """
        result = self.loop.run_until_complete(process_video(self.no_audio_video, 'video_no_audio.avi'))
        self.assertIsInstance(result, ProcessError,
                              "process_video should return a ProcessError instance for a video with no audio")
        result_dict = result.dict()
        self.assertTrue(result_dict.get("no_audio"), "Result should indicate no audio stream")
        self.assertIn("message", result_dict)

    def test_process_video_invalid_input(self):
        """Tests processing of a non-existent (invalid) video file.

        Verifies that process_video returns a ProcessError instance when an invalid input file is provided.
        The returned error should have the "error" flag set to True.

        Raises:
            AssertionError: If any expected condition is not met.
        """
        result = self.loop.run_until_complete(process_video(self.nonexistent_video, 'nonexistent.avi'))
        self.assertIsInstance(result, ProcessError,
                              "process_video should return a ProcessError instance for an invalid input")
        result_dict = result.dict()
        self.assertTrue(result_dict.get("error"), "Result should indicate an error for a non-existent input")

    def test_process_video_already_synchronized(self):
        """Tests processing of an already synchronized video file.

        Verifies that process_video returns a ProcessSuccess instance with:
          - "status" equal to "already_in_sync".
          - A message stating "Your clip is already in sync."
        If a final output file is provided, the test asserts that the file exists.

        Raises:
            AssertionError: If any expected condition is not met.
        """
        result = self.loop.run_until_complete(process_video(self.synced_video, 'synced_example.avi'))
        self.assertIsInstance(result, ProcessSuccess,
                              "process_video should return a ProcessSuccess instance for an already synchronized video")
        result_dict = result.dict()
        self.assertEqual(result_dict.get("status"), "already_in_sync",
                         "The status should be 'already_in_sync' when the clip is already synchronized")
        self.assertEqual(result_dict.get("message"), "Your clip is already in sync.",
                         "Expected message: 'Your clip is already in sync.'")
        final_output = result_dict.get("final_output")
        if final_output:
            self.assertTrue(os.path.exists(final_output),
                            "Final output file should exist for an already synchronized video")
            os.remove(final_output)

    @classmethod
    def tearDownClass(cls):
        """Cleans up test artifacts after all tests have run.

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
