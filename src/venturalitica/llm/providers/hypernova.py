"""Hypernova provider — Multiverse Computing's CompactifAI-compressed gpt-oss-120b."""

from __future__ import annotations

from typing import Any, Tuple

from ..base import ModelCard
from ..catalog import HYPERNOVA_DEFAULT
from .._gguf import load_gguf_chat_model


class HypernovaProvider:
    """Loads Multiverse's Hypernova-60B GGUF via huggingface_hub + ChatLlamaCpp."""

    name: str = "hypernova"
    aliases: Tuple[str, ...] = ("hypernova", "multiverse", "compactifai-local")
    default_card: ModelCard = HYPERNOVA_DEFAULT

    def __init__(self, card: ModelCard | None = None) -> None:
        self.card = card or self.default_card

    def create_chat_model(self, **opts: Any):
        return load_gguf_chat_model(self.card, **opts)
