"""Speech Recognition STT provider implementation."""

import speech_recognition as sr
import io
from typing import Optional
from providers.base import SpeechToTextProvider, STTConfig


class SpeechRecognitionProvider(SpeechToTextProvider):
    """STT using speech_recognition library."""

    def __init__(self, config: STTConfig):
        """
        Initialize Speech Recognition provider.

        Args:
            config: STT configuration
        """
        super().__init__(config)
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = config.energy_threshold

    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """
        Transcribe audio bytes to text using Google Speech Recognition.

        Args:
            audio_data: Raw audio bytes (16-bit PCM)
            sample_rate: Audio sample rate

        Returns:
            Transcribed text (empty string if no speech detected)
        """
        # Convert bytes to AudioData format
        # Assuming 16-bit PCM (2 bytes per sample)
        audio = sr.AudioData(audio_data, sample_rate, 2)

        try:
            # Use Google Speech Recognition (free tier)
            text = self.recognizer.recognize_google(
                audio,
                language=self.config.language
            )
            return text
        except sr.UnknownValueError:
            # Could not understand audio
            return ""
        except sr.RequestError as e:
            raise RuntimeError(f"STT service error: {e}")

    def transcribe_stream(self, audio_stream: io.BytesIO) -> str:
        """
        Transcribe from audio stream.

        Args:
            audio_stream: Audio data stream

        Returns:
            Transcribed text
        """
        audio_data = audio_stream.read()
        return self.transcribe(audio_data, self.config.sample_rate)

    def health_check(self) -> bool:
        """
        Check if service is available.

        Returns:
            True if service is available, False otherwise
        """
        try:
            # Test with short silence (1 second)
            silence = bytes(self.config.sample_rate * 2)  # 16-bit = 2 bytes per sample
            # This will fail gracefully if service is unavailable
            self.transcribe(silence)
            return True
        except Exception:
            return False

    def adjust_for_ambient_noise(
        self,
        audio_source: sr.AudioSource,
        duration: float = 1.0
    ) -> None:
        """
        Adjust recognizer sensitivity to ambient noise.

        Args:
            audio_source: Audio source to sample from
            duration: Duration to sample (seconds)
        """
        self.recognizer.adjust_for_ambient_noise(audio_source, duration=duration)
