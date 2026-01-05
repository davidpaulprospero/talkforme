"""Conversation manager for handling conversation history and persistence."""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .models import ConversationContext, Message, SpeakerRole


class ConversationManager:
    """Manages conversation history and persistence."""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize conversation manager.

        Args:
            data_dir: Directory for storing conversation data
        """
        self.data_dir = Path(data_dir)
        self.current_context = ConversationContext()
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        """Ensure data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def add_message(self, content: str, speaker: SpeakerRole) -> Message:
        """
        Add new message to conversation.

        Args:
            content: Message content
            speaker: Speaker role

        Returns:
            Created message
        """
        message = Message(content=content, speaker=speaker)
        self.current_context.add_message(message)
        return message

    def get_context_for_llm(self, last_n_messages: int = 5) -> str:
        """
        Format recent messages for LLM prompt.

        Args:
            last_n_messages: Number of recent messages to include

        Returns:
            Formatted conversation context string
        """
        recent_messages = self.current_context.get_recent_messages(last_n_messages)

        if not recent_messages:
            return "No previous conversation context."

        formatted_lines = []
        for msg in recent_messages:
            speaker_label = "Other person" if msg.speaker == SpeakerRole.OTHER else "You"
            formatted_lines.append(f"{speaker_label}: {msg.content}")

        return "\n".join(formatted_lines)

    def save_session(self, filename: Optional[str] = None) -> str:
        """
        Persist current session to JSON.

        Args:
            filename: Optional custom filename (defaults to session_id.json)

        Returns:
            Path to saved file
        """
        if filename is None:
            filename = f"{self.current_context.session_id}.json"

        filepath = self.data_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.current_context.to_dict(), f, indent=2, ensure_ascii=False)

        return str(filepath)

    def load_session(self, session_id: str) -> ConversationContext:
        """
        Load previous session from JSON.

        Args:
            session_id: Session ID to load

        Returns:
            Loaded conversation context

        Raises:
            FileNotFoundError: If session file doesn't exist
        """
        filepath = self.data_dir / f"{session_id}.json"

        if not filepath.exists():
            raise FileNotFoundError(f"Session file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.current_context = ConversationContext.from_dict(data)
        return self.current_context

    def get_all_sessions(self) -> List[str]:
        """
        List all saved session IDs.

        Returns:
            List of session IDs
        """
        if not self.data_dir.exists():
            return []

        session_files = self.data_dir.glob("*.json")
        return [f.stem for f in session_files if f.stem != "conversation_history"]

    def clear_current_session(self) -> None:
        """Clear current conversation context and start new session."""
        self.current_context = ConversationContext()

    def get_message_count(self) -> int:
        """
        Get total number of messages in current session.

        Returns:
            Message count
        """
        return len(self.current_context.messages)

    def get_last_message(self) -> Optional[Message]:
        """
        Get the most recent message.

        Returns:
            Last message or None if no messages
        """
        if self.current_context.messages:
            return self.current_context.messages[-1]
        return None
