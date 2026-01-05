"""Faster-Whisper STT provider implementation."""

import io
import numpy as np
from typing import Optional
from faster_whisper import WhisperModel
from providers.base import SpeechToTextProvider, STTConfig


class FasterWhisperProvider(SpeechToTextProvider):
    """STT using Faster-Whisper for local transcription."""

    def __init__(self, config: STTConfig):
        """
        Initialize Faster-Whisper provider.

        Args:
            config: STT configuration
        """
        super().__init__(config)

        # Model size: tiny, base, small, medium, large-v2, large-v3
        model_size = config.model or "base"

        # Device: "cpu", "cuda", "auto"
        device = "cpu"  # Change to "cuda" if you have NVIDIA GPU

        # Compute type: "int8", "float16", "float32"
        # int8 is fastest, float32 is most accurate
        compute_type = "int8"

        # Load model (downloads on first use, then cached)
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )

        # Extract language code (en-US -> en)
        self.language = config.language.split('-')[0] if config.language else "en"

        # Pre-cache VAD parameters (optimization: avoid dict creation on every call)
        self.vad_params = {
            'min_silence_duration_ms': 500,  # Minimum silence to split segments
            'threshold': 0.5  # VAD threshold (0-1)
        }

    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """
        Transcribe audio bytes to text using Faster-Whisper.

        Args:
            audio_data: Raw audio bytes (16-bit PCM)
            sample_rate: Audio sample rate

        Returns:
            Transcribed text (empty string if no speech detected)
        """
        try:
            # Convert bytes to numpy array
            # Assuming 16-bit PCM (2 bytes per sample)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

            # Convert to float32 and normalize to [-1, 1]
            audio_float = audio_array.astype(np.float32) / 32768.0

            # Transcribe with Faster-Whisper (optimization: use cached VAD params)
            segments, info = self.model.transcribe(
                audio_float,
                language=self.language,
                beam_size=1,  # Lower beam size = faster (1-5, default 5)
                vad_filter=True,  # Voice activity detection
                vad_parameters=self.vad_params  # Use pre-cached parameters
            )

            # Combine all segments into single text
            text = " ".join([segment.text.strip() for segment in segments])

            return text.strip()

        except Exception as e:
            raise RuntimeError(f"Faster-Whisper transcription error: {e}")

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
        Check if Faster-Whisper is available.

        Returns:
            True if model is loaded, False otherwise
        """
        try:
            # Test with short silence (0.5 seconds of zeros)
            silence = np.zeros(self.config.sample_rate // 2, dtype=np.float32)
            segments, _ = self.model.transcribe(silence, language=self.language)
            # Just check if we can run transcription without error
            list(segments)  # Consume generator
            return True
        except Exception:
            return False
