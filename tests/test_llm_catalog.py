"""Tests for venturalitica.llm.catalog — default ModelCard shape + env overrides."""

import importlib

import pytest

from venturalitica.llm import (
    ALIA_DEFAULT,
    DEFAULT_CARDS,
    HYPERNOVA_DEFAULT,
    MISTRAL_DEFAULT,
    OLLAMA_DEFAULT,
    ModelCard,
)


def test_default_cards_tuple_includes_every_provider():
    providers = {c.provider for c in DEFAULT_CARDS}
    assert providers == {"alia", "hypernova", "cloud", "ollama"}


def test_alia_default_is_q4_k_m_quant():
    """The SDK default points to the community Q4_K_M quant (22.9 GB)
    instead of BSC's Q8_0 (40 GB) so the model fits a typical workstation."""
    assert ALIA_DEFAULT.repo_id == "mradermacher/ALIA-40b-instruct-2601-GGUF"
    assert ALIA_DEFAULT.filename == "ALIA-40b-instruct-2601.Q4_K_M.gguf"
    assert ALIA_DEFAULT.size_gb == pytest.approx(22.9)
    assert ALIA_DEFAULT.license == "Apache-2.0"
    # ALIA's selling point is multilingual ES-family coverage.
    for lang in ("es", "ca", "eu", "gl"):
        assert lang in ALIA_DEFAULT.languages


def test_hypernova_default_points_to_multiverse_gguf():
    assert HYPERNOVA_DEFAULT.repo_id == \
        "MultiverseComputingCAI/Hypernova-60B-2602-GGUF"
    assert HYPERNOVA_DEFAULT.filename == "Hypernova-60B-2602-GGUF.gguf"
    assert HYPERNOVA_DEFAULT.size_gb == pytest.approx(31.87)
    assert HYPERNOVA_DEFAULT.license == "Apache-2.0"
    assert HYPERNOVA_DEFAULT.languages == ("en",)


def test_mistral_default_is_cloud_with_magistral_target_model():
    assert MISTRAL_DEFAULT.cloud is True
    assert MISTRAL_DEFAULT.api_model == "magistral-medium-latest"
    assert MISTRAL_DEFAULT.repo_id is None  # not a GGUF card


def test_ollama_default_is_mistral_tag():
    assert OLLAMA_DEFAULT.provider == "ollama"
    assert OLLAMA_DEFAULT.api_model == "mistral"


# ---------------------------------------------------------------------------
# ModelCard helpers
# ---------------------------------------------------------------------------

def test_short_label_marks_cloud_provider():
    assert "(cloud)" in MISTRAL_DEFAULT.short_label()
    assert "(cloud)" not in ALIA_DEFAULT.short_label()
    assert "(cloud)" not in HYPERNOVA_DEFAULT.short_label()


def test_model_card_is_frozen():
    """Cards are immutable so callers can safely cache them."""
    with pytest.raises((AttributeError, TypeError)):
        ALIA_DEFAULT.size_gb = 99  # type: ignore[misc]


def test_model_card_round_trips_through_constructor():
    """Sanity: every field round-trips."""
    custom = ModelCard(
        provider="alia",
        name="Custom Alia Q5",
        description="user-supplied",
        license="Apache-2.0",
        languages=("es",),
        repo_id="someone/ALIA-Q5",
        filename="alia.q5.gguf",
        size_gb=27.0,
    )
    assert custom.repo_id == "someone/ALIA-Q5"
    assert custom.languages == ("es",)
    assert custom.extras == {}


# ---------------------------------------------------------------------------
# Env-var overrides on the default cards
# ---------------------------------------------------------------------------

def test_env_var_overrides_alia_repo_and_file(monkeypatch):
    monkeypatch.setenv("VENTURALITICA_ALIA_REPO", "my-org/ALIA-mirror")
    monkeypatch.setenv("VENTURALITICA_ALIA_FILE", "ALIA.custom.gguf")
    # The catalog reads env vars at import time — reload the module to pick
    # the override up.
    import venturalitica.llm.catalog as catalog
    importlib.reload(catalog)
    assert catalog.ALIA_DEFAULT.repo_id == "my-org/ALIA-mirror"
    assert catalog.ALIA_DEFAULT.filename == "ALIA.custom.gguf"

    # Clean reload so subsequent tests see the SDK defaults again.
    monkeypatch.delenv("VENTURALITICA_ALIA_REPO", raising=False)
    monkeypatch.delenv("VENTURALITICA_ALIA_FILE", raising=False)
    importlib.reload(catalog)
    # Re-import the symbols other tests bind to.
    import venturalitica.llm as llm
    importlib.reload(llm)
