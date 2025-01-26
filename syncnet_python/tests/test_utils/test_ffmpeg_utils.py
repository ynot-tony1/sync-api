import unittest
import os
from utils.ffmpeg_utils import FFmpegUtils 
from settings import TEST_DATA_DIR
import logging

# configure logging to display debug information during tests
logging.basicConfig(level=logging.DEBUG)

class TestFFmpegUtils(unittest.TestCase):

    # ------------------ set up class for unit tests ------------------ #
    # setting up paths and variables for test data to be used class wide with self.
    @classmethod
    def setUpClass(cls):
        """
        Setting up class-wide resources.
        """
        # paths to test files
        cls.valid_video = os.path.join(TEST_DATA_DIR, 'example.avi')
        cls.video_no_audio = os.path.join(TEST_DATA_DIR, 'video_no_audio.avi')
        cls.video_no_video_stream = os.path.join(TEST_DATA_DIR, 'video_no_video_stream.avi')
        cls.invalid_file = os.path.join(TEST_DATA_DIR, 'invalid_file_corrupted_headers.avi')
        cls.nonexistent_file = os.path.join(TEST_DATA_DIR, 'nonexistent.avi')  

        # expected audio properties for the valid video
        cls.expected_audio_props = {
            'sample_rate': '16000',
            'channels': 1,
            'codec_name': 'pcm_s16le'
        }

        

    # ------------------ get_audio_properties unit tests ------------------ #

    # testing get_audio_properties with the test file
    def test_get_audio_properties_success(self):
        """
        Testing that FFmpegUtils.get_audio_properties returns correct properties for a valid audio file.
        """
        # calling the method to get audio properties
        audio_props = FFmpegUtils.get_audio_properties(self.valid_video)
        # checking sample rate
        self.assertEqual(
            audio_props['sample_rate'], 
            self.expected_audio_props['sample_rate'],
            f"Expected 'sample_rate' to be {self.expected_audio_props['sample_rate']}, got {audio_props['sample_rate']}."
        )
        # checking 'channels'
        self.assertEqual(
            audio_props['channels'], 
            self.expected_audio_props['channels'],
            f"Expected 'channels' to be {self.expected_audio_props['channels']}, got {audio_props['channels']}."
        )
        # checking codec
        self.assertEqual(
            audio_props['codec_name'], 
            self.expected_audio_props['codec_name'],
            f"Expected 'codec_name' to be {self.expected_audio_props['codec_name']}, got {audio_props['codec_name']}."
        )

    # testing get audio props function with no audio stream
    def test_get_audio_properties_no_audio_stream(self):
        """
        Testing that FFmpegUtils.get_audio_properties returns None for a file without an audio stream.
        """
        # path to the file with no audio stream
        video_no_audio = os.path.join(TEST_DATA_DIR, 'video_no_audio.avi')

        # calling the method
        audio_props = FFmpegUtils.get_audio_properties(video_no_audio)

        # asserting that audio_props is None
        self.assertIsNone(audio_props, "Audio properties should be None for a video without an audio stream.")


     # testing get audio props function with non existent file 
    def test_get_audio_properties_nonexistent_file(self):
        """
        Testing that FFmpegUtils.get_audio_properties returns None for a non-existent file.
        """
        # path to a non-existent file
        nonexistent_file = self.nonexistent_file

        # calling the function
        audio_props = FFmpegUtils.get_audio_properties(nonexistent_file)

        # asserting that audio_props is None
        self.assertIsNone(audio_props, "Audio properties should be None for a non-existent file.")




    # ------------------ get_video_fps unit tests ------------------ #     


    # testing the get video fps function with a valid video file
    def test_get_video_fps_success(self):
        """
        Testing that FFmpegUtils.get_video_fps returns the correct FPS for a valid video file.
        """
        # expected FPS for the valid video (ensure this matches your actual file)
        expected_fps = 25.0

        # call the method to get fps
        fps = FFmpegUtils.get_video_fps(self.valid_video)

        # assert that FPS is a float and matches the expected value
        self.assertIsInstance(fps, float, "fps should be a float.")
        self.assertAlmostEqual(fps, expected_fps, places=2, msg=f"expected the fps to be {expected_fps}, and got {fps}.")


    # testing the get fps function with a test file with no video stream
    def test_get_video_fps_no_video_stream(self):
        """
        Testing that FFmpegUtils.get_video_fps returns None for a file without any video streams.
        """
        # path to test file with no video stream        
        video_no_video_stream = self.video_no_video_stream
        fps = FFmpegUtils.get_video_fps(video_no_video_stream)

        # asserting that fps is None
        self.assertIsNone(fps, "FPS should be None for a file without any video streams.")


    # testing the get video fps function with a non existent file   
    def test_get_video_fps_nonexistent_file(self):
        """
        Testing that FFmpegUtils.get_video_fps returns None for a non-existent file.
        """
        # path to a non-existent file
        nonexistent_file = self.nonexistent_file

        # calling the method
        fps = FFmpegUtils.get_video_fps(nonexistent_file)

        # asserting that fps is None
        self.assertIsNone(fps, "FPS should be None for a non-existent file.")

    


if __name__ == '__main__':
    unittest.main()

