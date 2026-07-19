"""
Groq provider for SupplySense agent layer.

Uses Groq's llama-3.3-70b-versatile model for all LLM-powered reasoning
(planning, composition, critique, sweep summaries).
"""

import json
import logging
import os
from typing import Optional

from groq import Groq

logger = logging.getLogger(__name__)

# Model to use
GROQ_MODEL = "llama-3.3-70b-versatile"


class GroqProvider:
    """
    Wrapper for Groq API calls.
    
    Uses the GROQ_API_KEY environment variable for authentication.
    All calls use llama-3.3-70b-versatile model.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Groq provider.

        Args:
            api_key: Optional API key. If not provided, uses GROQ_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Set it as an environment variable or pass it to __init__."
            )

        self.client = Groq(api_key=self.api_key)
        logger.info(f"Groq provider initialized with model: {GROQ_MODEL}")

    def call(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """
        Make a synchronous call to Groq API.

        Args:
            system_prompt: System prompt for Claude behavior
            user_message: User's question/task
            max_tokens: Max tokens in response (default 2000)
            temperature: Sampling temperature (0-2, default 0.7)

        Returns:
            str: The LLM response text

        Raises:
            Exception: On API error
        """
        try:
            logger.debug(
                f"Calling Groq {GROQ_MODEL} | tokens: {max_tokens} | temp: {temperature}"
            )

            message = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            response_text = message.choices[0].message.content
            logger.debug(f"Response received: {len(response_text)} chars")
            return response_text

        except Exception as e:
            logger.error(f"Groq API call failed: {e}", exc_info=True)
            raise


# Global provider instance (lazy-initialized)
_groq_provider: Optional[GroqProvider] = None


def get_groq_provider() -> GroqProvider:
    """
    Get or create the global Groq provider instance.

    Returns:
        GroqProvider: Initialized and ready to use
    """
    global _groq_provider
    if _groq_provider is None:
        _groq_provider = GroqProvider()
    return _groq_provider


def call_groq(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 2000,
    temperature: float = 0.7,
) -> str:
    """
    Convenience function to call Groq without managing provider instance.

    Args:
        system_prompt: System prompt
        user_message: User message
        max_tokens: Max tokens (default 2000)
        temperature: Temperature (default 0.7)

    Returns:
        str: LLM response
    """
    provider = get_groq_provider()
    return provider.call(system_prompt, user_message, max_tokens, temperature)
