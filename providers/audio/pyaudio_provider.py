"""PyAudio provider implementation."""

import pyaudio
import queue
import threading
from typing import List
from providers.base import AudioProvider, AudioConfig


class PyAudioProvider(AudioProvider):
    """Audio capture using PyAudio."""

    def __init__(self, config: AudioConfig):
        """
        Initialize PyAudio provider.

        Args:
            config: Audio configuration
        """
        super().__init__(config)
        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream = None
        self.audio_queue = queue.Queue()
        self._recording_thread = None
        self._stop_event = threading.Event()

    def start_recording(self) -> None:
        """Start continuous recording."""
        if self._is_recording:
            return

        self._is_recording = True
        self._stop_event.clear()

        # Open audio stream
        self.stream = self.pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            input_device_index=self.config.input_device_index,
            frames_per_buffer=self.config.chunk_size,
            stream_callback=self._audio_callback
        )

        self.stream.start_stream()

    def stop_recording(self) -> None:
        """Stop recording."""
        if not self._is_recording:
            return

        self._is_recording = False
        self._stop_event.set()

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        # Clear the queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """
        Callback for audio stream.

        Args:
            in_data: Audio data from stream
            frame_count: Number of frames
            time_info: Timing information
            status: Stream status

        Returns:
            Tuple of (data, continue_flag)
        """
        if self._is_recording and not self._stop_event.is_set():
            self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)

    def get_audio_chunk(self) -> bytes:
        """
        Get latest audio chunk from queue.

        Returns:
            Audio chunk as bytes (empty if queue is empty)
        """
        try:
            return self.audio_queue.get(timeout=0.1)  # Reduced from 1.0s for faster responsiveness
        except queue.Empty:
            return b''

    def record_for_duration(self, duration_seconds: float) -> bytes:
        """
        Record audio for specific duration.

        Args:
            duration_seconds: Duration to record

        Returns:
            Complete audio data as bytes
        """
        frames = []
        chunks_needed = int(
            self.config.sample_rate / self.config.chunk_size * duration_seconds
        )

        stream = self.pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            input_device_index=self.config.input_device_index,
            frames_per_buffer=self.config.chunk_size
        )

        try:
            for _ in range(chunks_needed):
                data = stream.read(self.config.chunk_size)
                frames.append(data)
        finally:
            stream.stop_stream()
            stream.close()

        return b''.join(frames)

    def list_devices(self) -> List[dict]:
        """
        List available input devices.

        Returns:
            List of device information dictionaries
        """
        devices = []
        for i in range(self.pyaudio_instance.get_device_count()):
            try:
                device_info = self.pyaudio_instance.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'sample_rate': int(device_info['defaultSampleRate']),
                        'max_input_channels': device_info['maxInputChannels']
                    })
            except Exception:
                # Skip devices that cause errors
                continue
        return devices

    def health_check(self) -> bool:
        """
        Check if PyAudio is available and can access audio devices.

        Returns:
            True if PyAudio is functional, False otherwise
        """
        try:
            # Check if we can get device count
            device_count = self.pyaudio_instance.get_device_count()
            if device_count == 0:
                return False

            # Check if configured device exists (if specified)
            if self.config.input_device_index is not None:
                try:
                    device_info = self.pyaudio_instance.get_device_info_by_index(
                        self.config.input_device_index
                    )
                    if device_info['maxInputChannels'] == 0:
                        return False
                except Exception:
                    return False

            return True
        except Exception:
            return False

    def __del__(self):
        """Cleanup resources."""
        self.stop_recording()
        if hasattr(self, 'pyaudio_instance'):
            self.pyaudio_instance.terminate()
