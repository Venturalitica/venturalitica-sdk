"""ALIA provider — Barcelona Supercomputing Center's 40B multilingual model."""

from __future__ import annotations

from typing import Any, Tuple

from ..base import ModelCard
from ..catalog import ALIA_DEFAULT
from .._gguf import load_gguf_chat_model


class AliaProvider:
    """Loads BSC's ALIA-40b-instruct GGUF via huggingface_hub + ChatLlamaCpp."""

    name: str = "alia"
    aliases: Tuple[str, ...] = ("alia", "transformers", "bsc")
    default_card: ModelCard = ALIA_DEFAULT

    def __init__(self, card: ModelCard | None = None) -> None:
        self.card = card or self.default_card

    def create_chat_model(self, **opts: Any):
        return load_gguf_chat_model(self.card, **opts)
