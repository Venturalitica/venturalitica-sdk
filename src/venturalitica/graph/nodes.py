from typing import Dict, Any, List, Optional
from langchain_ollama import ChatOllama
from langchain_mistralai import ChatMistralAI
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import ChatPromptTemplate
from venturalitica.graph.state import ComplianceState, SectionDraft
from venturalitica.scanner import BOMScanner
from venturalitica.graph.parser import ASTCodeScanner
import os
import json
import re
import hashlib
import requests
import yaml
import threading
from pathlib import Path
from dotenv import load_dotenv
from packaging import version

# Initialize Env
load_dotenv()

class NodeFactory:
    _lock = threading.Lock()

    def __init__(self, model_name: str, provider: str = "auto", api_key: str = None):
        # Initialize LLM
        mistral_key = api_key or os.getenv("MISTRAL_API_KEY")
        hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        
        # Logical Provider Selection
        if provider == "transformers":
            # Default to ALIA 40B GGUF for efficient local execution
            repo_id = "BSC-LT/ALIA-40b-instruct-2512-GGUF"
            filename = "ALIA-40b-instruct-2512-Q8_0.gguf"
            print(f"🏠 Loading Local Spanish Model (ALIA 40B GGUF): {repo_id}/{filename}")
            try:
                from huggingface_hub import hf_hub_download
                from langchain_community.chat_models import ChatLlamaCpp

                # Ensure model is downloaded and get local path
                model_path = hf_hub_download(repo_id=repo_id, filename=filename)

                self.llm = ChatLlamaCpp(
                    model_path=model_path,
                    temperature=0.1,
                    max_tokens=4096,
                    top_p=1,
                    n_ctx=16384,
                    n_gpu_layers=-1,
                    n_batch=512,
                    verbose=False,
                )
            except Exception as e:
                print(f"❌ Error loading ALIA GGUF model: {str(e)}")
                print("🏠 Falling back to local Ollama (mistral)...")
                self.llm = ChatOllama(model="mistral", temperature=0.1)

        elif provider == "cloud" or (provider == "auto" and os.getenv("VENTURALITICA_LLM_PRO", "false").lower() == "true" and mistral_key):
            # Standardize on Magistral for PRO/Cloud
            target_model = "magistral-medium-latest"
            if mistral_key:
                print(f"🌟 Using High-Power Magistral LLM (Mistral AI): {target_model}")
                try:
                    self.llm = ChatMistralAI(
                        api_key=mistral_key,
                        model=target_model,
                        temperature=0.1,
                        max_retries=3,
                        timeout=180,
                    )
                except Exception as e:
                    print(f"  ⚠️ Cloud Connection Failed: {e}. Falling back to Local.")
                    self.llm = ChatOllama(model="mistral", temperature=0.1)
            else:
                print("⚠️ Cloud Provider requested but MISTRAL_API_KEY missing.")
                print("🏠 Falling back to Local Ollama (mistral)...")
                self.llm = ChatOllama(model="mistral", temperature=0.1)
        else:
            # Default: OLLAMA
            target_model = model_name if model_name and "/" not in model_name else "mistral"
            print(f"🏠 Using Local LLM (Ollama): {target_model}")
            self.llm = ChatOllama(model=target_model, temperature=0.1)

    def _load_prompts(self, lang: str = "en"):
        """Loads prompt templates from YAML files based on language."""
        lang_code = "es" if lang.lower().startswith("es") else "en"
        prompt_path = Path(__file__).parent / "prompts" / f"prompts.{lang_code}.yaml"
        
        if not prompt_path.exists():
            print(f"⚠️ Prompts for '{lang_code}' not found at {prompt_path}. Falling back to 'en'.")
            prompt_path = Path(__file__).parent / "prompts" / "prompts.en.yaml"
            
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
        
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

    def _generate_generic_section(self, section_id: str, state: ComplianceState) -> SectionDraft:
        """
        Generic section generator that uses evidence and localized prompts.
        """
        try:
            # 1. Load localized prompts
            target_lang = state.get("language", "English")
            yaml_data = self._load_prompts(target_lang)
            
            section_info = yaml_data.get("sections", {}).get(section_id.replace(".", ""), {})
            if not section_info:
                print(f"  ⚠️ Warning: Prompt for section {section_id} not found in YAML.")
                return {"content": f"Missing prompt for {section_id}", "status": "error"}

            # Context Preparation
            bom_summary = [c['name'] for c in state['bom'].get('components', [])]
            meta_summary = state['runtime_meta'].get('audit_results', 'No audit run yet.')
            
            # Format Code Context (summarized)
            code_summary = ""
            context = state.get("code_context", {})
            for fname, info in context.items():
                if "error" in info:
                    continue
                code_summary += f"\nFile: {fname}"
                if "docstring" in info and info["docstring"]:
                    code_summary += f"\n  - Story/Intent: {info['docstring']}"
                if "functions" in info and info["functions"]:
                    func_names = [f["name"] for f in info["functions"][:10]]
                    code_summary += f"\n  - Logic Hooks: {', '.join(func_names)}"
                if "calls" in info and info["calls"]:
                    formatted_calls = [f"{c['object']}.{c['method']} (L{c['lineno']})" for c in info['calls'][:5]]
                    code_summary += f"\n  - Key Calls: {', '.join(formatted_calls)}"
                if "imports" in info and info["imports"]:
                    code_summary += f"\n  - Stack: {', '.join(info['imports'][:5])}"
                if "raw_source" in info and info["raw_source"]:
                    # Provide an excerpt if too long
                    source = info["raw_source"]
                    excerpt = source[:300] + "..." if len(source) > 300 else source
                    code_summary += f"\n  - Source Excerpt:\n{excerpt}"
            
            # Check for existing draft and feedback
            current_draft = state.get("sections", {}).get(section_id, {})
            previous_content = current_draft.get("content", "")
            feedback = current_draft.get("feedback", None)

            # Cybersecurity specific context
            vuln_text = "N/A"
            if section_id == "2.h":
                security_report = state.get("bom_security", {})
                vuln_text = "No known vulnerabilities detected in supply chain."
                if security_report.get("vulnerable"):
                    issues = security_report.get("issues", [])
                    vuln_text = f"CRITICAL: Found {len(issues)} vulnerabilities in supply chain:\n"
                    for i in issues:
                        vuln_text += f"- {i['package']} {i['version']}: {i['id']} (Severity: {i['severity']})\n"

            # Construct Full Prompt from YAML parts
            full_prompt = yaml_data["system_base"].format(language=target_lang)
            full_prompt += "\n" + yaml_data["context_template"].format(
                bom_data="{bom_data}", 
                meta_data="{meta_data}", 
                code_summary="{code_summary}"
            )
            full_prompt += "\n\n" + section_info["prompt"].format(
                bom="{bom}",
                code="{code}",
                meta="{meta}",
                vuln_text=vuln_text
            )
            
            if feedback and previous_content:
                 print(f"  🔄 Refining Section {section_id} based on critic feedback...")
                 full_prompt += "\n\n" + yaml_data["refinement_template"].format(
                     feedback="{feedback}",
                     language=target_lang
                 )
            
            prompt = ChatPromptTemplate.from_template(full_prompt)
            chain = prompt | self.llm
            
            with self._lock:
                response = chain.invoke({
                    "bom_data": json.dumps(state.get('bom', {}), indent=2),
                    "meta_data": json.dumps(state.get('runtime_meta', {}), indent=2),
                    "code_summary": code_summary,
                    "bom": str(bom_summary),
                    "meta": str(meta_summary),
                    "code": code_summary,
                    "previous_content": previous_content,
                    "feedback": feedback,
                    "language": target_lang
                })
            
            # Clean response from markdown escapes
            raw_content = response.content
            extracted_text = []
            extracted_thinking = []

            def _extract_recursive(data, in_thought=False):
                if isinstance(data, str):
                    if in_thought: extracted_thinking.append(data)
                    else: extracted_text.append(data)
                elif isinstance(data, list):
                    for item in data: _extract_recursive(item, in_thought)
                elif isinstance(data, dict):
                    b_type = data.get("type")
                    if b_type == "text":
                        t = data.get("text", "")
                        if in_thought: extracted_thinking.append(t)
                        else: extracted_text.append(t)
                    elif b_type == "thinking":
                        thought = data.get("thinking", "")
                        _extract_recursive(thought, in_thought=True)

            _extract_recursive(raw_content)
            
            content = "".join(extracted_text).strip()
            thinking = "\n".join(extracted_thinking).strip()

            # Fallback: If content is empty but thinking contains markdown headers,
            # it means the model "thought out loud" the answer.
            if not content and "##" in thinking:
                # Use the thinking as content if it looks like the final doc
                content = thinking
                thinking = None # Move it all to content for the editor

            if content.startswith("```"):
                import re
                content = re.sub(r'^```[a-zA-Z]*\n?', '', content)
                content = re.sub(r'\n?```$', '', content)

            if thinking:
                print(f"  💭 Captured reasoning for {section_id} ({len(thinking)} chars)")

            return {
                "content": content.strip(), 
                "thinking": thinking if thinking else None,
                "status": "completed",
                "feedback": None 
            }
        except Exception as e:
            return {"content": f"Error generating section: {str(e)}", "status": "error", "feedback": None}

    def write_section_2a(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.a: Development Methods"""
        print("✍️  Drafting Section 2.a (Methods)...")
        draft = self._generate_generic_section("2.a", state)
        return {"sections": {**state.get("sections", {}), "2.a": draft}}

    def write_section_2b(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.b: Logic & Assumptions"""
        print("✍️  Drafting Section 2.b (Logic)...")
        draft = self._generate_generic_section("2.b", state)
        return {"sections": {**state.get("sections", {}), "2.b": draft}}

    def write_section_2c(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.c: Architecture"""
        print("✍️  Drafting Section 2.c (Architecture)...")
        draft = self._generate_generic_section("2.c", state)
        return {"sections": {**state.get("sections", {}), "2.c": draft}}

    def write_section_2d(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.d: Data Requirements"""
        print("✍️  Drafting Section 2.d (Data)...")
        draft = self._generate_generic_section("2.d", state)
        return {"sections": {**state.get("sections", {}), "2.d": draft}}

    def write_section_2e(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.e: Human Oversight"""
        print("✍️  Drafting Section 2.e (Oversight)...")
        draft = self._generate_generic_section("2.e", state)
        return {"sections": {**state.get("sections", {}), "2.e": draft}}

    def write_section_2f(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.f: Predetermined Changes"""
        print("✍️  Drafting Section 2.f (Changes)...")
        draft = self._generate_generic_section("2.f", state)
        return {"sections": {**state.get("sections", {}), "2.f": draft}}
        
    def write_section_2g(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.g: Validation"""
        print("✍️  Drafting Section 2.g (Validation)...")
        draft = self._generate_generic_section("2.g", state)
        return {"sections": {**state.get("sections", {}), "2.g": draft}}

    def write_section_2h(self, state: ComplianceState) -> Dict[str, Any]:
        """Section 2.h: Cybersecurity"""
        print("✍️  Drafting Section 2.h (Cybersecurity)...")
        draft = self._generate_generic_section("2.h", state)
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
                with self._lock:
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
        
        return {"final_markdown": md, "sections": sections}

    def critique_document(self, state: ComplianceState) -> Dict[str, Any]:
        """
        Critic Node: Reviews the document and requests revisions.
        """
        print("🧐 Critiquing document...")
        doc = state.get("final_markdown", "")
        revision_count = state.get("revision_count", 0) + 1
        target_lang = state.get("language", "English")
        
        if revision_count > 3:
            print("  ⚠️ Max revisions reached. Forcing approval.")
            return {"critic_verdict": "APPROVE", "revision_count": revision_count}
            
        yaml_data = self._load_prompts(target_lang)
        prompt_text = yaml_data.get("critic_prompt", "Critic prompt missing").format(
            language=target_lang,
            doc="{doc}",
            bom="{bom}",
            code="{code}",
            meta="{meta}"
        )
        
        prompt = ChatPromptTemplate.from_template(prompt_text)
        
        # Prepare summary for critic
        code_summary = ""
        context = state.get("code_context", {})
        for fname, info in context.items():
            code_summary += f"\nFile: {fname}\n  - Story: {info.get('docstring','')}\n  - Logic Hooks: {', '.join([f['name'] for f in info.get('functions',[])[:5]])}"

        chain = prompt | self.llm
        try:
            with self._lock:
                response = chain.invoke({
                    "doc": doc,
                    "bom": json.dumps(state.get('bom', {}), indent=2),
                    "code": code_summary,
                    "meta": json.dumps(state.get('runtime_meta', {}), indent=2),
                    "language": target_lang
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
                    with self._lock:
                        response = chain.invoke({"text": text_to_translate, "target_lang": lang_name})
                    raw_content = response.content
                    
                    # For translation, we prioritize the text and ignore thinking
                    extracted_text = []
                    def _extract_text(data):
                        if isinstance(data, str): extracted_text.append(data)
                        elif isinstance(data, list):
                            for i in data: _extract_text(i)
                        elif isinstance(data, dict):
                            if data.get("type") == "text":
                                extracted_text.append(data.get("text", ""))
                    
                    _extract_text(raw_content)
                    content = "".join(extracted_text).strip()

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
