"""Ollama LLM provider implementation."""

import requests
import json
from typing import Optional, Dict, Any, Generator
from providers.base import LLMProvider, LLMConfig


class OllamaLLMProvider(LLMProvider):
    """Ollama local LLM implementation."""

    def __init__(self, config: LLMConfig):
        """
        Initialize Ollama provider.

        Args:
            config: LLM configuration
        """
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"

        # Create session for HTTP connection pooling (optimization: reuse connections)
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text completion from Ollama.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text response

        Raises:
            RuntimeError: If Ollama API request fails
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        }

        try:
            # Use session for connection pooling (optimization)
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()['response']
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama API error: {e}")

    def generate_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Generator[str, None, str]:
        """
        Generate text completion from Ollama with streaming support.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Yields:
            Individual tokens as they are generated

        Returns:
            Complete generated text response

        Raises:
            RuntimeError: If Ollama API request fails
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": True,  # Enable streaming
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        }

        try:
            # Use session for connection pooling (optimization)
            response = self.session.post(url, json=payload, timeout=60, stream=True)
            response.raise_for_status()

            # Stream response chunks
            full_response = ""
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if "response" in chunk:
                        token = chunk["response"]
                        full_response += token
                        yield token  # Yield each token as it arrives
                    if chunk.get("done"):
                        break

            return full_response

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama API error: {e}")

    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate JSON response from Ollama.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Parsed JSON response as dictionary

        Raises:
            ValueError: If response is not valid JSON
        """
        # Add instruction to return JSON in prompt
        json_prompt = f"{prompt}\n\nRespond ONLY with valid JSON."
        response_text = self.generate(json_prompt, system_prompt)

        # Extract JSON from response
        try:
            # Try to find JSON in response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response_text[start:end]
                return json.loads(json_str)
            else:
                return json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from response: {response_text}") from e

    def health_check(self) -> bool:
        """
        Check Ollama availability and warm the model.

        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            # Check if Ollama is running
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return False

            # Warm model with minimal prompt (optimization: loads model into memory)
            warmup_payload = {
                "model": self.config.model,
                "prompt": "Hi",
                "stream": False,
                "options": {"num_predict": 1}
            }
            warmup_response = self.session.post(
                f"{self.base_url}/api/generate",
                json=warmup_payload,
                timeout=30
            )

            return warmup_response.status_code == 200
        except Exception:
            return False

    def __del__(self):
        """Cleanup session on deletion."""
        if hasattr(self, 'session'):
            self.session.close()
