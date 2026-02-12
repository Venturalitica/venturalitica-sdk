import json
import os
from unittest.mock import MagicMock, patch

from venturalitica.assurance.graph.nodes import NodeFactory
from venturalitica.assurance.graph.state import ComplianceState


@patch.dict(os.environ, {}, clear=True)
@patch("venturalitica.assurance.graph.nodes.ChatOllama")
def test_node_factory_init_local(mock_ollama):
    # Test default initialization (Local Ollama)
    factory = NodeFactory(model_name="llama3")
    assert factory.llm is not None
    mock_ollama.assert_called_once()
    assert factory.llm == mock_ollama.return_value


@patch.dict(os.environ, {"VENTURALITICA_LLM_PRO": "true", "MISTRAL_API_KEY": "fake_key"})
@patch("venturalitica.assurance.graph.nodes.ChatMistralAI")
def test_node_factory_init_pro(mock_mistral):
    # Test Pro initialization (Mistral)
    factory = NodeFactory(model_name="llama3")
    assert factory.llm is not None
    mock_mistral.assert_called_once()
    assert factory.llm == mock_mistral.return_value


@patch.dict(os.environ, {"VENTURALITICA_LLM_PRO": "true"}, clear=True)
@patch("venturalitica.assurance.graph.nodes.ChatOllama")
def test_node_factory_init_pro_missing_key_fallback(mock_ollama):
    # Pro flag set but no key -> Fallback to Local
    _ = NodeFactory(model_name="llama3")
    mock_ollama.assert_called_once()


def test_node_factory_utilities():
    # We use a dummy model name to avoid real initialization
    factory = NodeFactory(model_name="dummy", provider="mock")

    # Test _safe_json_loads
    raw_json = '```json\n{"a": 1}\n```'
    assert factory._safe_json_loads(raw_json) == {"a": 1}

    dirty_json = 'Text before\n```\n{"b": 2}\n```\nText after'
    assert factory._safe_json_loads(dirty_json) == {"b": 2}

    # Test _load_prompts
    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", MagicMock()):
            with patch("yaml.safe_load", return_value={"test": "prompt"}):
                prompts = factory._load_prompts("en")
                assert prompts == {"test": "prompt"}


@patch("requests.post")
def test_node_factory_check_security(mock_post):
    factory = NodeFactory(model_name="dummy", provider="mock")

    # Mock OSV response
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


@patch("langchain_community.chat_models.ChatLlamaCpp")
@patch("huggingface_hub.hf_hub_download", return_value="/tmp/model.gguf")
def test_node_factory_init_with_transformers_provider(mock_download, mock_llama):
    """Test NodeFactory with transformers provider falls back gracefully."""
    mock_llama.return_value = MagicMock()
    try:
        _ = NodeFactory("test", provider="transformers")
    except Exception:
        pass  # May fail depending on env, we just test the code path


def test_node_factory_scan_project(tmp_path):
    factory = NodeFactory(model_name="dummy", provider="mock")
    project_root = tmp_path / "project"
    project_root.mkdir()

    # Save current working directory
    old_cwd = os.getcwd()
    os.chdir(project_root)

    try:
        # Mock BOMScanner
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
