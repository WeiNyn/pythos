"""
LLM provider initialization and factory
"""

from typing import Optional

from ..config import AgentConfig
from .base import BaseLLMProvider
from .openai import OpenAIProvider


def create_llm_provider(config: AgentConfig) -> BaseLLMProvider:
    """
    Create an LLM provider instance based on configuration

    Args:
        config: Agent configuration containing provider selection

    Returns:
        Initialized LLM provider

    Raises:
        ValueError: If provider type is not supported
    """
    if config.llm_provider == "openai":
        return OpenAIProvider(api_key=config.api_key, rpm=config.rate_limit)
    elif config.llm_provider == "anthropic":
        # TODO: Implement Anthropic provider
        raise NotImplementedError("Anthropic provider not yet implemented")
    else:
        raise ValueError(f"Unsupported LLM provider: {config.llm_provider}")


__all__ = ["BaseLLMProvider", "create_llm_provider"]
