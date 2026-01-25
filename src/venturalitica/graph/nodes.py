from typing import Dict, Any, List, Optional
from langchain_ollama import ChatOllama
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from venturalitica.graph.state import ComplianceState, SectionDraft
from venturalitica.scanner import BOMScanner
from venturalitica.graph.parser import ASTCodeScanner
import os
import json
import os
import json
import re
import hashlib
import requests
from dotenv import load_dotenv
from packaging import version

# Initialize Env
load_dotenv()

class NodeFactory:
    def __init__(self, model_name: str):
        # Initialize LLM
        use_pro = os.getenv("VENTURALITICA_LLM_PRO", "false").lower() == "true"
        mistral_key = os.getenv("MISTRAL_API_KEY")

        if use_pro and mistral_key:
            print("🌟 Using High-Power Magistral LLM (Mistral AI)...")
            self.llm = ChatMistralAI(
                model="mistral-large-latest",
                temperature=0.1,
                max_retries=3,
                timeout=180,
                # Simple rate limiting via max_retries/timeout
            )
        else:
            print(f"🏠 Using Local LLM ({model_name})...")
            self.llm = ChatOllama(model=model_name, temperature=0.1)
        
    def _safe_json_loads(self, text: str) -> Optional[Dict]:
        """Robust JSON parser that handles markdown code blocks and common errors."""
        if not text:
            return None
            
        clean_text = text.strip()
        
        # 1. Strip Markdown Code Blocks
        clean_text = re.sub(r'```json\s*', '', clean_text)
        clean_text = re.sub(r'```', '', clean_text)
        
        # 2. Try raw parse
        try:
            return json.loads(clean_text)
        except:
            pass
            
        # 3. Find Largest {} block (Greedy)
        match = re.search(r'(\{.*\})', clean_text, re.DOTALL)
        if match:
            candidate = match.group(1)
            try:
                return json.loads(candidate)
            except:
                # 4. Emergency Cleanup: Common LLM JSON issues
                # Fix unescaped newlines in strings
                # Fix trailing commas
                candidate = re.sub(r',\s*\}', '}', candidate)
                candidate = re.sub(r',\s*\]', ']', candidate)
                try:
                    return json.loads(candidate)
                except:
                    pass
        
        return None

    def check_security(self, bom: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scans BOM against OSV.dev API for vulnerabilities.
        """
        print("  🛡️  Checking security vulnerabilities (OSV.dev)...")
        results = {"vulnerable": False, "issues": []}
        
        if not bom or "components" not in bom:
            return results

        components = bom.get("components", [])
        payload = {"queries": []}
        
        # Map BOM components to OSV queries
        for comp in components:
            if comp.get("type") == "library":
                payload["queries"].append({
                    "package": {"name": comp.get("name"), "ecosystem": "PyPI"},
                    "version": comp.get("version")
                })
        
        if not payload["queries"]:
            return results

        try:
            response = requests.post("https://api.osv.dev/v1/querybatch", json=payload, timeout=5)
            if response.status_code == 200:
                batch_results = response.json().get("results", [])
                for idx, res in enumerate(batch_results):
                    if "vulns" in res:
                        comp = components[idx]
                        for v in res["vulns"]:
                            results["vulnerable"] = True
                            # Map severity score to label
                            score = next((s["score"] for s in v.get("severity", []) if s["type"] == "CVSS_V3"), None)
                            label = "UNKNOWN"
                            if score:
                                try:
                                    s_val = float(score.split(":")[1]) if ":" in score else float(score)
                                    if s_val >= 9.0: label = "CRITICAL"
                                    elif s_val >= 7.0: label = "HIGH"
                                    elif s_val >= 4.0: label = "MEDIUM"
                                    else: label = "LOW"
                                except: label = "UNKNOWN"

                            results["issues"].append({
                                "package": comp.get("name"),
                                "version": comp.get("version"),
                                "id": v.get("id"),
                                "summary": v.get("summary") or v.get("details", "No summary available")[:100] + "...",
                                "severity": label,
                                "score": score or "N/A",
                                "link": f"https://osv.dev/vulnerability/{v.get('id')}"
                            })
                            print(f"    ⚠️ {label} Vulnerability found in {comp.get('name')}: {v.get('id')}")
        except Exception as e:
            print(f"  ⚠️ Security check failed: {e}")
            
        return results

    def scan_project(self, state: ComplianceState) -> Dict[str, Any]:
        """
        Scanner Node: Executed first.
        Prioritizes runtime artifacts (traces) over directory scanning.
        """
        print("🔍 Scanning project artifacts...")
        scanner = BOMScanner(state["project_root"])
        bom = json.loads(scanner.scan())
        
        # 1. Load Primary Runtime Metadata
        runtime_meta = {}
        meta_path = os.path.join(state["project_root"], ".venturalitica", "latest_run.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                runtime_meta = json.load(f)
                
        # 2. Collect Code Context (Priority: Runtime Evidence)
        code_context = {}
        
        # Check if latest_run already has code analysis
        if "code_context" in runtime_meta:
            print("  ✅ Using Runtime Code Evidence from latest run.")
            meta_ctx = runtime_meta["code_context"]
            filename = meta_ctx.get("file", "unknown_runtime_script")
            analysis = meta_ctx.get("analysis", {})
            
            # Enrich with raw source if path exists
            full_path = filename if os.path.isabs(filename) else os.path.join(state["project_root"], filename)
            if "raw_source" not in analysis and os.path.exists(full_path):
                with open(full_path, "r") as f:
                    analysis["raw_source"] = f.read()
            elif "raw_source" not in analysis:
                analysis["raw_source"] = f"Source path not found in trace: {filename}"
                
            code_context[os.path.basename(filename)] = analysis
        
        # Check for other traces
        trace_dir = os.path.join(state["project_root"], ".venturalitica")
        if os.path.exists(trace_dir):
            for f in os.listdir(trace_dir):
                if f.startswith("trace_") and f.endswith(".json"):
                    print(f"  ✅ Found execution trace: {f}")
                    with open(os.path.join(trace_dir, f), "r") as tf:
                        trace_data = json.load(tf)
                        if "code_context" in trace_data:
                            fname = trace_data["code_context"].get("file", f)
                            code_context[fname] = trace_data["code_context"].get("analysis", {})

        # Fallback to directory scan only if no runtime context found
        if not code_context:
            print("  ⚠️ No runtime traces found. Falling back to directory scan (post-hoc).")
            code_scanner = ASTCodeScanner()
            code_context = code_scanner.scan_directory(state["project_root"])

        # 3. Security Scan
        bom_security = self.check_security(bom)
        
        # 4. Calculate Evidence Hash (Cryptographic Anchor)
        evidence_payload = json.dumps({"bom": bom, "runtime": runtime_meta, "context": code_context}, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_payload.encode()).hexdigest()
        print(f"  🔐 Evidence Hash: {evidence_hash[:12]}...")

        return {
            "bom": bom, 
            "runtime_meta": runtime_meta, 
            "sections": {"scanner": {"content": "Project analysis complete", "status": "completed", "feedback": None}},
            "evidence_hash": evidence_hash,
            "bom_security": bom_security,
            "code_context": code_context
        }

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
            
            # Language Instruction (Synthesis ALWAYS in English for better grounding)
            lang_instruction = "Output Language: English"

            # Format Code Context (summarized)
            code_summary = ""
            context = state.get("code_context", {})
            for fname, info in context.items():
                if "error" in info:
                    continue
                code_summary += f"\nFile: {fname}"
                if "docstring" in info and info["docstring"]:
                    code_summary += f"\n  - Story/Intent: {info['docstring']}"
                if "calls" in info and info["calls"]:
                    formatted_calls = [f"{c['object']}.{c['method']} (L{c['lineno']})" for c in info['calls'][:5]]
                    code_summary += f"\n  - Key Calls: {', '.join(formatted_calls)}"
                if "imports" in info and info["imports"]:
                    code_summary += f"\n  - Stack: {', '.join(info['imports'][:5])}"
            
            # Check for existing draft and feedback
            current_draft = state.get("sections", {}).get(section_id, {})
            previous_content = current_draft.get("content", "")
            feedback = current_draft.get("feedback", None)
            
            full_prompt = f"""
{lang_instruction}

BOM artifacts from scanner:
{{bom_data}}

Runtime metadata (from trace):
{{meta_data}}

Extracted Code Context (AST):
{{code_summary}}

Section feedback or specifics:
{prompt_template}

Write the section following the EU AI Act 2024 compliance guidelines. 
TARGET LANGUAGE: English

STRICT GROUNDING RULES:
1. ONLY use information from the provided BOM, Runtime Metadata, and Code Summary.
2. DO NOT invent versions, libraries, or logic not found in the evidence.
3. If information is missing (e.g., provenance of data not in code), say "NOT_DOCUMENTED: Evidence missing from scan" instead of speculating.
4. DO NOT wrap your response in markdown code blocks (```markdwon ... ```). Output RAW markdown only.
5. Use a dry, technical, regulatory tone. No conversational filler.
6. MANDATORY: The entire response MUST be in English.
"""            
            if feedback and previous_content:
                 print(f"  🔄 Refining Section {section_id} based on critic feedback...")
                 full_prompt += f"""
                 
                 CRITIC FEEDBACK (FIX HALLUCINATIONS/LANGUAGE/MISSING DATA):
                 {{feedback}}
                 
                 INSTRUCTIONS:
                 Rewrite the draft to address the feedback. Keep the good parts.
                 STRICTLY AVOID inventing details. If the critic asks for evidence you don't have, mark as "NOT_DOCUMENTED".
                 STRICTLY FOLLOW the target language: English.
                 DO NOT wrap your response in markdown code blocks.
                 """
            
            prompt = ChatPromptTemplate.from_template(full_prompt)
            chain = prompt | self.llm
            
            response = chain.invoke({
                "bom_data": json.dumps(state.get('bom', {}), indent=2),
                "meta_data": json.dumps(state.get('runtime_meta', {}), indent=2),
                "code_summary": code_summary,
                "bom": str(bom_summary),
                "meta": str(meta_summary),
                "code": code_summary,
                "previous_content": previous_content,
                "feedback": feedback,
                "language": "English"
            })
            
            # Clean response from markdown escapes
            content = response.content
            if content.startswith("```"):
                import re
                content = re.sub(r'^```[a-zA-Z]*\n?', '', content)
                content = re.sub(r'\n?```$', '', content)

            return {
                "content": content.strip(), 
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
        - Code Analysis: {code}
        
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
        - Code Analysis: {code}
        
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
        - Code Analysis: {code}
        
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
        - Code Analysis: {code}
        
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
        
        CONTEXT:
        - Code Analysis: {code}

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
        
        CONTEXT:
        - Code Analysis: {code}
        
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
        - Code Analysis: {code}
        
        TASK:
        Address the following requirement:
        "the validation and testing procedures used, including information about the validation and testing data used and their main characteristics; metrics used to measure accuracy, robustness and compliance with other relevant requirements set out in Chapter III, Section 2, as well as potentially discriminatory impacts; test logs and all test reports dated and signed by the responsible persons, including with regard to predetermined changes as referred to under point (f);"
        """
        draft = self._generate_generic_section("2.g", prompt, state)
        return {"sections": {**state.get("sections", {}), "2.g": draft}}

    def write_section_2h(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.h: Cybersecurity"""
        print("✍️  Drafting Section 2.h (Cybersecurity)...")
        
        security_report = state.get("bom_security", {})
        vuln_text = "No known vulnerabilities detected in supply chain."
        if security_report.get("vulnerable"):
            issues = security_report.get("issues", [])
            vuln_text = f"CRITICAL: Found {len(issues)} vulnerabilities in supply chain:\n"
            for i in issues:
                vuln_text += f"- {i['package']} {i['version']}: {i['id']} (Severity: {i['severity']})\n"
        
        prompt = f"""
        You are an AI Compliance Officer writing Annex IV.2(h) for the EU AI Act.
        
        CONTEXT:
        - Code Analysis: {{code}}
        - Supply Chain Security Scan:
        {vuln_text}

        TASK:
        Address the following requirement:
        "cybersecurity measures put in place;"
        
        If vulnerabilities are present, you MUST disclose them and suggest mitigation (updating packages).
        """
        draft = self._generate_generic_section("2.h", prompt, state)
        return {"sections": {**state.get("sections", {}), "2.h": draft}}

    def compile_document(self, state: ComplianceState) -> Dict[str, Any]:
        """
        Compiler Node: Aggregates everything.
        """
        print(f"aaS Combining sections into final document (Language: {state.get('language', 'en')})...")
        sections = state["sections"]
        lang = state.get("language", "en").lower()
        
        # Localized Headers Mapping (Sample)
        headers = {
            "title": "EU AI Act - Annex IV Technical Documentation",
            "2.a": "2.a Methods and Development",
            "2.b": "2.b Design Logic",
            "2.c": "2.c System Architecture",
            "2.d": "2.d Data Requirements",
            "2.e": "2.e Human Oversight",
            "2.f": "2.f Predetermined Changes",
            "2.g": "2.g Validation and Testing",
            "2.h": "2.h Cybersecurity"
        }

        # If language is not English, translate the header titles
        if lang not in ["en", "english"]:
            print(f"  🌐 Scaling headers to {lang}...")
            header_list = "\n".join([f"{k}: {v}" for k, v in headers.items()])
            prompt = f"""
            Translate the following header titles specifically to English. 
            CRITICAL: Do not confuse {lang} with neighboring languages (e.g., if Occitan, do not use French or Catalan).
            Return ONLY a JSON object with the original keys and the translated values.
            
            HEADERS:
            {header_list}
            """
            try:
                response = self.llm.invoke(prompt)
                import re
                match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if match:
                    translated_headers = json.loads(match.group(0))
                    headers.update(translated_headers)
            except Exception as e:
                print(f"  ⚠️ Header translation failed: {e}")

                print(f"  ⚠️ Header translation failed: {e}")
 
        evidence_hash = state.get("evidence_hash", "UNKNOWN_HASH")
        md = f"# {headers['title']}\n"
        md += f"**Evidence Hash (SHA-256):** `{evidence_hash}`\n\n"
        md += f"## {headers['2.a']}\n" + sections.get("2.a", {}).get("content", "N/A") + "\n\n"
        md += f"## {headers['2.b']}\n" + sections.get("2.b", {}).get("content", "N/A") + "\n\n"
        md += f"## {headers['2.c']}\n" + sections.get("2.c", {}).get("content", "N/A") + "\n\n"
        md += f"## {headers['2.d']}\n" + sections.get("2.d", {}).get("content", "N/A") + "\n\n"
        md += f"## {headers['2.e']}\n" + sections.get("2.e", {}).get("content", "N/A") + "\n\n"
        md += f"## {headers['2.f']}\n" + sections.get("2.f", {}).get("content", "N/A") + "\n\n"
        md += f"## {headers['2.g']}\n" + sections.get("2.g", {}).get("content", "N/A") + "\n\n"
        md += f"## {headers['2.h']}\n" + sections.get("2.h", {}).get("content", "N/A") + "\n\n"
        
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
        You are a Chief AI Auditor for the EU Commission. Review the Annex IV.2 draft for accuracy, grounding, and language consistency.
        
        EVIDENCE SOURCES (The ONLY source of truth):
        - BOM: {bom}
        - AST/Code: {code}
        - Trace: {meta}
        
        TARGET LANGUAGE: English
        
        DRAFT DOCUMENT:
        {doc}
        
        TASK:
        1. Identify "Hallucinations": Claims about data, versions, or logic NOT found in the evidence sources.
        2. Identify Language Mismatch: If any section is not in English, mark it as REVISE.
        3. Identify Speculation: Where the agent is guessing instead of saying "NOT_DOCUMENTED".
        4. Rate regulatory tone.
        
        If you find hallucinations or language errors, REVISE and point them out specifically in the feedback.
        
        OUTPUT FORMAT (Strict JSON):
        {{
            "verdict": "APPROVE" or "REVISE",
            "feedback": {{
                "2.a": "Language mismatch: Expected English but found other...",
                "2.b": "Evidence mismatch: X is mentioned but not in BOM...",
                ...
            }}
        }} 
        """)
        
        chain = prompt | self.llm
        try:
            response = chain.invoke({
                "doc": doc,
                "bom": json.dumps(state.get('bom', {}), indent=2),
                "code": state.get('sections', {}).get('scanner', {}).get('content', 'N/A'),
                "meta": json.dumps(state.get('runtime_meta', {}), indent=2),
                "language": "English"
            })
            content = response.content
            feedback_json = self._safe_json_loads(content)
            
            if feedback_json:
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
    def translate_document(self, state: ComplianceState) -> Dict[str, Any]:
        """
        Translator Node: Final pass to translate English synthesis to ALL Target Languages.
        Refactored to handle a list of languages and avoid redundant syntheses.
        """
        target_langs = state.get("languages", [])
        doc = state.get("final_markdown", "")
        
        if not target_langs or not doc:
            return {"translations": {}}

        translations = {}
        
        # Internal helper to translate for ONE language (chunked)
        def _translate_single_lang(lang_name: str, english_doc: str) -> str:
            if lang_name.lower() == "english":
                return english_doc
                
            print(f"🌍 Translating technical document to {lang_name} (chunked)...")
            
            # Split by H2 headers (## 2.a, ## 2.b, etc.)
            chunks = re.split(r'^(## 2\.[a-h].*)$', english_doc, flags=re.MULTILINE)
            
            translated_parts = []
            prompt_tmpl = ChatPromptTemplate.from_template("""
            You are a Technical Multi-lingual Expert. Translate the following section from an EU AI Act Annex IV draft from English to {target_lang}.
            
            RULES:
            1. Preserve all technical terms (library names, versions, function calls) in their original English form.
            2. Maintain Markdown structure.
            3. Formal regulatory tone.
            4. No conversational filler.
            
            TEXT TO TRANSLATE:
            {text}
            """)
            
            chain = prompt_tmpl | self.llm
            
            current_header = ""
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                    
                if chunk.startswith("## 2."):
                    current_header = chunk
                    continue
                
                text_to_translate = chunk
                if current_header:
                    text_to_translate = f"{current_header}\n{chunk}"
                    current_header = ""

                try:
                    response = chain.invoke({"text": text_to_translate, "target_lang": lang_name})
                    content = response.content
                    if content.startswith("```"):
                        content = re.sub(r'^```[a-zA-Z]*\n?', '', content)
                        content = re.sub(r'\n?```$', '', content)
                    translated_parts.append(content.strip())
                except Exception as e:
                    print(f"  ⚠️ Chunk translation failed for {lang_name}: {e}")
                    translated_parts.append(text_to_translate) # Fallback

            return "\n\n".join(translated_parts)

        # Sequential processing to avoid LLM rate limits/concurrency issues
        for lang in target_langs:
            translations[lang] = _translate_single_lang(lang, doc)

        return {"translations": translations}
