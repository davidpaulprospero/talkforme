"""Responder module - generates conversation suggestions."""

import sys
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import ConfigLoader, setup_logger
from providers import OllamaLLMProvider, LLMConfig
from core import (
    ConversationManager,
    SuggestionGenerator,
    SpeakerRole
)


class SuggestionResponder:
    """Generates conversation suggestions based on transcribed speech."""

    def __init__(self):
        """Initialize suggestion responder."""
        # Load configuration
        self.config = ConfigLoader()
        self.logger = setup_logger(self.config.get_env('LOG_LEVEL', 'INFO'))

        # Initialize LLM provider
        self._init_llm_provider()

        # Initialize core components
        self.conversation_manager = ConversationManager(
            data_dir=self.config.get('conversation.data_dir', 'data')
        )
        self.suggestion_generator = SuggestionGenerator(
            llm_provider=self.llm_provider,
            config=self.config.config
        )

    def _init_llm_provider(self) -> None:
        """Initialize LLM provider."""
        llm_config = LLMConfig(
            model=self.config.get_env('OLLAMA_MODEL', 'gemma3:4b'),
            base_url=self.config.get_env('OLLAMA_BASE_URL', 'http://localhost:11434'),
            temperature=self.config.get('llm.temperature', 0.7),
            max_tokens=self.config.get('llm.max_tokens', 30)
        )
        self.llm_provider = OllamaLLMProvider(llm_config)

    def _health_check(self) -> bool:
        """Run health check on LLM provider."""
        self.logger.info("Running health check...")

        if not self.llm_provider.health_check():
            self.logger.error("LLM provider health check failed")
            return False

        self.logger.info("[OK] LLM provider")
        return True

    def process_transcript(self, transcript: str) -> None:
        """
        Process transcribed text and generate suggestions.

        Args:
            transcript: Transcribed speech text
        """
        if not transcript.strip():
            return

        self.logger.info(f"\n[OTHER PERSON]: {transcript}")

        # Add to conversation
        self.conversation_manager.add_message(transcript, SpeakerRole.OTHER)

        # Generate suggestions with streaming (no UI callback for cleaner output)
        self.logger.info("Generating suggestions...")
        import time
        start_time = time.time()

        try:
            suggestions = self.suggestion_generator.generate_suggestions_streaming(
                latest_message=transcript,
                context=self.conversation_manager.current_context,
                callback=None  # Disable streaming UI updates
            )

            # Log generation time
            elapsed_time = time.time() - start_time
            self.logger.info(f"[DONE] Suggestions generated in {elapsed_time:.2f} seconds")

            # Display suggestions
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
        if not suggestions:
            print("\nNo suggestions generated.\n")
            return

        # Display each suggestion without numbering
        for suggestion in suggestions:
            print(suggestion.content)

    def start(self) -> None:
        """Start listening for transcripts from stdin."""
        self.logger.info("="*60)
        self.logger.info("Suggestion Responder - LLM-Based Replies")
        self.logger.info("="*60)

        # Health check
        if not self._health_check():
            self.logger.error("Health check failed. Exiting.")
            sys.exit(1)

        self.logger.info("\nWaiting for transcripts... (Press Ctrl+C to stop)")

        # Read JSON input from stdin
        try:
            for line in sys.stdin:
                try:
                    data = json.loads(line.strip())
                    if data.get("type") == "transcript":
                        transcript = data.get("text", "")
                        self.process_transcript(transcript)
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON input: {line.strip()}")
        except KeyboardInterrupt:
            self.logger.info("\nStopped by user")


def main():
    """Main entry point for responder module."""
    try:
        responder = SuggestionResponder()
        responder.start()
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
