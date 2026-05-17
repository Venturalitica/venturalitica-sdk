"""Tests for venturalitica.llm.registry — provider lookup + alias resolution."""

import os
from unittest.mock import patch

import pytest

from venturalitica.llm import (
    ALIASES,
    PROVIDERS,
    AliaProvider,
    HypernovaProvider,
    MistralCloudProvider,
    OllamaProvider,
    list_providers,
    normalize_provider_name,
    resolve_provider,
)


# ---------------------------------------------------------------------------
# normalize_provider_name
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "alias, canonical",
    [
        ("alia", "alia"),
        ("transformers", "alia"),
        ("bsc", "alia"),
        ("hypernova", "hypernova"),
        ("multiverse", "hypernova"),
        ("compactifai-local", "hypernova"),
        ("cloud", "cloud"),
        ("mistral", "cloud"),
        ("ollama", "ollama"),
        ("local", "ollama"),
        ("auto", "auto"),
        ("", "auto"),
        (None, "auto"),
        ("  ALIA  ", "alia"),
        ("HYPERNOVA", "hypernova"),
        # Unknown names pass through (caller decides whether to fall back)
        ("future-provider", "future-provider"),
    ],
)
def test_normalize_provider_name(alias, canonical):
    assert normalize_provider_name(alias) == canonical


def test_aliases_map_covers_every_provider():
    """Every provider's `aliases` tuple must be reflected in the global
    ALIASES map (and vice-versa). Catches drift when a new alias is added
    to a provider class but not registered."""
    expected = {}
    for cls in PROVIDERS.values():
        for a in cls.aliases:
            expected[a] = cls.name
    assert ALIASES == expected


# ---------------------------------------------------------------------------
# resolve_provider — explicit names
# ---------------------------------------------------------------------------

def test_resolve_alia_returns_alia_provider():
    assert isinstance(resolve_provider("alia"), AliaProvider)
    assert isinstance(resolve_provider("transformers"), AliaProvider)  # alias
    assert isinstance(resolve_provider("bsc"), AliaProvider)  # alias


def test_resolve_hypernova_returns_hypernova_provider():
    assert isinstance(resolve_provider("hypernova"), HypernovaProvider)
    assert isinstance(resolve_provider("multiverse"), HypernovaProvider)
    assert isinstance(resolve_provider("compactifai-local"), HypernovaProvider)


def test_resolve_cloud_returns_mistral_provider_with_api_key():
    prov = resolve_provider("cloud", api_key="sk-test")
    assert isinstance(prov, MistralCloudProvider)
    assert prov.api_key == "sk-test"


def test_resolve_ollama_with_model_hint_propagates_to_resolved_model():
    prov = resolve_provider("ollama", model_hint="qwen2.5")
    assert isinstance(prov, OllamaProvider)
    assert prov.resolved_model == "qwen2.5"


def test_resolve_unknown_provider_falls_back_to_ollama_with_hint():
    prov = resolve_provider("foobar", model_hint="qwen2.5")
    assert isinstance(prov, OllamaProvider)
    assert prov.resolved_model == "qwen2.5"


# ---------------------------------------------------------------------------
# resolve_provider — auto strategy
# ---------------------------------------------------------------------------

@patch.dict(os.environ, {}, clear=True)
def test_resolve_auto_without_pro_flag_picks_ollama():
    """`auto` stays local by default — heavy local GGUFs are explicit opt-in."""
    assert isinstance(resolve_provider("auto"), OllamaProvider)
    assert isinstance(resolve_provider(None), OllamaProvider)
    assert isinstance(resolve_provider(""), OllamaProvider)


@patch.dict(
    os.environ,
    {"VENTURALITICA_LLM_PRO": "true", "MISTRAL_API_KEY": "sk-from-env"},
)
def test_resolve_auto_with_pro_flag_and_env_key_picks_cloud():
    prov = resolve_provider("auto")
    assert isinstance(prov, MistralCloudProvider)
    # env var was the source — api_key passthrough None means resolver fell
    # back to MISTRAL_API_KEY env var inside MistralCloudProvider.__init__.
    assert prov.api_key == "sk-from-env"


@patch.dict(os.environ, {"VENTURALITICA_LLM_PRO": "true"}, clear=True)
def test_resolve_auto_with_pro_flag_no_key_stays_local():
    """PRO flag without any API key still picks Ollama (not Mistral with None)."""
    assert isinstance(resolve_provider("auto"), OllamaProvider)


@patch.dict(os.environ, {"VENTURALITICA_LLM_PRO": "true"}, clear=True)
def test_resolve_auto_with_pro_flag_and_explicit_api_key_picks_cloud():
    """Explicit api_key kwarg satisfies the auto-select PRO condition even
    without the MISTRAL_API_KEY env var."""
    prov = resolve_provider("auto", api_key="sk-explicit")
    assert isinstance(prov, MistralCloudProvider)
    assert prov.api_key == "sk-explicit"


# ---------------------------------------------------------------------------
# list_providers
# ---------------------------------------------------------------------------

def test_list_providers_returns_all_registered_classes():
    classes = list_providers()
    assert AliaProvider in classes
    assert HypernovaProvider in classes
    assert MistralCloudProvider in classes
    assert OllamaProvider in classes
    assert len(classes) == 4


def test_provider_names_are_unique_and_match_registry_keys():
    for name, cls in PROVIDERS.items():
        assert cls.name == name, f"PROVIDERS[{name!r}] points to class with name={cls.name!r}"
