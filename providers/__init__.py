"""Provider implementations for Talk For Me."""

from .base import (
    LLMProvider, LLMConfig,
    SpeechToTextProvider, STTConfig,
    AudioProvider, AudioConfig
)
from .llm import OllamaLLMProvider
from .stt import SpeechRecognitionProvider, FasterWhisperProvider, VoskProvider
from .audio import PyAudioProvider

__all__ = [
    'LLMProvider',
    'LLMConfig',
    'SpeechToTextProvider',
    'STTConfig',
    'AudioProvider',
    'AudioConfig',
    'OllamaLLMProvider',
    'SpeechRecognitionProvider',
    'FasterWhisperProvider',
    'VoskProvider',
    'PyAudioProvider',
]
