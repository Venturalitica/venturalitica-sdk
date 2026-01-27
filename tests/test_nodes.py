
import pytest
from unittest.mock import patch, MagicMock
import os
from venturalitica.graph.nodes import NodeFactory

@patch.dict(os.environ, {}, clear=True)
@patch("venturalitica.graph.nodes.ChatOllama")
def test_node_factory_init_local(mock_ollama):
    # Test default initialization (Local Ollama)
    factory = NodeFactory(model_name="llama3")
    assert factory.llm is not None
    mock_ollama.assert_called_once()
    assert factory.llm == mock_ollama.return_value

@patch.dict(os.environ, {"VENTURALITICA_LLM_PRO": "true", "MISTRAL_API_KEY": "fake_key"})
@patch("venturalitica.graph.nodes.ChatMistralAI")
def test_node_factory_init_pro(mock_mistral):
    # Test Pro initialization (Mistral)
    factory = NodeFactory(model_name="llama3")
    assert factory.llm is not None
    mock_mistral.assert_called_once()
    assert factory.llm == mock_mistral.return_value

@patch.dict(os.environ, {"VENTURALITICA_LLM_PRO": "true"}, clear=True)
@patch("venturalitica.graph.nodes.ChatOllama")
def test_node_factory_init_pro_missing_key_fallback(mock_ollama):
    # Pro flag set but no key -> Fallback to Local
    factory = NodeFactory(model_name="llama3")
    mock_ollama.assert_called_once()

# ... other methods of NodeFactory would need mocking of State and LLM invoke ...
# For now coverage of __init__ is the main target as identified in the session summary.
