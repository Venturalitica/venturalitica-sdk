import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from venturalitica.inference import (
    SystemDescription,
    infer_risk_classification,
    infer_system_description,
    infer_technical_documentation,
)
from venturalitica.models import RiskAssessment, TechnicalDocumentation


def _make_agentic_mocks():
    """Create mock NodeFactory and ASTCodeScanner classes returned by _import_agentic()."""
    mock_factory_cls = MagicMock()
    mock_ast_cls = MagicMock()
    return mock_factory_cls, mock_ast_cls


# ===================================================================
# EXISTING TESTS (preserved, adapted to lazy-load pattern)
# ===================================================================


@patch("venturalitica.inference._import_agentic")
@patch("venturalitica.inference.BOMScanner")
def test_infer_system_description_mock(mock_bom, mock_import, tmp_path):
    mock_factory_cls, mock_ast_cls = _make_agentic_mocks()
    mock_import.return_value = (mock_factory_cls, mock_ast_cls)

    mock_bom.return_value.scan.return_value = json.dumps({"components": []})
    mock_ast_cls.return_value.scan_directory.return_value = {
        "main.py": {"docstring": "Test script"}
    }

    mock_node_inst = mock_factory_cls.return_value
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

    (tmp_path / "README.md").write_text("Hello")

    res = infer_system_description(str(tmp_path), provider="mock")
    assert res.name == "Inferred System"


@patch("venturalitica.inference._import_agentic")
def test_infer_risk_classification_mock(mock_import):
    mock_factory_cls, mock_ast_cls = _make_agentic_mocks()
    mock_import.return_value = (mock_factory_cls, mock_ast_cls)

    mock_node_inst = mock_factory_cls.return_value
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


@patch("venturalitica.inference._import_agentic")
@patch("venturalitica.inference.BOMScanner")
def test_infer_system_description_bom_parse_failure(mock_bom, mock_import, tmp_path):
    """BOM scan returns non-JSON -> bom falls back to {}."""
    mock_factory_cls, mock_ast_cls = _make_agentic_mocks()
    mock_import.return_value = (mock_factory_cls, mock_ast_cls)

    mock_bom.return_value.scan.return_value = "NOT-VALID-JSON"
    mock_ast_cls.return_value.scan_directory.return_value = {}

    mock_node_inst = mock_factory_cls.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm
    mock_response = MagicMock()
    mock_response.content = json.dumps({"name": "X"})
    mock_llm.invoke.return_value = mock_response
    mock_node_inst._safe_json_loads.return_value = {"name": "X"}

    res = infer_system_description(str(tmp_path), provider="mock")
    assert isinstance(res, SystemDescription)


@patch("venturalitica.inference._import_agentic")
@patch("venturalitica.inference.BOMScanner")
def test_infer_system_description_readme_discovery(mock_bom, mock_import, tmp_path):
    """README discovery loop picks up readme.md (second candidate)."""
    mock_factory_cls, mock_ast_cls = _make_agentic_mocks()
    mock_import.return_value = (mock_factory_cls, mock_ast_cls)

    mock_bom.return_value.scan.return_value = json.dumps({})
    mock_ast_cls.return_value.scan_directory.return_value = {}

    mock_node_inst = mock_factory_cls.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm
    mock_response = MagicMock()
    mock_response.content = json.dumps({"name": "WithReadme"})
    mock_llm.invoke.return_value = mock_response
    mock_node_inst._safe_json_loads.return_value = {"name": "WithReadme"}

    (tmp_path / "readme.md").write_text("# My Project\nDescription here")

    res = infer_system_description(str(tmp_path), provider="mock")
    assert isinstance(res, SystemDescription)


@patch("venturalitica.inference._import_agentic")
@patch("venturalitica.inference.BOMScanner")
def test_infer_system_description_empty_prompt_fallback(mock_bom, mock_import, tmp_path):
    """When prompt file doesn't have the key, returns empty SystemDescription."""
    mock_factory_cls, mock_ast_cls = _make_agentic_mocks()
    mock_import.return_value = (mock_factory_cls, mock_ast_cls)

    mock_bom.return_value.scan.return_value = json.dumps({})
    mock_ast_cls.return_value.scan_directory.return_value = {}

    with patch("venturalitica.inference.yaml.safe_load", return_value={"other_key": {}}):
        res = infer_system_description(str(tmp_path), provider="mock")
    assert res == SystemDescription()


@patch("venturalitica.inference._import_agentic")
@patch("venturalitica.inference.BOMScanner")
def test_infer_system_description_llm_list_content(mock_bom, mock_import, tmp_path):
    """When LLM returns list content, it is joined."""
    mock_factory_cls, mock_ast_cls = _make_agentic_mocks()
    mock_import.return_value = (mock_factory_cls, mock_ast_cls)

    mock_bom.return_value.scan.return_value = json.dumps({})
    mock_ast_cls.return_value.scan_directory.return_value = {}

    mock_node_inst = mock_factory_cls.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm

    mock_response = MagicMock()
    mock_response.content = ['{"name":', ' "ListJoined"}']
    mock_llm.invoke.return_value = mock_response
    mock_node_inst._safe_json_loads.return_value = {"name": "ListJoined"}

    res = infer_system_description(str(tmp_path), provider="mock")
    assert res.name == "ListJoined"


@patch("venturalitica.inference._import_agentic")
@patch("venturalitica.inference.BOMScanner")
def test_infer_system_description_json_extraction_failure(mock_bom, mock_import, tmp_path):
    """When _safe_json_loads returns None, fallback to empty SystemDescription."""
    mock_factory_cls, mock_ast_cls = _make_agentic_mocks()
    mock_import.return_value = (mock_factory_cls, mock_ast_cls)

    mock_bom.return_value.scan.return_value = json.dumps({})
    mock_ast_cls.return_value.scan_directory.return_value = {}

    mock_node_inst = mock_factory_cls.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm

    mock_response = MagicMock()
    mock_response.content = "This is not JSON at all"
    mock_llm.invoke.return_value = mock_response
    mock_node_inst._safe_json_loads.return_value = None

    res = infer_system_description(str(tmp_path), provider="mock")
    assert res == SystemDescription()


@patch("venturalitica.inference._import_agentic")
@patch("venturalitica.inference.BOMScanner")
def test_infer_system_description_exception_handler(mock_bom, mock_import, tmp_path):
    """When LLM invoke raises, catch and return empty SystemDescription."""
    mock_factory_cls, mock_ast_cls = _make_agentic_mocks()
    mock_import.return_value = (mock_factory_cls, mock_ast_cls)

    mock_bom.return_value.scan.return_value = json.dumps({})
    mock_ast_cls.return_value.scan_directory.return_value = {}

    mock_node_inst = mock_factory_cls.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm
    mock_llm.invoke.side_effect = RuntimeError("LLM unavailable")

    res = infer_system_description(str(tmp_path), provider="mock")
    assert res == SystemDescription()


# ===================================================================
# infer_technical_documentation – uncovered paths
# ===================================================================


@patch("venturalitica.inference._import_agentic")
@patch("venturalitica.inference.BOMScanner")
def test_infer_technical_documentation_full_flow(mock_bom, mock_import, tmp_path):
    """Full flow with mocked LLM returning valid JSON."""
    mock_factory_cls, mock_ast_cls = _make_agentic_mocks()
    mock_import.return_value = (mock_factory_cls, mock_ast_cls)

    mock_bom.return_value.scan.return_value = json.dumps({"components": []})
    mock_ast_cls.return_value.scan_directory.return_value = {
        "train.py": {
            "docstring": "Training script",
            "imports": ["torch", "pandas"],
            "calls": [{"type": "data_loading", "object": "pd", "method": "read_csv"}],
        }
    }

    mock_node_inst = mock_factory_cls.return_value
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


@patch("venturalitica.inference._import_agentic")
@patch("venturalitica.inference.BOMScanner")
def test_infer_technical_documentation_prompt_not_found(mock_bom, mock_import, tmp_path):
    """When prompt key not found, returns empty TechnicalDocumentation."""
    mock_factory_cls, mock_ast_cls = _make_agentic_mocks()
    mock_import.return_value = (mock_factory_cls, mock_ast_cls)

    mock_bom.return_value.scan.return_value = json.dumps({})
    mock_ast_cls.return_value.scan_directory.return_value = {}

    with patch("venturalitica.inference.yaml.safe_load", return_value={"other": {}}):
        res = infer_technical_documentation(str(tmp_path), provider="mock")
    assert isinstance(res, TechnicalDocumentation)
    assert res.development_methods == []


@patch("venturalitica.inference._import_agentic")
@patch("venturalitica.inference.BOMScanner")
def test_infer_technical_documentation_llm_exception(mock_bom, mock_import, tmp_path):
    """When LLM raises, returns empty TechnicalDocumentation."""
    mock_factory_cls, mock_ast_cls = _make_agentic_mocks()
    mock_import.return_value = (mock_factory_cls, mock_ast_cls)

    mock_bom.return_value.scan.return_value = json.dumps({})
    mock_ast_cls.return_value.scan_directory.return_value = {}

    mock_node_inst = mock_factory_cls.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm
    mock_llm.invoke.side_effect = RuntimeError("LLM timeout")

    res = infer_technical_documentation(str(tmp_path), provider="mock")
    assert isinstance(res, TechnicalDocumentation)
    assert res.development_methods == []


@patch("venturalitica.inference._import_agentic")
@patch("venturalitica.inference.BOMScanner")
def test_infer_technical_documentation_list_content(mock_bom, mock_import, tmp_path):
    """LLM returns list content -> joined to string before JSON parse."""
    mock_factory_cls, mock_ast_cls = _make_agentic_mocks()
    mock_import.return_value = (mock_factory_cls, mock_ast_cls)

    mock_bom.return_value.scan.return_value = json.dumps({})
    mock_ast_cls.return_value.scan_directory.return_value = {}

    mock_node_inst = mock_factory_cls.return_value
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


@patch("venturalitica.inference._import_agentic")
def test_infer_risk_classification_markdown_code_block(mock_import):
    """Markdown ```json block is stripped before JSON parse."""
    mock_factory_cls, mock_ast_cls = _make_agentic_mocks()
    mock_import.return_value = (mock_factory_cls, mock_ast_cls)

    mock_node_inst = mock_factory_cls.return_value
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


@patch("venturalitica.inference._import_agentic")
def test_infer_risk_classification_generic_code_block(mock_import):
    """Generic ``` block (without json) is stripped."""
    mock_factory_cls, mock_ast_cls = _make_agentic_mocks()
    mock_import.return_value = (mock_factory_cls, mock_ast_cls)

    mock_node_inst = mock_factory_cls.return_value
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


@patch("venturalitica.inference._import_agentic")
def test_infer_risk_classification_exception_fallback(mock_import):
    """When LLM raises, returns RiskAssessment with error reasoning."""
    mock_factory_cls, mock_ast_cls = _make_agentic_mocks()
    mock_import.return_value = (mock_factory_cls, mock_ast_cls)

    mock_node_inst = mock_factory_cls.return_value
    mock_llm = MagicMock()
    mock_node_inst.llm = mock_llm
    mock_llm.invoke.side_effect = RuntimeError("API down")

    sd = SystemDescription(intended_purpose="Test", name="T")
    res = infer_risk_classification(sd, provider="mock")
    assert isinstance(res, RiskAssessment)
    assert "Error" in res.reasoning
    assert res.risk_level == "UNKNOWN"
