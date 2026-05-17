"""Provider registry — turn a user-facing name into a `LLMProvider` instance.

`resolve_provider("transformers")` → `AliaProvider()` (back-compat).
`resolve_provider("hypernova")` → `HypernovaProvider()`.
`resolve_provider("auto")` → `MistralCloudProvider()` when `VENTURALITICA_LLM_PRO=true`
and a Mistral API key is available; otherwise `OllamaProvider()`.

Aliases live in a single map so adding `bsc`, `multiverse`, or a future
`compactifai-cloud` is a one-line change."""

from __future__ import annotations

import os
from typing import Dict, Optional, Tuple, Type

from .base import LLMProvider
from .providers import (
    AliaProvider,
    HypernovaProvider,
    MistralCloudProvider,
    OllamaProvider,
)

# Canonical name → provider class. Keep this sorted by capability tier:
# local-curated (alia/hypernova) → cloud (mistral) → local-generic (ollama).
PROVIDERS: Dict[str, Type[LLMProvider]] = {
    "alia": AliaProvider,
    "hypernova": HypernovaProvider,
    "cloud": MistralCloudProvider,
    "ollama": OllamaProvider,
}

# user-facing alias → canonical provider id.
# Order doesn't matter; lookup is O(1).
ALIASES: Dict[str, str] = {}
for _cls in PROVIDERS.values():
    for _alias in _cls.aliases:
        ALIASES[_alias] = _cls.name


def normalize_provider_name(provider: Optional[str]) -> str:
    """Resolve aliases to canonical provider ids.

    Returns `"auto"` for empty / falsy input so the caller knows to apply
    auto-selection rules. Unknown names pass through unchanged so the
    caller can decide whether to fall back or fail loudly.
    """
    if not provider:
        return "auto"
    key = provider.lower().strip()
    return ALIASES.get(key, key)


def _auto_select(api_key: Optional[str]) -> str:
    """`auto` provider strategy: prefer cloud when the user opted in to
    PRO mode AND has a key; otherwise stay local with Ollama. The Alia and
    Hypernova local-GGUF providers are NEVER auto-selected — they're heavy
    and explicit opt-in is the right UX."""
    if os.getenv("VENTURALITICA_LLM_PRO", "false").lower() == "true" and (
        api_key or os.getenv("MISTRAL_API_KEY")
    ):
        return "cloud"
    return "ollama"


def resolve_provider(
    provider: Optional[str] = "auto",
    *,
    api_key: Optional[str] = None,
    model_hint: Optional[str] = None,
) -> LLMProvider:
    """Resolve a user-facing provider string to an instantiated `LLMProvider`.

    Args:
        provider: User-facing name (`"alia"`, `"transformers"`, `"hypernova"`,
            `"cloud"`, `"ollama"`, `"auto"`, or any alias). `None` and empty
            string are treated as `"auto"`.
        api_key: Override for the cloud provider's API key (falls back to
            the `MISTRAL_API_KEY` env var inside `MistralCloudProvider`).
        model_hint: Forwarded to `OllamaProvider` so users can pick a
            non-default local tag without changing env vars.

    Returns:
        An instantiated provider. Cheap to call — the heavy lifting happens
        inside `create_chat_model()`.
    """
    canonical = normalize_provider_name(provider)
    if canonical == "auto":
        canonical = _auto_select(api_key)

    cls = PROVIDERS.get(canonical)
    if cls is None:
        # Unknown provider — treat as a hint for the local Ollama backend.
        return OllamaProvider(model_name=model_hint or provider)

    if cls is MistralCloudProvider:
        return cls(api_key=api_key)
    if cls is OllamaProvider:
        return cls(model_name=model_hint)
    return cls()


def list_providers() -> Tuple[Type[LLMProvider], ...]:
    """Used by the dashboard / CLI to enumerate available providers."""
    return tuple(PROVIDERS.values())
