"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Generator
from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    model: str
    temperature: float = 0.7
    max_tokens: int = 500
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMConfig):
        """
        Initialize LLM provider.

        Args:
            config: LLM configuration
        """
        self.config = config

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text completion from prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def generate_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Generator[str, None, str]:
        """
        Generate text completion with streaming support.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Yields:
            Individual tokens as they are generated

        Returns:
            Complete generated text response
        """
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Parsed JSON response as dictionary
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if provider is available and healthy.

        Returns:
            True if provider is available, False otherwise
        """
        pass
