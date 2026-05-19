"""Tests for the concrete provider implementations under venturalitica.llm.providers."""

from unittest.mock import patch

import pytest

from venturalitica.llm import (
    AliaProvider,
    HypernovaProvider,
    MistralCloudProvider,
    OllamaProvider,
    ProviderError,
)


# ---------------------------------------------------------------------------
# GGUF providers — Alia + Hypernova
# ---------------------------------------------------------------------------

@patch("venturalitica.llm._gguf.ChatLlamaCpp", create=True)
@patch("venturalitica.llm._gguf.hf_hub_download", create=True, return_value="/tmp/alia.gguf")
def test_alia_provider_downloads_and_wraps_in_llamacpp(mock_download, mock_llama):
    provider = AliaProvider()
    llm = provider.create_chat_model()
    mock_download.assert_called_once()
    assert llm is mock_llama.return_value
    # default opts include n_ctx=16384 and n_gpu_layers=-1
    _, kwargs = mock_llama.call_args
    assert kwargs.get("n_ctx") == 16384
    assert kwargs.get("n_gpu_layers") == -1


@patch("venturalitica.llm._gguf.ChatLlamaCpp", create=True)
@patch("venturalitica.llm._gguf.hf_hub_download", create=True, return_value="/tmp/hyper.gguf")
def test_hypernova_provider_downloads_and_wraps_in_llamacpp(mock_download, mock_llama):
    provider = HypernovaProvider()
    llm = provider.create_chat_model()
    mock_download.assert_called_once()
    assert llm is mock_llama.return_value


@patch("venturalitica.llm._gguf.ChatLlamaCpp", create=True)
@patch("venturalitica.llm._gguf.hf_hub_download", create=True, return_value="/tmp/alia.gguf")
def test_gguf_provider_overrides_passed_through_to_llamacpp(mock_download, mock_llama):
    """Callers can override n_ctx, temperature, etc. via create_chat_model(**opts)."""
    AliaProvider().create_chat_model(n_ctx=4096, temperature=0.7)
    _, kwargs = mock_llama.call_args
    assert kwargs.get("n_ctx") == 4096
    assert kwargs.get("temperature") == 0.7


@patch("venturalitica.llm._gguf.ChatLlamaCpp", create=True)  # bypass the missing-extra guard
@patch("venturalitica.llm._gguf.hf_hub_download", create=True, side_effect=RuntimeError("HF 503"))
def test_gguf_provider_raises_provider_error_on_download_failure(mock_download, _mock_llama):
    with pytest.raises(ProviderError) as exc:
        AliaProvider().create_chat_model()
    assert "Failed to download" in str(exc.value)


def test_gguf_provider_rejects_card_missing_repo_id():
    """A ModelCard without repo_id/filename can't drive the GGUF loader."""
    from venturalitica.llm import ModelCard
    bad_card = ModelCard(
        provider="alia",
        name="empty",
        description="no GGUF info",
        license="Apache-2.0",
    )
    with pytest.raises(ProviderError) as exc:
        AliaProvider(card=bad_card).create_chat_model()
    assert "missing repo_id" in str(exc.value)


def test_gguf_provider_raises_when_hf_hub_extra_is_missing(monkeypatch):
    """If huggingface_hub isn't installed, the loader must fail loudly with
    install guidance — not a confusing AttributeError further down."""
    import venturalitica.llm._gguf as gguf_module
    monkeypatch.setattr(gguf_module, "hf_hub_download", None)
    monkeypatch.setattr(gguf_module, "ChatLlamaCpp", object())  # truthy, isolate the hf check
    with pytest.raises(ProviderError) as exc:
        AliaProvider().create_chat_model()
    assert "venturalitica[agentic]" in str(exc.value)


def test_gguf_provider_wraps_llamacpp_load_failure(monkeypatch):
    """llama.cpp blows up on a corrupt GGUF → ProviderError with context."""
    import venturalitica.llm._gguf as gguf_module
    monkeypatch.setattr(gguf_module, "hf_hub_download", lambda **kw: "/tmp/x.gguf")

    def _boom(**kw):
        raise RuntimeError("invalid magic")

    monkeypatch.setattr(gguf_module, "ChatLlamaCpp", _boom)
    with pytest.raises(ProviderError) as exc:
        AliaProvider().create_chat_model()
    assert "llama.cpp failed to load" in str(exc.value)


def test_alia_provider_aliases_include_legacy_transformers():
    assert "alia" in AliaProvider.aliases
    assert "transformers" in AliaProvider.aliases  # back-compat
    assert "bsc" in AliaProvider.aliases


def test_hypernova_provider_aliases_include_multiverse():
    assert "hypernova" in HypernovaProvider.aliases
    assert "multiverse" in HypernovaProvider.aliases
    assert "compactifai-local" in HypernovaProvider.aliases


# ---------------------------------------------------------------------------
# MistralCloudProvider
# ---------------------------------------------------------------------------

@patch("venturalitica.llm.providers.mistral.ChatMistralAI", create=True)
def test_mistral_provider_passes_api_key_and_model_to_chatmistral(mock_mistral):
    provider = MistralCloudProvider(api_key="sk-explicit")
    llm = provider.create_chat_model()
    assert llm is mock_mistral.return_value
    _, kwargs = mock_mistral.call_args
    assert kwargs.get("api_key") == "sk-explicit"
    assert kwargs.get("model") == "magistral-medium-latest"
    assert kwargs.get("max_retries") == 3


def test_mistral_provider_raises_provider_error_without_api_key(monkeypatch):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    provider = MistralCloudProvider(api_key=None)
    with pytest.raises(ProviderError) as exc:
        provider.create_chat_model()
    assert "MISTRAL_API_KEY" in str(exc.value)


def test_mistral_provider_reads_env_var_when_no_explicit_key(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "sk-from-env")
    provider = MistralCloudProvider()
    assert provider.api_key == "sk-from-env"


def test_mistral_provider_raises_when_extra_is_missing(monkeypatch):
    """If langchain-mistralai isn't installed, fall back to install guidance."""
    import venturalitica.llm.providers.mistral as mistral_module
    monkeypatch.setattr(mistral_module, "ChatMistralAI", None)
    provider = MistralCloudProvider(api_key="sk-x")
    with pytest.raises(ProviderError) as exc:
        provider.create_chat_model()
    assert "langchain-mistralai" in str(exc.value)


def test_mistral_provider_wraps_chatmistral_init_failure(monkeypatch):
    """If ChatMistralAI itself raises (bad model name, network…), surface
    a ProviderError with the model id in the message for debugging."""
    import venturalitica.llm.providers.mistral as mistral_module

    def _boom(**kw):
        raise RuntimeError("503 from API")

    monkeypatch.setattr(mistral_module, "ChatMistralAI", _boom)
    provider = MistralCloudProvider(api_key="sk-x")
    with pytest.raises(ProviderError) as exc:
        provider.create_chat_model()
    assert "ChatMistralAI failed" in str(exc.value)
    assert "magistral-medium-latest" in str(exc.value)


# ---------------------------------------------------------------------------
# OllamaProvider
# ---------------------------------------------------------------------------

@patch("venturalitica.llm.providers.ollama.ChatOllama", create=True)
def test_ollama_provider_default_uses_mistral_tag(mock_ollama):
    provider = OllamaProvider()
    llm = provider.create_chat_model()
    assert llm is mock_ollama.return_value
    _, kwargs = mock_ollama.call_args
    assert kwargs.get("model") == "mistral"
    assert kwargs.get("temperature") == 0.1
    assert provider.resolved_model == "mistral"


@patch("venturalitica.llm.providers.ollama.ChatOllama", create=True)
def test_ollama_provider_accepts_explicit_model_name(mock_ollama):
    provider = OllamaProvider(model_name="qwen2.5")
    provider.create_chat_model()
    _, kwargs = mock_ollama.call_args
    assert kwargs.get("model") == "qwen2.5"


@patch("venturalitica.llm.providers.ollama.ChatOllama", create=True)
def test_ollama_provider_ignores_hf_style_slashed_names(mock_ollama):
    """`meta-llama/Llama-3.1` is a HuggingFace id, not an Ollama tag —
    fall back to the card default."""
    provider = OllamaProvider(model_name="meta-llama/Llama-3.1-8B")
    assert provider.resolved_model == "mistral"
    provider.create_chat_model()
    _, kwargs = mock_ollama.call_args
    assert kwargs.get("model") == "mistral"


def test_ollama_provider_raises_when_extra_is_missing(monkeypatch):
    """If langchain-ollama isn't installed, surface install guidance."""
    import venturalitica.llm.providers.ollama as ollama_module
    monkeypatch.setattr(ollama_module, "ChatOllama", None)
    with pytest.raises(ProviderError) as exc:
        OllamaProvider().create_chat_model()
    assert "langchain-ollama" in str(exc.value)
