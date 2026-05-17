"""Default `ModelCard` instances exposed by the SDK.

Each provider has exactly one default card here. Users who want to swap
quantizations or point at a community-quanted mirror set the corresponding
`VENTURALITICA_<PROVIDER>_REPO` / `VENTURALITICA_<PROVIDER>_FILE` env vars,
without touching SDK code.

Adding a new model to the catalogue: append a `ModelCard(...)` and reference
it from the matching `providers/<name>.py`."""

from __future__ import annotations

import os

from .base import ModelCard


# ---------------------------------------------------------------------------
# ALIA — Barcelona Supercomputing Center
#
# ALIA-40b-instruct-2601 is the January-2026 instruction-tuned successor to
# the 2512 model previously hardcoded in the SDK. We default to the
# `mradermacher` Q4_K_M GGUF mirror (22.9 GB) because BSC only publishes a
# Q8_0 quant directly (40 GB), which is impractical on most workstations.
# Set `VENTURALITICA_ALIA_REPO` + `VENTURALITICA_ALIA_FILE` to override.
# ---------------------------------------------------------------------------
ALIA_DEFAULT = ModelCard(
    provider="alia",
    name="ALIA-40b-instruct-2601 (Q4_K_M)",
    description=(
        "Barcelona Supercomputing Center's 40B multilingual model. "
        "Trained on MareNostrum 5 across 35 European languages with Spain's "
        "four co-official languages (Spanish, Catalan, Basque, Galician) "
        "oversampled 2x. The most advanced open European foundational model "
        "for Spanish-language regulatory writing."
    ),
    license="Apache-2.0",
    languages=("es", "ca", "eu", "gl", "en", "pt", "fr", "de", "it"),
    repo_id=os.getenv(
        "VENTURALITICA_ALIA_REPO", "mradermacher/ALIA-40b-instruct-2601-GGUF"
    ),
    filename=os.getenv(
        "VENTURALITICA_ALIA_FILE", "ALIA-40b-instruct-2601.Q4_K_M.gguf"
    ),
    size_gb=22.9,
    recommended_vram_gb=24.0,
    requires_gpu=False,  # runs on CPU with patience; GPU offload improves throughput
    cloud=False,
)


# ---------------------------------------------------------------------------
# Hypernova — Multiverse Computing (CompactifAI)
#
# Quantum-inspired tensor-network compression of OpenAI's gpt-oss-120b down
# to 60B parameters with ~2-3% accuracy delta (Apache 2.0, same as base).
# Strong reasoning + native tool calling; English-primary. Sits next to
# Alia as the second EU-grown local option with a clear narrative for
# Basque/Spanish customers (Multiverse is San Sebastián).
# ---------------------------------------------------------------------------
HYPERNOVA_DEFAULT = ModelCard(
    provider="hypernova",
    name="Hypernova-60B-2602 (CompactifAI-compressed gpt-oss-120b)",
    description=(
        "Multiverse Computing's quantum-inspired CompactifAI compression of "
        "OpenAI gpt-oss-120b. 60B parameters with retained reasoning, "
        "function calling, and structured-output capabilities. Same Apache "
        "2.0 license as the base model."
    ),
    license="Apache-2.0",
    languages=("en",),
    repo_id=os.getenv(
        "VENTURALITICA_HYPERNOVA_REPO",
        "MultiverseComputingCAI/Hypernova-60B-2602-GGUF",
    ),
    filename=os.getenv(
        "VENTURALITICA_HYPERNOVA_FILE", "Hypernova-60B-2602-GGUF.gguf"
    ),
    size_gb=31.87,
    recommended_vram_gb=36.0,
    requires_gpu=False,
    cloud=False,
)


# ---------------------------------------------------------------------------
# Mistral — Magistral (cloud, paid)
#
# The frontier-grade option. Requires MISTRAL_API_KEY. Default model can be
# overridden with VENTURALITICA_MISTRAL_MODEL.
# ---------------------------------------------------------------------------
MISTRAL_DEFAULT = ModelCard(
    provider="cloud",
    name="Magistral medium (Mistral AI)",
    description=(
        "Mistral AI's hosted Magistral reasoning model. Frontier quality, "
        "fastest time-to-first-token. Requires MISTRAL_API_KEY."
    ),
    license="proprietary",
    languages=("en", "fr", "es", "de", "it", "pt"),
    api_model=os.getenv("VENTURALITICA_MISTRAL_MODEL", "magistral-medium-latest"),
    api_base_url=None,  # langchain-mistralai uses the SDK default base URL
    cloud=True,
)


# ---------------------------------------------------------------------------
# Ollama — local generic fallback (whatever the user has pulled)
# ---------------------------------------------------------------------------
OLLAMA_DEFAULT = ModelCard(
    provider="ollama",
    name="Local Ollama daemon (mistral)",
    description=(
        "Local Ollama daemon — whichever model the user has pulled. The "
        "lightweight, always-on fallback. Defaults to `mistral` if no "
        "explicit model name is provided."
    ),
    license="model-dependent",
    languages=(),
    api_model=os.getenv("VENTURALITICA_OLLAMA_MODEL", "mistral"),
    cloud=False,
)


# Convenience for the dashboard / CLI listing.
DEFAULT_CARDS = (ALIA_DEFAULT, HYPERNOVA_DEFAULT, MISTRAL_DEFAULT, OLLAMA_DEFAULT)
