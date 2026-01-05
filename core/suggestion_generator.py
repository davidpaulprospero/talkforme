"""Suggestion generator for creating contextual reply suggestions."""

from typing import List, Dict, Any, Callable, Optional
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from providers.base import LLMProvider
from .models import Suggestion, ToneType, ConversationContext


# Pre-defined tone markers (class-level constant for performance)
TONE_MARKERS = {
    ToneType.PROFESSIONAL: ['thank you', 'appreciate', 'please', 'would'],
    ToneType.CASUAL: ['yeah', 'cool', 'awesome', 'hey', 'sure'],
    ToneType.EMPATHETIC: ['understand', 'feel', 'sorry', 'here for you'],
    ToneType.HUMOROUS: ['haha', 'lol', '!', '😊']
}


class SuggestionGenerator:
    """Generates reply suggestions with different tones."""

    def __init__(self, llm_provider: LLMProvider, config: Dict[str, Any]):
        """
        Initialize suggestion generator.

        Args:
            llm_provider: LLM provider instance
            config: Configuration dictionary
        """
        self.llm = llm_provider
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Get tones from config or use defaults
        tone_names = config.get('tones', ['professional', 'casual', 'empathetic', 'humorous'])
        self.tones = [ToneType(tone) for tone in tone_names]

        # Pre-cache system prompts (these never change)
        self._system_prompt_cache = {
            tone: self._get_system_prompt(tone) for tone in self.tones
        }

        # Pre-cache tone instructions (these never change)
        self._tone_instructions = {
            ToneType.PROFESSIONAL: "Keep it professional, clear, and respectful.",
            ToneType.CASUAL: "Keep it casual, friendly, and relaxed.",
            ToneType.EMPATHETIC: "Show empathy, understanding, and emotional support.",
            ToneType.HUMOROUS: "Add appropriate humor while staying relevant."
        }

        # Pre-cache prompt template (only dynamic parts are context and message)
        self._prompt_template = """Based on this conversation context:
{context}

The other person just said: "{message}"

Generate a brief {tone} reply. {instruction}

Requirements:
- Keep it VERY SHORT (5-15 words maximum, 1 sentence)
- Make it natural and conversational
- Stay contextually appropriate
- Respond ONLY with the suggested reply, no explanations or quotes

Your suggested reply:"""

        # Pre-compile regex patterns (optimization: compile once, use many times)
        self._response_prefix_regex = re.compile(
            r'^(Reply|Response|Answer):\s*',
            re.IGNORECASE
        )
        self._quote_cleanup_regex = re.compile(r'^["\']|["\']$')

    def generate_suggestions(
        self,
        latest_message: str,
        context: ConversationContext
    ) -> List[Suggestion]:
        """
        Generate multiple reply suggestions.

        Args:
            latest_message: Most recent message from other person
            context: Conversation context

        Returns:
            List of suggestions ranked by confidence
        """
        suggestions = []

        # Get conversation context for prompt
        context_str = self._format_context(context)

        # Generate suggestions in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=len(self.tones)) as executor:
            # Submit all suggestion generation tasks
            future_to_tone = {
                executor.submit(
                    self._generate_single_suggestion,
                    latest_message,
                    context_str,
                    tone
                ): tone
                for tone in self.tones
            }

            # Collect results as they complete
            for future in as_completed(future_to_tone):
                tone = future_to_tone[future]
                try:
                    self.logger.info(f"Generating {tone.value} suggestion...")
                    suggestion = future.result()
                    if suggestion:
                        suggestions.append(suggestion)
                        self.logger.info(f"[DONE] {tone.value} suggestion completed")
                except Exception as e:
                    # Log error but continue with other tones
                    self.logger.error(f"Error generating {tone.value} suggestion: {e}")

        # Rank suggestions by confidence
        suggestions.sort(key=lambda s: s.confidence_score, reverse=True)

        return suggestions

    def generate_suggestions_streaming(
        self,
        latest_message: str,
        context: ConversationContext,
        callback: Optional[Callable[[ToneType, str], None]] = None
    ) -> List[Suggestion]:
        """
        Generate multiple reply suggestions with streaming support.

        Args:
            latest_message: Most recent message from other person
            context: Conversation context
            callback: Optional callback function(tone, partial_text) for streaming updates

        Returns:
            List of suggestions ranked by confidence
        """
        suggestions = []

        # Get conversation context for prompt
        context_str = self._format_context(context)

        # Generate suggestions in parallel with streaming
        with ThreadPoolExecutor(max_workers=len(self.tones)) as executor:
            # Submit all suggestion generation tasks
            future_to_tone = {
                executor.submit(
                    self._generate_single_suggestion_streaming,
                    latest_message,
                    context_str,
                    tone,
                    callback
                ): tone
                for tone in self.tones
            }

            # Collect results as they complete
            for future in as_completed(future_to_tone):
                tone = future_to_tone[future]
                try:
                    self.logger.info(f"Generating {tone.value} suggestion...")
                    suggestion = future.result()
                    if suggestion:
                        suggestions.append(suggestion)
                        self.logger.info(f"[DONE] {tone.value} suggestion completed")
                except Exception as e:
                    # Log error but continue with other tones
                    self.logger.error(f"Error generating {tone.value} suggestion: {e}")

        # Rank suggestions by confidence
        suggestions.sort(key=lambda s: s.confidence_score, reverse=True)

        return suggestions

    def _generate_single_suggestion(
        self,
        message: str,
        context: str,
        tone: ToneType
    ) -> Suggestion:
        """
        Generate a single suggestion for a specific tone.

        Args:
            message: Latest message from other person
            context: Formatted conversation context
            tone: Desired tone

        Returns:
            Generated suggestion
        """
        prompt = self._build_prompt(message, context, tone)
        system_prompt = self._system_prompt_cache[tone]  # Use cached system prompt

        # Generate response from LLM
        response = self.llm.generate(prompt, system_prompt)

        # Clean up response
        reply = self._clean_response(response)

        # Calculate confidence score
        confidence = self._calculate_confidence(reply, message, context, tone)

        return Suggestion(
            content=reply,
            tone=tone,
            confidence_score=confidence,
            reasoning=None  # Could add reasoning from LLM later
        )

    def _generate_single_suggestion_streaming(
        self,
        message: str,
        context: str,
        tone: ToneType,
        callback: Optional[Callable[[ToneType, str], None]] = None
    ) -> Suggestion:
        """
        Generate a single suggestion for a specific tone with streaming.

        Args:
            message: Latest message from other person
            context: Formatted conversation context
            tone: Desired tone
            callback: Optional callback function for streaming updates

        Returns:
            Generated suggestion
        """
        prompt = self._build_prompt(message, context, tone)
        system_prompt = self._system_prompt_cache[tone]  # Use cached system prompt

        # Use streaming generation
        full_response = ""
        for token in self.llm.generate_streaming(prompt, system_prompt):
            full_response += token
            if callback:
                # Send partial update to callback
                callback(tone, full_response)

        # Clean up response
        reply = self._clean_response(full_response)

        # Calculate confidence score
        confidence = self._calculate_confidence(reply, message, context, tone)

        return Suggestion(
            content=reply,
            tone=tone,
            confidence_score=confidence,
            reasoning=None
        )

    def _build_prompt(
        self,
        message: str,
        context: str,
        tone: ToneType
    ) -> str:
        """
        Build LLM prompt for specific tone using cached template.

        Args:
            message: Latest message
            context: Conversation context
            tone: Desired tone

        Returns:
            Formatted prompt
        """
        # Use pre-cached template and instructions for faster formatting
        return self._prompt_template.format(
            context=context,
            message=message,
            tone=tone.value,
            instruction=self._tone_instructions.get(tone, '')
        )

    def _get_system_prompt(self, tone: ToneType) -> str:
        """
        Get system prompt for specific tone.

        Args:
            tone: Desired tone

        Returns:
            System prompt
        """
        return (
            "You are a helpful conversation assistant. "
            "Generate natural, contextually appropriate replies "
            "that help the user respond thoughtfully."
        )

    def _format_context(self, context: ConversationContext) -> str:
        """
        Format conversation context for prompt.

        Args:
            context: Conversation context

        Returns:
            Formatted context string
        """
        recent_messages = context.get_recent_messages(5)

        if not recent_messages:
            return "No previous conversation context."

        formatted_lines = []
        for msg in recent_messages:
            speaker = "Other" if msg.speaker.value == "other" else "You"
            formatted_lines.append(f"{speaker}: {msg.content}")

        return "\n".join(formatted_lines)

    def _clean_response(self, response: str) -> str:
        """
        Clean up LLM response.

        Args:
            response: Raw LLM response

        Returns:
            Cleaned response
        """
        # Remove common prefixes/suffixes
        response = response.strip()

        # Remove quotes if the entire response is quoted (optimization: use cached regex)
        response = self._quote_cleanup_regex.sub('', response)

        # Remove "Reply:" or similar prefixes (optimization: use pre-compiled regex)
        response = self._response_prefix_regex.sub('', response)

        return response.strip()

    def _calculate_confidence(
        self,
        suggestion: str,
        message: str,
        context: str,
        tone: ToneType
    ) -> float:
        """
        Calculate confidence score for suggestion.

        Args:
            suggestion: Generated suggestion
            message: Original message
            context: Conversation context
            tone: Tone used

        Returns:
            Confidence score (0.0 to 1.0)
        """
        score = 0.5  # Base score

        # Length check (prefer 20-150 characters)
        length = len(suggestion)
        if 20 <= length <= 150:
            score += 0.2
        elif length < 20:
            score -= 0.2
        elif length > 200:
            score -= 0.1

        # Check if it's not just repeating the input
        if suggestion.lower() not in message.lower():
            score += 0.1

        # Check for tone-specific markers (optimization: use pre-defined constant)
        markers = TONE_MARKERS.get(tone, [])
        if any(marker in suggestion.lower() for marker in markers):
            score += 0.1

        # Ensure score is between 0.0 and 1.0
        return max(0.0, min(1.0, score))
