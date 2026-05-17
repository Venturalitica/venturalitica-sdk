"""Tests for the agentic compliance-graph node factory.

After the LLM-package refactor, NodeFactory delegates all provider routing
to `venturalitica.llm.resolve_provider`. These tests focus on the thin
glue layer that lives in `nodes.py` (provider lookup + fallback to Ollama
on ProviderError). Provider-level behaviour is covered by `test_llm_*.py`.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("langchain_core", reason="Requires venturalitica[agentic]")

from venturalitica.assurance.graph.nodes import NodeFactory
from venturalitica.assurance.graph.state import ComplianceState


# ---------------------------------------------------------------------------
# Default routing (provider="auto"): no PRO flag → Ollama fallback
# ---------------------------------------------------------------------------

@patch.dict(os.environ, {}, clear=True)
@patch("venturalitica.llm.providers.ollama.ChatOllama")
def test_node_factory_auto_falls_back_to_ollama(mock_ollama):
    factory = NodeFactory(model_name="llama3")
    assert factory.llm is mock_ollama.return_value
    mock_ollama.assert_called_once()


@patch.dict(
    os.environ, {"VENTURALITICA_LLM_PRO": "true", "MISTRAL_API_KEY": "fake_key"}
)
@patch("venturalitica.llm.providers.mistral.ChatMistralAI")
def test_node_factory_auto_with_pro_flag_routes_to_mistral(mock_mistral):
    factory = NodeFactory(model_name="llama3")
    assert factory.llm is mock_mistral.return_value
    mock_mistral.assert_called_once()


@patch.dict(os.environ, {"VENTURALITICA_LLM_PRO": "true"}, clear=True)
@patch("venturalitica.llm.providers.ollama.ChatOllama")
def test_node_factory_pro_flag_without_key_falls_back_to_ollama(mock_ollama):
    NodeFactory(model_name="llama3")
    mock_ollama.assert_called_once()


# ---------------------------------------------------------------------------
# Explicit provider names
# ---------------------------------------------------------------------------

@patch("venturalitica.llm._gguf.ChatLlamaCpp", create=True)
@patch("venturalitica.llm._gguf.hf_hub_download", create=True, return_value="/tmp/alia.gguf")
def test_node_factory_alia_loads_gguf(mock_download, mock_llama):
    """`provider="alia"` resolves to AliaProvider and downloads its default GGUF."""
    factory = NodeFactory("test", provider="alia")
    assert mock_download.called
    # repo+filename come from venturalitica.llm.catalog.ALIA_DEFAULT
    args, kwargs = mock_download.call_args
    assert kwargs.get("repo_id", args[0] if args else None) == \
        "mradermacher/ALIA-40b-instruct-2601-GGUF"
    assert kwargs.get("filename", args[1] if len(args) > 1 else None) == \
        "ALIA-40b-instruct-2601.Q4_K_M.gguf"
    assert factory.llm is mock_llama.return_value


@patch("venturalitica.llm._gguf.ChatLlamaCpp", create=True)
@patch("venturalitica.llm._gguf.hf_hub_download", create=True, return_value="/tmp/hypernova.gguf")
def test_node_factory_hypernova_loads_gguf(mock_download, mock_llama):
    """`provider="hypernova"` resolves to HypernovaProvider and downloads its GGUF."""
    factory = NodeFactory("test", provider="hypernova")
    assert mock_download.called
    args, kwargs = mock_download.call_args
    assert kwargs.get("repo_id", args[0] if args else None) == \
        "MultiverseComputingCAI/Hypernova-60B-2602-GGUF"
    assert kwargs.get("filename", args[1] if len(args) > 1 else None) == \
        "Hypernova-60B-2602-GGUF.gguf"
    assert factory.llm is mock_llama.return_value


@patch("venturalitica.llm._gguf.ChatLlamaCpp", create=True)
@patch("venturalitica.llm._gguf.hf_hub_download", create=True, return_value="/tmp/legacy.gguf")
def test_node_factory_transformers_alias_still_works(mock_download, mock_llama):
    """Legacy provider name `transformers` keeps working as an alias for `alia`."""
    factory = NodeFactory("test", provider="transformers")
    assert mock_download.called
    assert factory.llm is mock_llama.return_value


# ---------------------------------------------------------------------------
# ProviderError fallback
# ---------------------------------------------------------------------------

@patch("venturalitica.llm.providers.ollama.ChatOllama")
@patch("venturalitica.llm._gguf.hf_hub_download", create=True, side_effect=RuntimeError("HF 503"))
def test_node_factory_falls_back_to_ollama_when_gguf_download_fails(
    mock_download, mock_ollama
):
    """When the chosen provider raises ProviderError, NodeFactory falls back
    to a vanilla OllamaProvider instead of letting the pipeline crash."""
    NodeFactory("test", provider="alia")
    mock_ollama.assert_called_once()


# ---------------------------------------------------------------------------
# Utility methods (unrelated to provider routing — preserved from old suite)
# ---------------------------------------------------------------------------

def test_node_factory_utilities():
    factory = NodeFactory(model_name="dummy", provider="mock")  # unknown → ollama fallback

    raw_json = '```json\n{"a": 1}\n```'
    assert factory._safe_json_loads(raw_json) == {"a": 1}

    dirty_json = 'Text before\n```\n{"b": 2}\n```\nText after'
    assert factory._safe_json_loads(dirty_json) == {"b": 2}

    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", MagicMock()):
            with patch("yaml.safe_load", return_value={"test": "prompt"}):
                prompts = factory._load_prompts("en")
                assert prompts == {"test": "prompt"}


@patch("requests.post")
def test_node_factory_check_security(mock_post):
    factory = NodeFactory(model_name="dummy", provider="mock")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [{"vulns": [{"id": "CVE-1", "severity": [{"type": "CVSS_V3", "score": "9.5"}]}]}]
    }
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    bom = {"components": [{"name": "requests", "version": "2.25.1", "type": "library"}]}
    results = factory.check_security(bom)
    assert results["vulnerable"] is True
    assert results["issues"][0]["id"] == "CVE-1"
    assert results["issues"][0]["severity"] == "CRITICAL"


def test_node_factory_scan_project(tmp_path):
    factory = NodeFactory(model_name="dummy", provider="mock")
    project_root = tmp_path / "project"
    project_root.mkdir()

    old_cwd = os.getcwd()
    os.chdir(project_root)

    try:
        with patch(
            "venturalitica.scanner.BOMScanner.scan",
            return_value=json.dumps({"components": []}),
        ):
            with patch.object(
                factory,
                "check_security",
                return_value={"vulnerable": False, "issues": []},
            ):
                state: ComplianceState = {
                    "project_root": str(project_root),
                    "language": "en",
                }
                res = factory.scan_project(state)
                assert "bom" in res
                assert "sections" in res
                assert res["sections"]["scanner"]["status"] == "completed"
    finally:
        os.chdir(old_cwd)
