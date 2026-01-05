"""Abstract base class for Speech-to-Text providers."""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
import io


@dataclass
class STTConfig:
    """Configuration for STT providers."""
    language: str = "en-US"
    model: Optional[str] = None
    api_key: Optional[str] = None
    sample_rate: int = 16000
    energy_threshold: int = 4000  # For voice activity detection


class SpeechToTextProvider(ABC):
    """Abstract base class for STT providers."""

    def __init__(self, config: STTConfig):
        """
        Initialize STT provider.

        Args:
            config: STT configuration
        """
        self.config = config

    @abstractmethod
    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """
        Transcribe audio bytes to text.

        Args:
            audio_data: Raw audio bytes
            sample_rate: Audio sample rate

        Returns:
            Transcribed text
        """
        pass

    @abstractmethod
    def transcribe_stream(self, audio_stream: io.BytesIO) -> str:
        """
        Transcribe audio stream to text.

        Args:
            audio_stream: Audio data stream

        Returns:
            Transcribed text
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if provider is available.

        Returns:
            True if provider is available, False otherwise
        """
        pass
