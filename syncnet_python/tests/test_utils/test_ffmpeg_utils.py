import unittest
import os
from utils.ffmpeg_utils import FFmpegUtils 
from settings import TEST_DATA_DIR


class TestFFmpegUtils(unittest.TestCase):

    # class wide resources with manually verified test data 
    @classmethod
    def setUpClass(cls):
        """
        Setting up some class wide resources 
        """
        # path to the test_data directory
        cls.input_file = os.path.join(TEST_DATA_DIR , 'example.avi')
        # expected audio properties are based on the known outputs from a manual ffprobe of example.avi
        cls.expected_audio_props = {
            'sample_rate': '16000',        # expected sample rate
            'channels': 1,                 # example number of channels
            'codec_name': 'pcm_s16le'      # example codec
        }

    # testing get_audio_properties with the test file
    def test_get_audio_properties_success(self):
        """
        Testing that FFmpegUtils.get_audio_properties returns the correct properties for a valid audio file.
        """
        # calling the method to get audio properties
        audio_props = FFmpegUtils.get_audio_properties(self.input_file)
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

    def test_get_audio_properties_no_audio_stream(self):
        """
        Testing that FFmpegUtils.get_audio_properties returns None for a file without an audio stream.
        """
        # path to the file with no audio stream
        video_no_audio = os.path.join(TEST_DATA_DIR, 'video_no_audio.avi')
    
        # calling the method
        audio_props = FFmpegUtils.get_audio_properties(video_no_audio)
        
        # asserting that audio_props is None
        self.assertIsNone(audio_props, "Audio properties should be None for a video without any audio stream inside it.")

if __name__ == '__main__':
    unittest.main()

