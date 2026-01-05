"""Base abstract classes for providers."""

from .llm_provider import LLMProvider, LLMConfig
from .stt_provider import SpeechToTextProvider, STTConfig
from .audio_provider import AudioProvider, AudioConfig

__all__ = [
    'LLMProvider',
    'LLMConfig',
    'SpeechToTextProvider',
    'STTConfig',
    'AudioProvider',
    'AudioConfig',
]
