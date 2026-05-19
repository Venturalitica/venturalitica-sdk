"""Shared GGUF loader used by the local-GGUF providers (Alia, Hypernova).

Centralising the `huggingface_hub.hf_hub_download` + `ChatLlamaCpp` wiring
keeps each provider file trivial and ensures any future tuning (GPU
offloading, context window, batch size, retry policy) lands once.

The optional deps (`huggingface_hub`, `langchain_community.chat_models`) are
bound at module import time inside a try/except so they can be mocked at
the module level by `unittest.mock.patch("venturalitica.llm._gguf.<symbol>")`
in tests — and so the SDK base install (without the `[agentic]` extra)
imports the module cleanly and only fails when a GGUF load is actually
attempted."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import ModelCard, ProviderError

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


# Pre-bind the optional deps at module level so mocks can patch them.
try:  # pragma: no cover — exercised in environments with [agentic] installed
    from huggingface_hub import hf_hub_download
except ImportError:  # pragma: no cover
    hf_hub_download = None  # type: ignore[assignment]

try:  # pragma: no cover
    from langchain_community.chat_models import ChatLlamaCpp
except ImportError:  # pragma: no cover
    ChatLlamaCpp = None  # type: ignore[assignment]


# Defaults applied unless the caller overrides via opts. Tuned for a typical
# RTX 4090 / single-GPU workstation; users with less VRAM should drop
# `n_gpu_layers` to a positive integer (number of layers offloaded to GPU).
_DEFAULTS: dict = {
    "temperature": 0.1,
    "max_tokens": 4096,
    "top_p": 1,
    "n_ctx": 16384,
    "n_gpu_layers": -1,  # `-1` = offload everything; ChatLlamaCpp auto-falls back to CPU
    "n_batch": 512,
    "verbose": False,
}


def load_gguf_chat_model(card: ModelCard, **overrides: Any) -> "BaseChatModel":
    """Download (cached) the GGUF named by `card` and wrap it in ChatLlamaCpp.

    Raises:
        ProviderError: if the optional `[agentic]` extra isn't installed,
        or if the model can't be downloaded, or if llama.cpp can't load it.
        Callers typically catch this and fall back to Ollama.
    """
    if not card.repo_id or not card.filename:
        raise ProviderError(
            f"{card.short_label()} is missing repo_id/filename — not a GGUF card."
        )

    if hf_hub_download is None or ChatLlamaCpp is None:
        raise ProviderError(
            "Local GGUF providers require huggingface_hub + langchain_community. "
            "Install with: pip install 'venturalitica[agentic]'"
        )

    try:
        model_path = hf_hub_download(repo_id=card.repo_id, filename=card.filename)
    except Exception as exc:
        raise ProviderError(
            f"Failed to download {card.repo_id}/{card.filename}: {exc}"
        ) from exc

    settings = {**_DEFAULTS, **overrides}
    try:
        return ChatLlamaCpp(model_path=model_path, **settings)
    except Exception as exc:
        raise ProviderError(
            f"llama.cpp failed to load {card.short_label()}: {exc}"
        ) from exc
