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
        return {
            "sections": {},
            "revision_count": 0,
            "critic_verdict": ""
        }

    def _generate_generic_section(self, section_id: str, prompt_template: str, state: ComplianceState) -> SectionDraft:
        """
        Helper to invoke Ollama, supporting feedback loop.
        """
        try:
            # Context Preparation
            bom_summary = [c['name'] for c in state['bom'].get('components', [])]
            meta_summary = state['runtime_meta'].get('audit_results', 'No audit run yet.')
            
            # Check for existing draft and feedback
            current_draft = state.get("sections", {}).get(section_id, {})
            previous_content = current_draft.get("content", "")
            feedback = current_draft.get("feedback", None)
            
            full_prompt = prompt_template
            
            if feedback and previous_content:
                 print(f"  🔄 Refining Section {section_id} based on critic feedback...")
                 full_prompt += f"""
                 
                 PREVIOUS DRAFT:
                 {previous_content}
                 
                 CRITIC FEEDBACK (FIX THIS):
                 {feedback}
                 
                 INSTRUCTIONS:
                 Rewrite the draft to address the feedback. Keep the good parts.
                 """
            
            prompt = ChatPromptTemplate.from_template(full_prompt)
            chain = prompt | self.llm
            
            response = chain.invoke({
                "bom": str(bom_summary),
                "meta": str(meta_summary)
            })
            
            return {
                "content": response.content, 
                "status": "completed",
                "feedback": None # Clear feedback after handling
            }
        except Exception as e:
            return {"content": f"Error generating section: {str(e)}", "status": "error", "feedback": None}

    def write_section_2a(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.a: Development Methods"""
        print("✍️  Drafting Section 2.a (Methods)...")
        prompt = """
        You are an AI Compliance Officer writing Annex IV.2(a) for the EU AI Act.
        
        CONTEXT:
        - Libraries detected: {bom}
        
        TASK:
        Address the following requirement:
        "the methods and steps performed for the development of the AI system, including, where relevant, recourse to pre-trained systems or tools provided by third parties and how those were used, integrated or modified by the provider;"
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
        Address the following requirement:
        "the design specifications of the system, namely the general logic of the AI system and of the algorithms; the key design choices including the rationale and assumptions made, including with regard to persons or groups of persons in respect of who, the system is intended to be used; the main classification choices; what the system is designed to optimise for, and the relevance of the different parameters; the description of the expected output and output quality of the system; the decisions about any possible trade-off made regarding the technical solutions adopted to comply with the requirements set out in Chapter III, Section 2;"
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
        Address the following requirement:
        "the description of the system architecture explaining how software components build on or feed into each other and integrate into the overall processing; the computational resources used to develop, train, test and validate the AI system;"
        """
        draft = self._generate_generic_section("2.c", prompt, state)
        return {"sections": {**state.get("sections", {}), "2.c": draft}}

    def write_section_2d(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.d: Data Requirements"""
        print("✍️  Drafting Section 2.d (Data)...")
        prompt = """
        You are an AI Compliance Officer writing Annex IV.2(d) for the EU AI Act.
        
        CONTEXT:
        - Libraries: {bom}
        
        TASK:
        Address the following requirement:
        "where relevant, the data requirements in terms of datasheets describing the training methodologies and techniques and the training data sets used, including a general description of these data sets, information about their provenance, scope and main characteristics; how the data was obtained and selected; labelling procedures (e.g. for supervised learning), data cleaning methodologies (e.g. outliers detection);"
        """
        draft = self._generate_generic_section("2.d", prompt, state)
        return {"sections": {**state.get("sections", {}), "2.d": draft}}

    def write_section_2e(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.e: Human Oversight"""
        print("✍️  Drafting Section 2.e (Oversight)...")
        prompt = """
        You are an AI Compliance Officer writing Annex IV.2(e) for the EU AI Act.
        
        TASK:
        Address the following requirement:
        "assessment of the human oversight measures needed in accordance with Article 14, including an assessment of the technical measures needed to facilitate the interpretation of the outputs of AI systems by the deployers, in accordance with Article 13(3), point (d);"
        """
        draft = self._generate_generic_section("2.e", prompt, state)
        return {"sections": {**state.get("sections", {}), "2.e": draft}}

    def write_section_2f(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.f: Predetermined Changes"""
        print("✍️  Drafting Section 2.f (Changes)...")
        prompt = """
        You are an AI Compliance Officer writing Annex IV.2(f) for the EU AI Act.
        
        TASK:
        Address the following requirement:
        "where applicable, a detailed description of pre-determined changes to the AI system and its performance, together with all the relevant information related to the technical solutions adopted to ensure continuous compliance of the AI system with the relevant requirements set out in Chapter III, Section 2;"
        """
        draft = self._generate_generic_section("2.f", prompt, state)
        return {"sections": {**state.get("sections", {}), "2.f": draft}}
        
    def write_section_2g(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.g: Validation"""
        print("✍️  Drafting Section 2.g (Validation)...")
        prompt = """
        You are an AI Compliance Officer writing Annex IV.2(g) for the EU AI Act.
        
        CONTEXT:
        - Validation Results: {meta}
        
        TASK:
        Address the following requirement:
        "the validation and testing procedures used, including information about the validation and testing data used and their main characteristics; metrics used to measure accuracy, robustness and compliance with other relevant requirements set out in Chapter III, Section 2, as well as potentially discriminatory impacts; test logs and all test reports dated and signed by the responsible persons, including with regard to predetermined changes as referred to under point (f);"
        """
        draft = self._generate_generic_section("2.g", prompt, state)
        return {"sections": {**state.get("sections", {}), "2.g": draft}}

    def write_section_2h(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.h: Cybersecurity"""
        print("✍️  Drafting Section 2.h (Cybersecurity)...")
        prompt = """
        You are an AI Compliance Officer writing Annex IV.2(h) for the EU AI Act.
        
        TASK:
        Address the following requirement:
        "cybersecurity measures put in place;"
        """
        draft = self._generate_generic_section("2.h", prompt, state)
        return {"sections": {**state.get("sections", {}), "2.h": draft}}

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
        md += "## 2.d Data Requirements\n" + sections.get("2.d", {}).get("content", "N/A") + "\n\n"
        md += "## 2.e Human Oversight\n" + sections.get("2.e", {}).get("content", "N/A") + "\n\n"
        md += "## 2.f Predetermined Changes\n" + sections.get("2.f", {}).get("content", "N/A") + "\n\n"
        md += "## 2.g Validation and Testing\n" + sections.get("2.g", {}).get("content", "N/A") + "\n\n"
        md += "## 2.h Cybersecurity\n" + sections.get("2.h", {}).get("content", "N/A") + "\n\n"
        
        return {"final_markdown": md}

    def critique_document(self, state: ComplianceState) -> Dict[str, Any]:
        """
        Critic Node: Reviews the document and requests revisions.
        """
        print("🧐 Critiquing document...")
        doc = state.get("final_markdown", "")
        revision_count = state.get("revision_count", 0) + 1
        
        if revision_count > 3:
            print("  ⚠️ Max revisions reached. Forcing approval.")
            return {"critic_verdict": "APPROVE", "revision_count": revision_count}
            
        prompt = ChatPromptTemplate.from_template("""
        You are a Chief AI Auditor. Review the following Annex IV.2 documentation.
        
        DOCUMENT:
        {doc}
        
        TASK:
        Evaluate coherence, completeness, and legal tone.
        
        OUTPUT FORMAT (Strict JSON):
        {{
            "verdict": "APPROVE" or "REVISE",
            "feedback": {{
                "2.a": "feedback...",
                "2.b": "feedback...",
                ...
            }}
        }} 
        """)
        
        chain = prompt | self.llm
        try:
            response = chain.invoke({"doc": doc})
            import re
            content = response.content
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                feedback_json = json.loads(match.group(0))
                verdict = feedback_json.get("verdict", "APPROVE")
                feedbacks = feedback_json.get("feedback", {})
                
                new_sections = {**state["sections"]}
                for k, v in new_sections.items():
                    if k in feedbacks and feedbacks[k]:
                        new_sections[k] = {**v, "feedback": feedbacks[k], "status": "drafting"}
                
                return {
                    "critic_verdict": verdict, 
                    "revision_count": revision_count,
                    "sections": new_sections
                }
            else:
                 print("  ⚠️ Critic returned non-JSON. Approving.")
                 return {"critic_verdict": "APPROVE", "revision_count": revision_count}
                 
        except Exception as e:
            print(f"  ⚠️ Critic error: {e}")
            return {"critic_verdict": "APPROVE", "revision_count": revision_count}
