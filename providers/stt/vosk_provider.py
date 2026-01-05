"""Vosk STT provider implementation."""

import io
import json
import wave
import logging
from pathlib import Path
from typing import Optional, Callable, Iterator
from vosk import Model, KaldiRecognizer
from providers.base import SpeechToTextProvider, STTConfig


class VoskProvider(SpeechToTextProvider):
    """STT using Vosk for local transcription."""

    def __init__(self, config: STTConfig):
        """
        Initialize Vosk provider.

        Args:
            config: STT configuration
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

        # Model path from config or default
        model_path = config.model or "models/vosk-model-small-en-us-0.15"

        # Expand to absolute path
        if not Path(model_path).is_absolute():
            # Relative to project root
            model_path = Path(__file__).parent.parent.parent / model_path

        # Load Vosk model
        if not Path(model_path).exists():
            raise RuntimeError(f"Vosk model not found at: {model_path}")

        self.model = Model(str(model_path))
        self.sample_rate = config.sample_rate

        # Create reusable recognizer (optimization: reuse instead of recreating)
        self.recognizer = KaldiRecognizer(self.model, config.sample_rate)
        self.recognizer.SetWords(False)  # Set once, don't need word-level timestamps

    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """
        Transcribe audio bytes to text using Vosk.

        Args:
            audio_data: Raw audio bytes (16-bit PCM)
            sample_rate: Audio sample rate

        Returns:
            Transcribed text (empty string if no speech detected)
        """
        try:
            # Reset recognizer state for new audio (optimization: reuse recognizer)
            self.recognizer.Reset()

            # Process audio data
            self.recognizer.AcceptWaveform(audio_data)

            # Get final result
            result = json.loads(self.recognizer.FinalResult())
            text = result.get('text', '')

            return text.strip()

        except Exception as e:
            raise RuntimeError(f"Vosk transcription error: {e}")

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

    def transcribe_streaming(
        self,
        audio_chunks: Iterator[bytes],
        sample_rate: int = 16000,
        callback: Optional[Callable[[str, bool], None]] = None
    ) -> str:
        """
        Transcribe audio with streaming partial results (optimization: real-time feedback).

        Args:
            audio_chunks: Iterator of audio byte chunks
            sample_rate: Audio sample rate
            callback: Optional callback(text, is_final) called on results

        Returns:
            Final complete transcription
        """
        try:
            self.recognizer.Reset()
            full_transcript = ""
            chunk_count = 0
            partial_count = 0
            final_count = 0

            for chunk in audio_chunks:
                chunk_count += 1
                if self.recognizer.AcceptWaveform(chunk):
                    # Complete phrase recognized
                    final_count += 1
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').strip()

                    if text:
                        self.logger.debug(f"Final result #{final_count} after {chunk_count} chunks: '{text}'")
                        full_transcript = text
                        if callback:
                            callback(text, is_final=True)
                else:
                    # Partial result (word in progress)
                    partial = json.loads(self.recognizer.PartialResult())
                    partial_text = partial.get('partial', '').strip()

                    if partial_text:
                        partial_count += 1
                        if partial_count % 5 == 0:  # Log every 5th partial
                            self.logger.debug(f"Partial #{partial_count}: '{partial_text}'")
                        if callback:
                            callback(partial_text, is_final=False)

            # Get final result
            final_result = json.loads(self.recognizer.FinalResult())
            final_text = final_result.get('text', '').strip()

            if final_text:
                full_transcript = final_text
                if callback:
                    callback(final_text, is_final=True)

            return full_transcript

        except Exception as e:
            raise RuntimeError(f"Vosk streaming transcription error: {e}")

    def health_check(self) -> bool:
        """
        Check if Vosk is available.

        Returns:
            True if model is loaded, False otherwise
        """
        try:
            # Check if model is loaded
            if not hasattr(self, 'model') or self.model is None:
                return False

            # Test with short silence using reusable recognizer
            silence = bytes(self.config.sample_rate * 2)  # 1 second of silence
            self.recognizer.Reset()
            self.recognizer.AcceptWaveform(silence)
            self.recognizer.FinalResult()

            return True
        except Exception:
            return False
