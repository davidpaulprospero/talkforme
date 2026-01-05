"""Abstract base class for audio capture providers."""

from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class AudioConfig:
    """Configuration for audio providers."""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    format: str = "paInt16"  # PyAudio format
    input_device_index: Optional[int] = None


class AudioProvider(ABC):
    """Abstract base class for audio capture."""

    def __init__(self, config: AudioConfig):
        """
        Initialize audio provider.

        Args:
            config: Audio configuration
        """
        self.config = config
        self._is_recording = False

    @abstractmethod
    def start_recording(self) -> None:
        """Start continuous audio recording."""
        pass

    @abstractmethod
    def stop_recording(self) -> None:
        """Stop audio recording."""
        pass

    @abstractmethod
    def get_audio_chunk(self) -> bytes:
        """
        Get latest audio chunk.

        Returns:
            Audio chunk as bytes
        """
        pass

    @abstractmethod
    def record_for_duration(self, duration_seconds: float) -> bytes:
        """
        Record audio for specific duration.

        Args:
            duration_seconds: Duration to record

        Returns:
            Complete audio data as bytes
        """
        pass

    @abstractmethod
    def list_devices(self) -> List[dict]:
        """
        List available audio input devices.

        Returns:
            List of device information dictionaries
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if audio provider is available and functional.

        Returns:
            True if provider is available, False otherwise
        """
        pass

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._is_recording
