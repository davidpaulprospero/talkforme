"""Core data models for Talk For Me conversation system."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import json


class ToneType(Enum):
    """Available tone types for suggestions."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    EMPATHETIC = "empathetic"
    HUMOROUS = "humorous"


class SpeakerRole(Enum):
    """Speaker role in conversation."""
    OTHER = "other"  # The person we're listening to
    USER = "user"    # Our responses


@dataclass
class Message:
    """Represents a single message in conversation."""
    content: str
    speaker: SpeakerRole
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert message to dictionary for JSON serialization."""
        return {
            "content": self.content,
            "speaker": self.speaker.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        """Create message from dictionary."""
        return cls(
            content=data["content"],
            speaker=SpeakerRole(data["speaker"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class Suggestion:
    """Represents a reply suggestion."""
    content: str
    tone: ToneType
    confidence_score: float  # 0.0 to 1.0
    reasoning: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert suggestion to dictionary."""
        return {
            "content": self.content,
            "tone": self.tone.value,
            "confidence_score": self.confidence_score,
            "reasoning": self.reasoning
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Suggestion':
        """Create suggestion from dictionary."""
        return cls(
            content=data["content"],
            tone=ToneType(data["tone"]),
            confidence_score=data["confidence_score"],
            reasoning=data.get("reasoning")
        )


@dataclass
class ConversationContext:
    """Holds conversation history and context."""
    messages: List[Message] = field(default_factory=list)
    session_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    max_history: int = 20  # Keep last N messages for context

    def add_message(self, message: Message) -> None:
        """Add message and maintain max history."""
        self.messages.append(message)
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]

    def get_recent_messages(self, count: int = 5) -> List[Message]:
        """Get N most recent messages."""
        return self.messages[-count:] if count <= len(self.messages) else self.messages

    def to_dict(self) -> dict:
        """Convert context to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "max_history": self.max_history
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ConversationContext':
        """Create context from dictionary."""
        ctx = cls(
            session_id=data["session_id"],
            max_history=data.get("max_history", 20)
        )
        ctx.messages = [Message.from_dict(msg) for msg in data.get("messages", [])]
        return ctx
