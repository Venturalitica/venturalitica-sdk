"""LLM provider abstractions.

The Venturalítica SDK lets users plug in different LLM backends for the
agentic Annex IV writer (`vl annex-iv`, `assurance.graph`). Each backend is
modelled as a `LLMProvider` — a thin factory that knows how to instantiate a
LangChain `BaseChatModel`. Provider metadata (which model, where it lives,
what languages it supports, what it costs in RAM/$) is carried by a
`ModelCard` dataclass so callers can inspect the catalogue without importing
heavy LangChain machinery.

Design goals:

- **One provider per file** under `providers/` so adding a new backend
  (DeepSeek, a self-hosted vLLM endpoint, an OpenAI-compatible router…) is
  a single file plus one registry entry.
- **Lazy imports** of LangChain / huggingface-hub inside provider methods.
  Importing this base module never pulls torch or langchain, so the SDK
  base install stays light.
- **Declarative catalogue** of model variants in `catalog.py`. The
  dashboard, CLI help, and tests all read from the same ModelCard objects.
- **Back-compat aliases** centralised in `registry.py::ALIASES` so legacy
  provider names (`transformers`, `mistral`, …) keep working without
  scattering string compares through the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional, Protocol, Tuple

if TYPE_CHECKING:
    # Hint-only — never imported at runtime so this module stays import-cheap.
    from langchain_core.language_models import BaseChatModel


class ProviderError(RuntimeError):
    """Raised by a provider when model instantiation fails for a recoverable
    reason (missing API key, GGUF download failed, Ollama daemon down…).
    Callers typically catch this and fall back to a safer provider."""


@dataclass(frozen=True)
class ModelCard:
    """Declarative description of a single model variant.

    A provider may offer several cards (e.g. Alia Q4_K_M, Q5_K_M, Q8_0); the
    `catalog.py` module exposes the SDK defaults but consumers can mint
    their own ModelCard instances and feed them to a provider directly.
    """

    provider: str
    """Canonical provider id this card belongs to (`alia`, `hypernova`,
    `cloud`, `ollama`)."""

    name: str
    """Human-readable display name, used by the dashboard and CLI."""

    description: str
    """One-paragraph elevator pitch — what makes this model interesting."""

    license: str
    """SPDX-style license id (`Apache-2.0`, `MIT`, `proprietary`, …)."""

    languages: Tuple[str, ...] = ()
    """ISO 639-1 codes the model is known to handle well. Empty tuple = no
    formal evaluation (treat as English-only)."""

    # --- Local GGUF specifics (Alia, Hypernova, future llama.cpp models) ---
    repo_id: Optional[str] = None
    filename: Optional[str] = None
    size_gb: Optional[float] = None
    recommended_vram_gb: Optional[float] = None

    # --- Cloud / API specifics (Mistral, future CompactifAI API, OpenAI…) ---
    api_model: Optional[str] = None
    api_base_url: Optional[str] = None

    # --- Runtime hints ---
    requires_gpu: bool = False
    cloud: bool = False

    # --- Free-form extras (n_ctx overrides, special tokens, etc.) ----------
    extras: dict = field(default_factory=dict)

    def short_label(self) -> str:
        """Compact one-liner used in logs."""
        suffix = " (cloud)" if self.cloud else ""
        return f"{self.provider}/{self.name}{suffix}"


class LLMProvider(Protocol):
    """Factory protocol for LLM backends.

    Implementations live under `venturalitica.llm.providers.<name>`.
    A provider knows how to:

    - Identify itself (`name`, `aliases`)
    - Describe its default model (`default_card`)
    - Produce a LangChain `BaseChatModel` instance (`create_chat_model`)

    Providers MUST NOT raise from `__init__`; construction is cheap. All
    expensive work (HF downloads, daemon contact, API calls) goes inside
    `create_chat_model` so callers can swap providers without paying the
    instantiation cost up-front.
    """

    name: str
    aliases: Tuple[str, ...]
    default_card: ModelCard

    def create_chat_model(self, **opts: Any) -> "BaseChatModel":
        """Instantiate the underlying LangChain chat model.

        Raises `ProviderError` (or any subclass) on recoverable failures;
        callers catch and fall back to the Ollama provider by default.
        """
        ...
