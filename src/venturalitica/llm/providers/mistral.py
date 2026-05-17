"""Mistral cloud provider — Magistral via langchain-mistralai."""

from __future__ import annotations

import os
from typing import Any, Optional, Tuple

from ..base import ModelCard, ProviderError
from ..catalog import MISTRAL_DEFAULT

# Module-level optional import (see _gguf.py / ollama.py for rationale).
try:  # pragma: no cover
    from langchain_mistralai import ChatMistralAI
except ImportError:  # pragma: no cover
    ChatMistralAI = None  # type: ignore[assignment]


class MistralCloudProvider:
    """Hosted Magistral reasoning model. Needs MISTRAL_API_KEY."""

    name: str = "cloud"
    aliases: Tuple[str, ...] = ("cloud", "mistral")
    default_card: ModelCard = MISTRAL_DEFAULT

    def __init__(self, card: ModelCard | None = None, api_key: Optional[str] = None) -> None:
        self.card = card or self.default_card
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")

    def create_chat_model(self, **opts: Any):
        if not self.api_key:
            raise ProviderError(
                "MISTRAL_API_KEY is required for the `cloud` (Mistral Magistral) "
                "provider. Either export the env var or pass api_key=... to the "
                "factory."
            )
        if ChatMistralAI is None:
            raise ProviderError(
                "The `cloud` provider requires langchain-mistralai. "
                "Install with: pip install 'venturalitica[agentic]'"
            )

        settings = {
            "temperature": 0.1,
            "max_retries": 3,
            "timeout": 180,
            **opts,
        }
        try:
            return ChatMistralAI(
                api_key=self.api_key,
                model=self.card.api_model,
                **settings,
            )
        except Exception as exc:
            raise ProviderError(
                f"ChatMistralAI failed to initialise ({self.card.api_model}): {exc}"
            ) from exc
