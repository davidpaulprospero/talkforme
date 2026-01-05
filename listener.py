"""Audio listener module - captures and transcribes speech."""

import sys
import signal
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import ConfigLoader, setup_logger
from providers import (
    FasterWhisperProvider, VoskProvider, SpeechRecognitionProvider, STTConfig,
    PyAudioProvider, AudioConfig
)
from core import AudioListener


class SpeechListener:
    """Audio listener that captures speech and outputs transcriptions."""

    def __init__(self):
        """Initialize speech listener."""
        # Load configuration
        self.config = ConfigLoader()
        log_level = self.config.get_env('LOG_LEVEL', 'INFO')
        self.logger = setup_logger(log_level)

        # Configure all child loggers (core.*, providers.*)
        import logging
        logging.basicConfig(level=getattr(logging, log_level.upper(), logging.INFO))

        # Initialize providers
        self._init_providers()

        # Initialize audio listener
        self.audio_listener = AudioListener(
            audio_provider=self.audio_provider,
            stt_provider=self.stt_provider,
            config=self.config.config
        )

        self.running = False

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _init_providers(self) -> None:
        """Initialize STT and audio providers."""
        # STT Provider (dynamic based on config)
        stt_config = STTConfig(
            language=self.config.get('stt.language', 'en-US'),
            model=self.config.get('stt.model', 'base'),
            energy_threshold=self.config.get('audio.energy_threshold', 4000),
            sample_rate=self.config.get('audio.sample_rate', 16000)
        )

        # Select STT provider based on config
        provider_name = self.config.get('stt.provider', 'faster_whisper')
        if provider_name == 'vosk':
            self.stt_provider = VoskProvider(stt_config)
        elif provider_name == 'speech_recognition':
            self.stt_provider = SpeechRecognitionProvider(stt_config)
        else:  # Default to faster_whisper
            self.stt_provider = FasterWhisperProvider(stt_config)

        # Audio Provider (PyAudio)
        audio_config = AudioConfig(
            sample_rate=self.config.get('audio.sample_rate', 16000),
            channels=self.config.get('audio.channels', 1),
            chunk_size=self.config.get('audio.chunk_size', 1024),
            input_device_index=self.config.get('audio.input_device_index')
        )
        self.audio_provider = PyAudioProvider(audio_config)

    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals."""
        self.logger.info("\nShutting down listener...")
        self.stop()
        sys.exit(0)

    def _health_checks(self) -> bool:
        """Run health checks on providers."""
        self.logger.info("Running health checks...")

        # Check STT provider
        if not self.stt_provider.health_check():
            self.logger.error("STT provider health check failed")
            return False
        self.logger.info("[OK] STT provider")

        # Check audio provider
        if not self.audio_provider.health_check():
            self.logger.error("Audio provider health check failed")
            return False
        self.logger.info("[OK] Audio provider")

        return True

    def on_speech_detected(self, transcript: str) -> None:
        """
        Called when speech is detected and transcribed.

        Args:
            transcript: Transcribed text
        """
        if not transcript.strip():
            return

        # Output as JSON for the responder module to consume
        output = {
            "type": "transcript",
            "text": transcript.strip()
        }
        print(json.dumps(output), flush=True)

    def start(self) -> None:
        """Start listening for speech."""
        self.logger.info("="*60)
        self.logger.info("Speech Listener - Audio Capture & Transcription")
        self.logger.info("="*60)

        # Health checks
        if not self._health_checks():
            self.logger.error("Health checks failed. Exiting.")
            sys.exit(1)

        self.logger.info("\nListening for speech... (Press Ctrl+C to stop)")
        self.running = True

        # Start listening
        self.audio_listener.start_listening(self.on_speech_detected)

        # Keep running
        try:
            while self.running:
                import time
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """Stop listening."""
        self.running = False
        self.audio_listener.stop_listening()
        self.logger.info("Listener stopped.")


def main():
    """Main entry point for listener module."""
    try:
        listener = SpeechListener()
        listener.start()
    except KeyboardInterrupt:
        print("\nStopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
