from typing import Dict, Any, List
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from venturalitica.graph.state import ComplianceState, SectionDraft
from venturalitica.scanner import BOMScanner
import os
import json

class NodeFactory:
    def __init__(self, model_name: str):
        # Initialize User's Local Model
        self.llm = ChatOllama(model=model_name, temperature=0.1)
        
    def scan_project(self, state: ComplianceState) -> Dict[str, Any]:
        """
        Scanner Node: Executed first.
        """
        print("🔍 Scanning project artifacts...")
        scanner = BOMScanner(state["project_root"])
        bom_json_str = scanner.scan()
        bom = json.loads(bom_json_str)
        
        # Load Runtime Metadata if available
        runtime_meta = {}
        meta_path = os.path.join(state["project_root"], ".venturalitica", "latest_run.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                runtime_meta = json.load(f)
                
        return {"bom": bom, "runtime_meta": runtime_meta}

    def plan_sections(self, state: ComplianceState) -> Dict[str, Any]:
        """
        Planning Node: Just prepares the state for parallel execution.
        """
        print("🗺️  Planning Annex IV sections...")
        return {"sections": {}}

    def _generate_generic_section(self, section_id: str, prompt_template: str, state: ComplianceState) -> SectionDraft:
        """
        Helper to invoke Ollama.
        """
        try:
            # Context Preparation
            bom_summary = [c['name'] for c in state['bom'].get('components', [])]
            meta_summary = state['runtime_meta'].get('audit_results', 'No audit run yet.')
            
            prompt = ChatPromptTemplate.from_template(prompt_template)
            chain = prompt | self.llm
            
            response = chain.invoke({
                "bom": str(bom_summary),
                "meta": str(meta_summary)
            })
            
            return {"content": response.content, "status": "completed"}
        except Exception as e:
            return {"content": f"Error generating section: {str(e)}", "status": "error"}

    def write_section_2a(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.a: Development Methods"""
        print("✍️  Drafting Section 2.a (Methods)...")
        prompt = """
        You are an AI Compliance Officer writing Annex IV.2(a) for the EU AI Act.
        
        CONTEXT:
        - Libraries detected: {bom}
        
        TASK:
        Describe the methods and steps used for the development of the AI system.
        Mention that the system is built using standard Python data science libraries.
        If 'sklearn' or 'torch' is present, mention them as the core framework.
        Keep it formal and legalistic.
        """
        draft = self._generate_generic_section("2.a", prompt, state)
        return {"sections": {**state.get("sections", {}), "2.a": draft}}

    def write_section_2b(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.b: Logic & Assumptions"""
        print("✍️  Drafting Section 2.b (Logic)...")
        prompt = """
        You are an AI Compliance Officer writing Annex IV.2(b) for the EU AI Act.
        
        CONTEXT:
        - Components: {bom}
        
        TASK:
        Describe the general logic of the AI system.
        Explain that the system uses inductive reasoning based on statistical learning.
        Justify the design choice of using these libraries as industry standard for auditability.
        """
        draft = self._generate_generic_section("2.b", prompt, state)
        return {"sections": {**state.get("sections", {}), "2.b": draft}}

    def write_section_2c(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.c: Architecture"""
        print("✍️  Drafting Section 2.c (Architecture)...")
        prompt = """
        You are an AI Compliance Officer writing Annex IV.2(c) for the EU AI Act.
        
        CONTEXT:
        - System BOM: {bom}
        
        TASK:
        Description of the system architecture.
        List the key software components and how they rely on each other.
        Use the BOM list provided.
        """
        draft = self._generate_generic_section("2.c", prompt, state)
        return {"sections": {**state.get("sections", {}), "2.c": draft}}
        
    def write_section_2g(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.g: Validation"""
        print("✍️  Drafting Section 2.g (Validation)...")
        # For validation, we trust the hard facts more than the LLM, but we let LLM wrap it.
        prompt = """
        You are an AI Compliance Officer writing Annex IV.2(g) for the EU AI Act.
        
        CONTEXT:
        - Validation Results: {meta}
        
        TASK:
        Describe the validation procedures.
        Summarize the audit results provided above.
        State clearly if the system meets the metric thresholds.
        """
        draft = self._generate_generic_section("2.g", prompt, state)
        return {"sections": {**state.get("sections", {}), "2.g": draft}}

    def compile_document(self, state: ComplianceState) -> Dict[str, Any]:
        """
        Compiler Node: Aggregates everything.
        """
        print("aaS Combining sections into final document...")
        sections = state["sections"]
        
        md = "# EU AI Act - Annex IV Technical Documentation\n\n"
        md += "## 2.a Methods and Development\n" + sections.get("2.a", {}).get("content", "N/A") + "\n\n"
        md += "## 2.b Design Logic\n" + sections.get("2.b", {}).get("content", "N/A") + "\n\n"
        md += "## 2.c System Architecture\n" + sections.get("2.c", {}).get("content", "N/A") + "\n\n"
        md += "## 2.g Validation and Testing\n" + sections.get("2.g", {}).get("content", "N/A") + "\n\n"
        
        return {"final_markdown": md}
