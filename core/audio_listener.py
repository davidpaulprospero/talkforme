"""Audio listener for continuous speech detection and transcription."""

import threading
import time
import struct
import logging
import numpy as np
import concurrent.futures
from typing import Optional, Callable, Dict, Any

from providers.base import AudioProvider, SpeechToTextProvider


class AudioListener:
    """Orchestrates continuous audio recording and transcription."""

    def __init__(
        self,
        audio_provider: AudioProvider,
        stt_provider: SpeechToTextProvider,
        config: Dict[str, Any]
    ):
        """
        Initialize audio listener.

        Args:
            audio_provider: Audio capture provider
            stt_provider: Speech-to-text provider
            config: Configuration dictionary
        """
        self.audio = audio_provider
        self.stt = stt_provider
        self.config = config
        self.logger = logging.getLogger(__name__)

        # VAD configuration
        self.energy_threshold = config.get('audio', {}).get('energy_threshold', 4000)
        self.silence_duration = config.get('audio', {}).get('silence_duration', 1.5)

        # State
        self._listening = False
        self._listen_thread: Optional[threading.Thread] = None
        self._callback: Optional[Callable[[str], None]] = None
        self._last_audio_log_time = 0
        self._audio_activity_detected = False

        # Async transcription (optimization: non-blocking transcription)
        self.transcription_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1,  # Single worker to process transcriptions sequentially
            thread_name_prefix="transcription"
        )
        self.pending_transcriptions = []  # Track ongoing transcriptions

    def start_listening(self, on_speech_detected: Callable[[str], None]) -> None:
        """
        Start continuous listening loop.

        Args:
            on_speech_detected: Callback function called with transcribed text
        """
        if self._listening:
            return

        self._callback = on_speech_detected
        self._listening = True

        # Start listening thread
        self._listen_thread = threading.Thread(
            target=self._listening_loop,
            daemon=True
        )
        self._listen_thread.start()

    def stop_listening(self) -> None:
        """Stop listening."""
        if not self._listening:
            return

        self._listening = False

        if self._listen_thread:
            self._listen_thread.join(timeout=2.0)
            self._listen_thread = None

        # Wait for pending transcriptions before shutdown (optimization: clean async shutdown)
        if self.pending_transcriptions:
            self.logger.info("Waiting for pending transcriptions...")
            concurrent.futures.wait(self.pending_transcriptions, timeout=5.0)

        self.transcription_executor.shutdown(wait=True)
        self.audio.stop_recording()

    def _listening_loop(self) -> None:
        """Main listening loop (runs in separate thread)."""
        self.audio.start_recording()

        audio_buffer = []
        is_speaking = False
        silence_chunks = 0
        speech_chunks = 0

        sample_rate = self.audio.config.sample_rate
        chunk_size = self.audio.config.chunk_size
        chunks_per_second = sample_rate / chunk_size
        silence_chunks_threshold = int(self.silence_duration * chunks_per_second)


        while self._listening:
            try:
                # Get audio chunk
                chunk = self.audio.get_audio_chunk()

                if not chunk:
                    time.sleep(0.01)
                    continue

                # Check if chunk contains speech (simple VAD)
                is_speech, rms_level = self._detect_speech_activity(chunk)

                if is_speech:
                    # Speech detected
                    speech_chunks += 1
                    silence_chunks = 0

                    if not is_speaking and speech_chunks >= 2:
                        # Start of speech
                        is_speaking = True
                        # Don't clear buffer - keep accumulated chunks from pre-speech detection

                    # Always append speech chunks (even before is_speaking flag is set)
                    audio_buffer.append(chunk)

                    # Log if we're accumulating chunks before is_speaking flag
                    if not is_speaking and speech_chunks == 1:
                        self.logger.debug(f"First speech chunk detected (RMS={int(rms_level)}), buffering...")
                else:
                    # Silence detected
                    silence_chunks += 1
                    speech_chunks = 0  # Reset speech counter when silence detected

                    if is_speaking:
                        audio_buffer.append(chunk)

                        # Log silence accumulation
                        if silence_chunks == 1:
                            self.logger.debug(f"Silence started (RMS={int(rms_level)}, buffer has {len(audio_buffer)} chunks)")
                        elif silence_chunks % 3 == 0:  # Log every 3 silence chunks
                            self.logger.debug(f"Silence continuing... {silence_chunks}/{silence_chunks_threshold} chunks")

                        # End of speech detected
                        if silence_chunks >= silence_chunks_threshold:
                            is_speaking = False

                            # Process accumulated audio asynchronously (optimization: non-blocking)
                            # Copy buffer to avoid race conditions
                            audio_data = audio_buffer.copy()
                            audio_buffer = []

                            # Submit transcription task to executor
                            future = self.transcription_executor.submit(
                                self._process_audio_segment,
                                audio_data
                            )
                            self.pending_transcriptions.append(future)

                            # Clean up completed futures
                            self.pending_transcriptions = [
                                f for f in self.pending_transcriptions if not f.done()
                            ]
                    else:
                        # Not speaking and silence detected - clear any accumulated buffer
                        if audio_buffer:
                            self.logger.debug(f"Clearing pre-speech buffer ({len(audio_buffer)} chunks) due to extended silence")
                            audio_buffer = []

            except Exception as e:
                print(f"Error in listening loop: {e}")
                time.sleep(0.1)

    def _detect_speech_activity(self, audio_chunk: bytes) -> tuple[bool, float]:
        """
        Simple VAD using amplitude threshold (optimized with numpy).

        Args:
            audio_chunk: Audio data chunk

        Returns:
            Tuple of (is_speech, rms_level)
        """
        if not audio_chunk:
            return False, 0.0

        # Calculate RMS amplitude (assuming 16-bit PCM)
        try:
            # Convert bytes to numpy array (optimization: faster than struct.unpack)
            samples = np.frombuffer(audio_chunk, dtype=np.int16)

            # Vectorized RMS calculation (optimization: much faster than Python loop)
            rms = np.sqrt(np.mean(samples.astype(np.float32) ** 2))

            return rms > self.energy_threshold, rms

        except Exception:
            return False, 0.0

    def _process_audio_segment(self, audio_buffer: list) -> None:
        """
        Transcribe audio segment and call callback (with streaming support).

        Args:
            audio_buffer: List of audio chunks
        """
        if not audio_buffer or not self._callback:
            self.logger.debug(f"Skipping transcription - no buffer ({len(audio_buffer) if audio_buffer else 0}) or callback")
            return

        # Minimum audio check
        total_length = sum(len(chunk) for chunk in audio_buffer)
        min_length = self.audio.config.sample_rate * 2 * 0.5  # 16-bit = 2 bytes per sample
        duration = total_length / (self.audio.config.sample_rate * 2)

        if total_length < min_length:
            self.logger.warning(f"Audio segment too short: {duration:.2f}s (minimum: 0.5s) - skipping transcription")
            return

        try:
            # Check if STT provider supports streaming
            if hasattr(self.stt, 'transcribe_streaming'):

                def chunk_generator():
                    for chunk in audio_buffer:
                        yield chunk

                def on_partial_result(text: str, is_final: bool):
                    if is_final and self._callback:
                        self._callback(text)

                transcript = self.stt.transcribe_streaming(
                    chunk_generator(),
                    self.audio.config.sample_rate,
                    callback=on_partial_result
                )
            else:
                # Fallback to standard transcription
                audio_data = b''.join(audio_buffer)
                transcript = self.stt.transcribe(
                    audio_data,
                    self.audio.config.sample_rate
                )

                # Call callback if text was transcribed
                if transcript and transcript.strip() and self._callback:
                    self._callback(transcript.strip())

        except Exception as e:
            self.logger.error(f"Error transcribing audio: {e}")

    @property
    def is_listening(self) -> bool:
        """Check if currently listening."""
        return self._listening
