"""Tests for the FFmpegUtils asynchronous utility functions.

This module tests various functions provided by FFmpegUtils including:
  - Retrieving audio properties from a video file.
  - Retrieving video properties from a video file.
  - Shifting audio in a video file.
  - Applying cumulative audio shifts.
  
These tests use an asyncio event loop to run asynchronous methods and temporary directories
to simulate file operations.
"""

import os
import shutil
import tempfile
import asyncio
import unittest

from api.config.settings import TEST_DATA_DIR, FINAL_OUTPUT_DIR
from api.utils.ffmpeg_utils import FFmpegUtils


class TestFFmpegUtils(unittest.TestCase):
    """Test suite for FFmpegUtils methods."""

    @classmethod
    def setUpClass(cls):
        """Set up the event loop and test file paths used for all tests.

        Attributes:
            loop (asyncio.AbstractEventLoop): The asyncio event loop for test execution.
            example_video (str): Path to a valid video file with audio.
            synced_video (str): Path to a video file that is already synchronized.
            no_audio_video (str): Path to a video file that lacks an audio stream.
            no_video_video (str): Path to a video file that has no video stream.
        """
        cls.loop = asyncio.get_event_loop()
        cls.example_video = os.path.join(TEST_DATA_DIR, 'example.avi')
        cls.synced_video = os.path.join(TEST_DATA_DIR, 'synced_example.avi')
        cls.no_audio_video = os.path.join(TEST_DATA_DIR, 'video_no_audio.avi')
        cls.no_video_video = os.path.join(TEST_DATA_DIR, 'video_no_video_stream.avi')

    def test_get_audio_properties_success(self):
        """Test that get_audio_properties returns a valid dictionary for a video with audio.

        The test runs FFmpegUtils.get_audio_properties on a valid video file and asserts that
        the returned dictionary contains the keys: 'sample_rate', 'channels', and 'codec_name'.
        """
        props = self.loop.run_until_complete(
            FFmpegUtils.get_audio_properties(self.example_video)
        )
        self.assertIsInstance(props, dict, "Audio properties should be a dict for a valid video.")
        self.assertIn('sample_rate', props)
        self.assertIn('channels', props)
        self.assertIn('codec_name', props)

    def test_get_audio_properties_no_audio(self):
        """Test that get_audio_properties returns None for a video with no audio stream.

        The test runs FFmpegUtils.get_audio_properties on a video file known to have no audio,
        and asserts that the returned value is None.
        """
        props = self.loop.run_until_complete(
            FFmpegUtils.get_audio_properties(self.no_audio_video)
        )
        self.assertIsNone(props, "Audio properties should be None for a video without an audio stream.")

    def test_get_video_properties_success(self):
        """Test that get_video_properties returns a valid dictionary for a video with a video stream.

        The test runs FFmpegUtils.get_video_properties on a valid video file and asserts that
        the returned dictionary contains the keys: 'codec_name' and 'avg_frame_rate'.
        """
        props = self.loop.run_until_complete(
            FFmpegUtils.get_video_properties(self.example_video)
        )
        self.assertIsInstance(props, dict, "Video properties should be a dict for a valid video.")
        self.assertIn('codec_name', props)
        self.assertIn('avg_frame_rate', props)

    def test_shift_audio_success(self):
        """Test that shift_audio creates a non-empty output file for a valid video input.

        The test applies a positive audio shift to the example video and asserts that:
          - The output file exists.
          - The output file size is greater than zero.
        """
        temp_dir = tempfile.mkdtemp()
        output_file = os.path.join(temp_dir, "shifted_example.avi")
        try:
            self.loop.run_until_complete(
                FFmpegUtils.shift_audio(self.example_video, output_file, 100)
            )
            self.assertTrue(os.path.exists(output_file), "Output file should be created by shift_audio.")
            self.assertGreater(os.path.getsize(output_file), 0, "Shifted file should not be empty.")
        finally:
            shutil.rmtree(temp_dir)

    def test_shift_audio_nonexistent_file(self):
        """Test that shift_audio does not create an output file when the input file does not exist.

        The test attempts to shift audio for a non-existent file and asserts that no output
        file is created.
        """
        nonexistent_file = os.path.join(TEST_DATA_DIR, "nonexistent.avi")
        temp_dir = tempfile.mkdtemp()
        output_file = os.path.join(temp_dir, "output.avi")
        try:
            self.loop.run_until_complete(
                FFmpegUtils.shift_audio(nonexistent_file, output_file, 100)
            )
            self.assertFalse(os.path.exists(output_file), "Output file should not be created for a nonexistent input.")
        finally:
            shutil.rmtree(temp_dir)

    def test_apply_cumulative_shift_success(self):
        """Test that apply_cumulative_shift creates a valid final output file.

        The test runs FFmpegUtils.apply_cumulative_shift with a valid input video file and a specified
        shift value. It asserts that the final output file exists and is non-empty.
        After the test, any created temporary files are removed.
        """
        temp_dir = tempfile.mkdtemp()
        final_output = os.path.join(temp_dir, "final_shifted_example.avi")
        try:
            self.loop.run_until_complete(
                FFmpegUtils.apply_cumulative_shift(self.example_video, final_output, 150)
            )
            self.assertTrue(os.path.exists(final_output), "Final output file should exist after cumulative shift.")
            self.assertGreater(os.path.getsize(final_output), 0, "Final output file should not be empty.")
        finally:
            if os.path.exists(final_output):
                os.remove(final_output)
            shutil.rmtree(temp_dir)
            temp_copy = os.path.join(FINAL_OUTPUT_DIR, os.path.basename(self.example_video))
            if os.path.exists(temp_copy):
                os.remove(temp_copy)


if __name__ == '__main__':
    unittest.main()
