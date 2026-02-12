import os
import json
import yaml
from pathlib import Path
from typing import Optional, Any, Dict
from venturalitica.models import SystemDescription
from venturalitica.assurance.graph.nodes import NodeFactory
from venturalitica.scanner import BOMScanner
from venturalitica.assurance.graph.parser import ASTCodeScanner


class ProjectContext:
    """
    Helper class to encapsulate shared scanning and loading logic for LLM inference.
    Eliminates boilerplate across infer_system_description, infer_technical_documentation, etc.
    """

    def __init__(self, target_dir: str):
        self.target_dir = target_dir
        self._bom: Optional[Dict[str, Any]] = None
        self._code_context: Optional[Dict[str, Any]] = None
        self._readme_content: Optional[str] = None

    @property
    def bom(self) -> Dict[str, Any]:
        """Lazy-load BOM via BOMScanner."""
        if self._bom is None:
            scanner = BOMScanner(self.target_dir)
            bom_json = scanner.scan()
            try:
                self._bom = json.loads(bom_json)
            except Exception:
                self._bom = {}
        return self._bom or {}

    @property
    def code_context(self) -> Dict[str, Any]:
        """Lazy-load code context via ASTCodeScanner."""
        if self._code_context is None:
            code_scanner = ASTCodeScanner()
            self._code_context = code_scanner.scan_directory(self.target_dir) or {}
        return self._code_context or {}

    @property
    def readme_content(self) -> str:
        """Lazy-load README file (first match from standard names)."""
        if self._readme_content is None:
            self._readme_content = ""
            for name in ["README.md", "readme.md", "README", "README.txt"]:
                readme_path = Path(self.target_dir) / name
                if readme_path.exists():
                    with open(readme_path, "r", encoding="utf-8") as f:
                        self._readme_content = f.read()[:5000]  # Limit size
                    break
        return self._readme_content

    @staticmethod
    def load_prompt(prompt_key: str) -> str:
        """
        Load a specific prompt from prompts.en.yaml.
        Returns empty string if not found.
        """
        prompt_path = (
            Path(__file__).parent
            / "assurance"
            / "graph"
            / "prompts"
            / "prompts.en.yaml"
        )
        if not prompt_path.exists():
            # Fallback search
            prompt_path = (
                Path(os.path.dirname(__file__))
                / "assurance"
                / "graph"
                / "prompts"
                / "prompts.en.yaml"
            )

        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompts = yaml.safe_load(f)
                return prompts.get(prompt_key, {}).get("prompt", "")
        return ""

    def format_code_summary(self, include_data_loading: bool = False) -> str:
        """
        Format code context into a readable summary for LLM.
        If include_data_loading=True, includes data loading calls.
        """
        code_summary = ""
        for fname, info in self.code_context.items():
            if "error" in info:
                continue
            code_summary += f"\nFile: {fname}"
            if info.get("docstring"):
                code_summary += f"\n  - Story: {info['docstring']}"
            if info.get("imports"):
                code_summary += f"\n  - Imports: {', '.join(info['imports'][:5])}"
            if include_data_loading:
                for call in info.get("calls", []):
                    if call.get("type") == "data_loading":
                        code_summary += f"\n  - 💿 DATA LOAD: {call.get('object')}.{call.get('method')}"
        return code_summary


def infer_system_description(
    target_dir: str,
    provider: str = "auto",
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> SystemDescription:
    """
    Analyzes the project repository and uses an LLM to infer the SystemDescription (Annex IV.1).
    """
    print(f"🪄 Starting Smart Inference for {target_dir}...")

    # Load project context (BOM, code, README)
    context = ProjectContext(target_dir)

    # Load inference prompt
    inference_prompt_raw = ProjectContext.load_prompt("system_card_inference")
    if not inference_prompt_raw:
        print("⚠️ Warning: System Card Inference prompt not found. Using fallback.")
        return SystemDescription()

    # Format and Invoke
    code_summary = context.format_code_summary()

    full_prompt = inference_prompt_raw.replace(
        "{bom}", json.dumps(context.bom, indent=2)
    )
    full_prompt = full_prompt.replace("{code}", code_summary)
    full_prompt = full_prompt.replace("{readme}", context.readme_content[:3000])

    try:
        factory = NodeFactory(model_name=model_name, provider=provider, api_key=api_key)
        response = factory.llm.invoke(full_prompt)
        content = response.content

        # Handle cases where some providers return a list of strings
        if isinstance(content, list):
            content = "".join(str(c) for c in content)

        # Robust JSON extraction
        data = factory._safe_json_loads(content)
        if data:
            return SystemDescription(
                name=data.get("name", ""),
                version=data.get("version", ""),
                provider_name=data.get("provider_name", ""),
                intended_purpose=data.get("intended_purpose", ""),
                interaction_description=data.get("interaction_description", ""),
                software_dependencies=data.get("software_dependencies", ""),
                market_placement_form=data.get("market_placement_form", ""),
                hardware_description=data.get("hardware_description", ""),
                ui_description=data.get("ui_description", ""),
                instructions_for_use=data.get("instructions_for_use", ""),
                potential_misuses=data.get("potential_misuses", ""),
            )
        else:
            print(
                f"⚠️ Smart Inference: JSON extraction failed. Content head: {content[:100]}"
            )
    except Exception as e:
        print(f"❌ Smart Inference failed: {e}")

    return SystemDescription()


def infer_technical_documentation(
    target_dir: str,
    provider: str = "auto",
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Any:
    """
    Infers Annex IV.2 Technical Documentation (Development, Data, Oversight, etc.)
    Returns a TechnicalDocumentation object (or dict if model not avail).
    """
    from venturalitica.models import TechnicalDocumentation

    print(f"🪄 Starting Technical Documentation Inference for {target_dir}...")

    # Load project context (BOM, code, README)
    context = ProjectContext(target_dir)

    # Load inference prompt
    inference_prompt_raw = ProjectContext.load_prompt(
        "technical_documentation_inference"
    )
    if not inference_prompt_raw:
        return TechnicalDocumentation()

    # Format Code Summary (Include Data Loading info)
    code_summary = context.format_code_summary(include_data_loading=True)

    full_prompt = inference_prompt_raw.replace(
        "{bom}", json.dumps(context.bom, indent=2)
    )
    full_prompt = full_prompt.replace("{code}", code_summary)
    full_prompt = full_prompt.replace("{readme}", context.readme_content[:3000])

    try:
        factory = NodeFactory(model_name=model_name, provider=provider, api_key=api_key)
        response = factory.llm.invoke(full_prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join(str(c) for c in content)

        data = factory._safe_json_loads(content)
        if data:
            return TechnicalDocumentation(
                development_methods=data.get("development_methods", []),
                logic_description=data.get("logic_description", ""),
                architecture_diagram=data.get("architecture_diagram", ""),
                data_provenance=data.get("data_provenance", {}),
                human_oversight_measures=data.get("human_oversight_measures", []),
                predetermined_changes=data.get("predetermined_changes", ""),
                validation_procedures=data.get("validation_procedures", ""),
                cybersecurity_measures=data.get("cybersecurity_measures", []),
            )
    except Exception as e:
        print(f"❌ Tech Doc Inference failed: {e}")

    return TechnicalDocumentation()


def infer_risk_classification(
    system_description: SystemDescription,
    provider: str = "auto",
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Any:
    """
    Infers the Regulatory Risk Level based on the System Description (Annex I & III).
    Returns a RiskAssessment object.
    """
    # Import locally to avoid circular imports if any
    from venturalitica.models import RiskAssessment

    # Load prompt
    inference_prompt_raw = ProjectContext.load_prompt("risk_classification_inference")
    if not inference_prompt_raw:
        return RiskAssessment(reasoning="Risk classification prompt not found")

    # Format Prompt
    full_prompt = inference_prompt_raw.replace(
        "{intended_purpose}", system_description.intended_purpose
    )
    full_prompt = full_prompt.replace(
        "{potential_misuses}", system_description.potential_misuses
    )
    full_prompt = full_prompt.replace("{name}", system_description.name)

    print(f"⚖️  Evaluating Risk Level using {provider}...")

    factory = NodeFactory(model_name=model_name, provider=provider, api_key=api_key)

    try:
        response = factory.llm.invoke(full_prompt)
        content = response.content
        # Clean markdown code blocks if present
        if isinstance(content, str):
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

        data = factory._safe_json_loads(content)

        return RiskAssessment(
            risk_level=data.get("risk_level", "UNKNOWN"),
            reasoning=data.get("reasoning", "Analysis failed"),
            applicable_articles=data.get("applicable_articles", []),
            flags=data.get("flags", []),
        )
    except Exception as e:
        print(f"❌ Risk Assessment Failed: {e}")
        return RiskAssessment(reasoning=f"Error: {e}")
