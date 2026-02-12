import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from venturalitica.inference import (
    SystemDescription,
    infer_system_description,
    infer_risk_classification,
    infer_technical_documentation,
)
from venturalitica.models import TechnicalDocumentation, RiskAssessment


# ===================================================================
# EXISTING TESTS (preserved)
# ===================================================================


@patch("venturalitica.inference.NodeFactory")
@patch("venturalitica.inference.BOMScanner")
@patch("venturalitica.inference.ASTCodeScanner")
def test_infer_system_description_mock(mock_ast, mock_bom, mock_factory, tmp_path):
    # Setup mocks
    mock_bom_inst = mock_bom.return_value
    mock_bom_inst.scan.return_value = json.dumps({"components": []})

    mock_ast_inst = mock_ast.return_value
    mock_ast_inst.scan_directory.return_value = {
        "main.py": {"docstring": "Test script"}
    }

    mock_node_inst = mock_factory.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm

    mock_response = MagicMock()
    mock_response.content = json.dumps(
        {"name": "Inferred System", "intended_purpose": "Testing"}
    )
    mock_llm.invoke.return_value = mock_response
    mock_node_inst._safe_json_loads.return_value = {
        "name": "Inferred System",
        "intended_purpose": "Testing",
    }

    # Create dummy files
    (tmp_path / "README.md").write_text("Hello")

    res = infer_system_description(str(tmp_path), provider="mock")
    assert res.name == "Inferred System"


@patch("venturalitica.inference.NodeFactory")
def test_infer_risk_classification_mock(mock_factory):
    mock_node_inst = mock_factory.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm

    mock_response = MagicMock()
    mock_response.content = json.dumps(
        {"risk_level": "HIGH", "reasoning": "Test reasoning"}
    )
    mock_llm.invoke.return_value = mock_response
    mock_node_inst._safe_json_loads.return_value = {
        "risk_level": "HIGH",
        "reasoning": "Test reasoning",
    }

    sd = SystemDescription(intended_purpose="Credit Scoring", name="LoanAI")
    res = infer_risk_classification(sd, provider="mock")
    assert res.risk_level == "HIGH"


# ===================================================================
# infer_system_description – uncovered paths
# ===================================================================


@patch("venturalitica.inference.NodeFactory")
@patch("venturalitica.inference.BOMScanner")
@patch("venturalitica.inference.ASTCodeScanner")
def test_infer_system_description_bom_parse_failure(
    mock_ast, mock_bom, mock_factory, tmp_path
):
    """BOM scan returns non-JSON -> bom falls back to {}."""
    mock_bom.return_value.scan.return_value = "NOT-VALID-JSON"
    mock_ast.return_value.scan_directory.return_value = {}

    mock_node_inst = mock_factory.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm
    mock_response = MagicMock()
    mock_response.content = json.dumps({"name": "X"})
    mock_llm.invoke.return_value = mock_response
    mock_node_inst._safe_json_loads.return_value = {"name": "X"}

    res = infer_system_description(str(tmp_path), provider="mock")
    assert isinstance(res, SystemDescription)


@patch("venturalitica.inference.NodeFactory")
@patch("venturalitica.inference.BOMScanner")
@patch("venturalitica.inference.ASTCodeScanner")
def test_infer_system_description_readme_discovery(
    mock_ast, mock_bom, mock_factory, tmp_path
):
    """README discovery loop picks up readme.md (second candidate)."""
    mock_bom.return_value.scan.return_value = json.dumps({})
    mock_ast.return_value.scan_directory.return_value = {}

    mock_node_inst = mock_factory.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm
    mock_response = MagicMock()
    mock_response.content = json.dumps({"name": "WithReadme"})
    mock_llm.invoke.return_value = mock_response
    mock_node_inst._safe_json_loads.return_value = {"name": "WithReadme"}

    # Only create readme.md (second candidate in the loop)
    (tmp_path / "readme.md").write_text("# My Project\nDescription here")

    res = infer_system_description(str(tmp_path), provider="mock")
    assert isinstance(res, SystemDescription)


@patch("venturalitica.inference.NodeFactory")
@patch("venturalitica.inference.BOMScanner")
@patch("venturalitica.inference.ASTCodeScanner")
def test_infer_system_description_empty_prompt_fallback(
    mock_ast, mock_bom, mock_factory, tmp_path
):
    """When prompt file doesn't have the key, returns empty SystemDescription."""
    mock_bom.return_value.scan.return_value = json.dumps({})
    mock_ast.return_value.scan_directory.return_value = {}

    # Force the prompt path to not exist so no prompt is loaded
    with patch("venturalitica.inference.Path") as mock_path_cls:
        # Make Path behave normally for target_dir but force prompt path to not exist
        real_path = Path

        def path_side_effect(*args, **kwargs):
            p = real_path(*args, **kwargs)
            return p

        mock_path_cls.side_effect = path_side_effect
        # Instead, simply patch the yaml file to return empty
        with patch("builtins.open", side_effect=FileNotFoundError):
            # The function checks prompt_path.exists() which will be True in normal flow,
            # so we need a different approach: patch yaml to return no key
            pass

    # Simpler approach: mock the yaml content to not contain the expected key
    with patch(
        "venturalitica.inference.yaml.safe_load", return_value={"other_key": {}}
    ):
        res = infer_system_description(str(tmp_path), provider="mock")
    assert res == SystemDescription()  # empty fallback


@patch("venturalitica.inference.NodeFactory")
@patch("venturalitica.inference.BOMScanner")
@patch("venturalitica.inference.ASTCodeScanner")
def test_infer_system_description_llm_list_content(
    mock_ast, mock_bom, mock_factory, tmp_path
):
    """When LLM returns list content, it is joined."""
    mock_bom.return_value.scan.return_value = json.dumps({})
    mock_ast.return_value.scan_directory.return_value = {}

    mock_node_inst = mock_factory.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm

    # Response content is a list (some providers return this)
    mock_response = MagicMock()
    mock_response.content = ['{"name":', ' "ListJoined"}']
    mock_llm.invoke.return_value = mock_response
    mock_node_inst._safe_json_loads.return_value = {"name": "ListJoined"}

    res = infer_system_description(str(tmp_path), provider="mock")
    assert res.name == "ListJoined"


@patch("venturalitica.inference.NodeFactory")
@patch("venturalitica.inference.BOMScanner")
@patch("venturalitica.inference.ASTCodeScanner")
def test_infer_system_description_json_extraction_failure(
    mock_ast, mock_bom, mock_factory, tmp_path
):
    """When _safe_json_loads returns None, fallback to empty SystemDescription."""
    mock_bom.return_value.scan.return_value = json.dumps({})
    mock_ast.return_value.scan_directory.return_value = {}

    mock_node_inst = mock_factory.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm

    mock_response = MagicMock()
    mock_response.content = "This is not JSON at all"
    mock_llm.invoke.return_value = mock_response
    mock_node_inst._safe_json_loads.return_value = None  # extraction fails

    res = infer_system_description(str(tmp_path), provider="mock")
    assert res == SystemDescription()


@patch("venturalitica.inference.NodeFactory")
@patch("venturalitica.inference.BOMScanner")
@patch("venturalitica.inference.ASTCodeScanner")
def test_infer_system_description_exception_handler(
    mock_ast, mock_bom, mock_factory, tmp_path
):
    """When LLM invoke raises, catch and return empty SystemDescription."""
    mock_bom.return_value.scan.return_value = json.dumps({})
    mock_ast.return_value.scan_directory.return_value = {}

    mock_node_inst = mock_factory.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm
    mock_llm.invoke.side_effect = RuntimeError("LLM unavailable")

    res = infer_system_description(str(tmp_path), provider="mock")
    assert res == SystemDescription()


# ===================================================================
# infer_technical_documentation – uncovered paths
# ===================================================================


@patch("venturalitica.inference.NodeFactory")
@patch("venturalitica.inference.BOMScanner")
@patch("venturalitica.inference.ASTCodeScanner")
def test_infer_technical_documentation_full_flow(
    mock_ast, mock_bom, mock_factory, tmp_path
):
    """Full flow with mocked LLM returning valid JSON."""
    mock_bom.return_value.scan.return_value = json.dumps({"components": []})
    mock_ast.return_value.scan_directory.return_value = {
        "train.py": {
            "docstring": "Training script",
            "imports": ["torch", "pandas"],
            "calls": [{"type": "data_loading", "object": "pd", "method": "read_csv"}],
        }
    }

    mock_node_inst = mock_factory.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm

    td_data = {
        "development_methods": ["supervised learning"],
        "logic_description": "Neural network classifier",
        "architecture_diagram": "graph LR; A-->B",
        "data_provenance": {"sources": ["dataset.csv"]},
        "human_oversight_measures": ["manual review"],
        "predetermined_changes": "none",
        "validation_procedures": "cross-validation",
        "cybersecurity_measures": ["encryption"],
    }
    mock_response = MagicMock()
    mock_response.content = json.dumps(td_data)
    mock_llm.invoke.return_value = mock_response
    mock_node_inst._safe_json_loads.return_value = td_data

    (tmp_path / "README.md").write_text("# Readme content")

    res = infer_technical_documentation(str(tmp_path), provider="mock")
    assert isinstance(res, TechnicalDocumentation)
    assert res.development_methods == ["supervised learning"]
    assert res.logic_description == "Neural network classifier"


@patch("venturalitica.inference.NodeFactory")
@patch("venturalitica.inference.BOMScanner")
@patch("venturalitica.inference.ASTCodeScanner")
def test_infer_technical_documentation_prompt_not_found(
    mock_ast, mock_bom, mock_factory, tmp_path
):
    """When prompt key not found, returns empty TechnicalDocumentation."""
    mock_bom.return_value.scan.return_value = json.dumps({})
    mock_ast.return_value.scan_directory.return_value = {}

    with patch("venturalitica.inference.yaml.safe_load", return_value={"other": {}}):
        res = infer_technical_documentation(str(tmp_path), provider="mock")
    assert isinstance(res, TechnicalDocumentation)
    assert res.development_methods == []


@patch("venturalitica.inference.NodeFactory")
@patch("venturalitica.inference.BOMScanner")
@patch("venturalitica.inference.ASTCodeScanner")
def test_infer_technical_documentation_llm_exception(
    mock_ast, mock_bom, mock_factory, tmp_path
):
    """When LLM raises, returns empty TechnicalDocumentation."""
    mock_bom.return_value.scan.return_value = json.dumps({})
    mock_ast.return_value.scan_directory.return_value = {}

    mock_node_inst = mock_factory.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm
    mock_llm.invoke.side_effect = RuntimeError("LLM timeout")

    res = infer_technical_documentation(str(tmp_path), provider="mock")
    assert isinstance(res, TechnicalDocumentation)
    assert res.development_methods == []


@patch("venturalitica.inference.NodeFactory")
@patch("venturalitica.inference.BOMScanner")
@patch("venturalitica.inference.ASTCodeScanner")
def test_infer_technical_documentation_list_content(
    mock_ast, mock_bom, mock_factory, tmp_path
):
    """LLM returns list content -> joined to string before JSON parse."""
    mock_bom.return_value.scan.return_value = json.dumps({})
    mock_ast.return_value.scan_directory.return_value = {}

    mock_node_inst = mock_factory.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm

    td_data = {"development_methods": ["dl"], "logic_description": "Joined"}
    mock_response = MagicMock()
    mock_response.content = ['{"development_methods":', ' ["dl"]}']
    mock_llm.invoke.return_value = mock_response
    mock_node_inst._safe_json_loads.return_value = td_data

    res = infer_technical_documentation(str(tmp_path), provider="mock")
    assert isinstance(res, TechnicalDocumentation)


# ===================================================================
# infer_risk_classification – uncovered paths
# ===================================================================


@patch("venturalitica.inference.NodeFactory")
def test_infer_risk_classification_markdown_code_block(mock_factory):
    """Markdown ```json block is stripped before JSON parse."""
    mock_node_inst = mock_factory.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm

    raw_json = '{"risk_level": "HIGH", "reasoning": "test"}'
    mock_response = MagicMock()
    mock_response.content = f"```json\n{raw_json}\n```"
    mock_llm.invoke.return_value = mock_response
    mock_node_inst._safe_json_loads.return_value = {
        "risk_level": "HIGH",
        "reasoning": "test",
    }

    sd = SystemDescription(intended_purpose="Biometric ID", name="FaceID")
    res = infer_risk_classification(sd, provider="mock")
    assert res.risk_level == "HIGH"


@patch("venturalitica.inference.NodeFactory")
def test_infer_risk_classification_generic_code_block(mock_factory):
    """Generic ``` block (without json) is stripped."""
    mock_node_inst = mock_factory.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm

    raw_json = '{"risk_level": "MINIMAL", "reasoning": "simple tool"}'
    mock_response = MagicMock()
    mock_response.content = f"```\n{raw_json}\n```"
    mock_llm.invoke.return_value = mock_response
    mock_node_inst._safe_json_loads.return_value = {
        "risk_level": "MINIMAL",
        "reasoning": "simple tool",
    }

    sd = SystemDescription(intended_purpose="Calculator", name="Calc")
    res = infer_risk_classification(sd, provider="mock")
    assert res.risk_level == "MINIMAL"


@patch("venturalitica.inference.NodeFactory")
def test_infer_risk_classification_exception_fallback(mock_factory):
    """When LLM raises, returns RiskAssessment with error reasoning."""
    mock_node_inst = mock_factory.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm
    mock_llm.invoke.side_effect = RuntimeError("API down")

    sd = SystemDescription(intended_purpose="Test", name="T")
    res = infer_risk_classification(sd, provider="mock")
    assert isinstance(res, RiskAssessment)
    assert "Error" in res.reasoning
    assert res.risk_level == "UNKNOWN"
