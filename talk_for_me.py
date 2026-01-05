"""Talk For Me - Real-time conversation suggestion system."""

import sys
import signal
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import ConfigLoader, setup_logger
from providers import (
    OllamaLLMProvider, LLMConfig,
    FasterWhisperProvider, VoskProvider, SpeechRecognitionProvider, STTConfig,
    PyAudioProvider, AudioConfig
)
from core import (
    ConversationManager,
    SuggestionGenerator,
    AudioListener,
    SpeakerRole
)


class TalkForMe:
    """Main application class for Talk For Me."""

    def __init__(self):
        """Initialize Talk For Me application."""
        # Load configuration
        self.config = ConfigLoader()
        self.logger = setup_logger(self.config.get_env('LOG_LEVEL', 'INFO'))

        # Initialize providers
        self._init_providers()

        # Initialize core components
        self.conversation_manager = ConversationManager(
            data_dir=self.config.get('conversation.data_dir', 'data')
        )
        self.suggestion_generator = SuggestionGenerator(
            llm_provider=self.llm_provider,
            config=self.config.config
        )
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
        """Initialize all providers."""
        # LLM Provider (Ollama)
        llm_config = LLMConfig(
            model=self.config.get_env('OLLAMA_MODEL', 'llama2'),
            base_url=self.config.get_env('OLLAMA_BASE_URL', 'http://localhost:11434'),
            temperature=self.config.get('llm.temperature', 0.7),
            max_tokens=self.config.get('llm.max_tokens', 500)
        )
        self.llm_provider = OllamaLLMProvider(llm_config)

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

    def _signal_handler(self, signum, frame):
        """Handle interrupt signals."""
        self.logger.info("\nReceived interrupt signal. Shutting down...")
        self.running = False

    def _health_checks(self) -> bool:
        """
        Verify all providers are healthy.

        Returns:
            True if all checks pass, False otherwise
        """
        self.logger.info("Running health checks...")

        checks = {
            'Ollama LLM': self.llm_provider.health_check(),
            'Speech Recognition': self.stt_provider.health_check(),
        }

        for component, status in checks.items():
            status_str = "[OK]" if status else "[FAIL]"
            self.logger.info(f"{status_str} {component}")

        all_passed = all(checks.values())
        return all_passed

    def on_speech_detected(self, transcript: str) -> None:
        """
        Handle new speech from other speaker.

        Args:
            transcript: Transcribed speech
        """
        if not transcript.strip():
            return

        # Filter out very short transcriptions (noise/artifacts)
        word_count = len(transcript.split())
        min_words = self.config.get('transcription.min_words', 3)

        if word_count < min_words:
            self.logger.debug(f"Transcript too short ({word_count} words): '{transcript}'")
            return

        # Display transcript
        print(f"\n[OTHER PERSON]: {transcript}")

        # Add to conversation
        self.conversation_manager.add_message(transcript, SpeakerRole.OTHER)

        # Generate suggestions
        self.logger.info("Generating suggestions...")
        try:
            suggestions = self.suggestion_generator.generate_suggestions_streaming(
                latest_message=transcript,
                context=self.conversation_manager.current_context,
                callback=None  # Disable streaming UI updates
            )

            # Display final suggestions
            self.logger.info("[DONE] Suggestions generated")
            self._display_suggestions(suggestions)

            # Auto-save if enabled
            if self.config.get('conversation.auto_save', True):
                self.conversation_manager.save_session()

        except Exception as e:
            self.logger.error(f"Error generating suggestions: {e}")

    def _display_suggestions(self, suggestions: list) -> None:
        """
        Display suggestions to user.

        Args:
            suggestions: List of suggestions
        """
        if suggestions:
            print("\n" + "=" * 60)
            print("SUGGESTIONS:")
            print("=" * 60)
            for i, suggestion in enumerate(suggestions, 1):
                print(f"\n{i}. [{suggestion.tone.value.upper()}] {suggestion.content}")
            print()
        else:
            self.logger.info("No suggestions generated")

    def _display_partial_suggestions(self, partial_suggestions: dict) -> None:
        """
        Display suggestions as they stream in (updates in place).

        Args:
            partial_suggestions: Dictionary mapping tones to partial text
        """
        import sys

        # Clear previous output (move cursor up and clear lines)
        # Calculate lines to clear: header (3 lines) + suggestions (2 lines each)
        lines_to_clear = 4 + (len(partial_suggestions) * 3)
        for _ in range(lines_to_clear):
            sys.stdout.write("\033[F")  # Move cursor up
            sys.stdout.write("\033[K")  # Clear line

        print("\n" + "=" * 60)
        print("GENERATING SUGGESTIONS...")
        print("=" * 60)

        for tone, text in partial_suggestions.items():
            if text:
                # Clean partial text for display
                display_text = text.strip()
                if len(display_text) > 100:
                    display_text = display_text[:100] + "..."
                print(f"\n[{tone.value.upper()}] {display_text}")

        print()
        sys.stdout.flush()

    def run(self) -> None:
        """Run the main application loop."""
        self.logger.info("=" * 60)
        self.logger.info("Talk For Me - Real-time Conversation Assistant")
        self.logger.info("=" * 60)

        # Health checks
        if not self._health_checks():
            self.logger.error("Health checks failed. Please ensure:")
            self.logger.error("  - Ollama is running (ollama serve)")
            self.logger.error("  - Internet connection available for STT")
            return

        # Start listening
        self.running = True
        self.logger.info("\nListening for speech... (Press Ctrl+C to stop)")

        try:
            self.audio_listener.start_listening(
                on_speech_detected=self.on_speech_detected
            )

            # Keep running until interrupted
            while self.running:
                import time
                time.sleep(0.1)

        except KeyboardInterrupt:
            pass

        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Cleanup resources and save session."""
        self.logger.info("\nStopping listener...")
        # Stop listening
        self.audio_listener.stop_listening()

        # Save final session
        if self.conversation_manager.get_message_count() > 0:
            self.logger.info("Saving conversation...")
            self.conversation_manager.save_session()
            self.logger.info("Session saved")


def main():
    """Entry point for Talk For Me."""
    try:
        app = TalkForMe()
        app.run()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nPlease ensure:")
        print("  1. config.json exists in the project root")
        print("  2. Copy .env.example to .env and configure as needed")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
