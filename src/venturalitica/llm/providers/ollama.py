"""Ollama provider — the local-daemon generic fallback."""

from __future__ import annotations

from typing import Any, Optional, Tuple

from ..base import ModelCard, ProviderError
from ..catalog import OLLAMA_DEFAULT

# Module-level optional import so mocks can patch at this path without
# requiring the [agentic] extra to be installed in the test env.
try:  # pragma: no cover
    from langchain_ollama import ChatOllama
except ImportError:  # pragma: no cover
    ChatOllama = None  # type: ignore[assignment]


class OllamaProvider:
    """Wraps whichever model the local Ollama daemon has pulled."""

    name: str = "ollama"
    aliases: Tuple[str, ...] = ("ollama", "local")
    default_card: ModelCard = OLLAMA_DEFAULT

    def __init__(self, card: ModelCard | None = None, model_name: Optional[str] = None) -> None:
        self.card = card or self.default_card
        # `model_name` overrides the card's default — useful for users who
        # have a custom model pulled into Ollama (e.g. llama3.1, qwen2.5).
        # Slashed names like `meta-llama/Llama-3.1-8B` are HuggingFace ids,
        # not Ollama tags, so we ignore them here.
        if model_name and "/" not in model_name:
            self._model = model_name
        else:
            self._model = self.card.api_model or "mistral"

    @property
    def resolved_model(self) -> str:
        """Return the actual Ollama tag this provider will pull."""
        return self._model

    def create_chat_model(self, **opts: Any):
        if ChatOllama is None:
            raise ProviderError(
                "The `ollama` provider requires langchain-ollama. "
                "Install with: pip install 'venturalitica[agentic]'"
            )
        settings = {"temperature": 0.1, **opts}
        return ChatOllama(model=self._model, **settings)
