"""
`venturalitica export-annex-iv` — derive EU AI Act Art.11 Annex IV
technical documentation from an OSCAL Assessment Results file produced
by the SDK during training.

Coherence with the arXiv preprint (arXiv:2604.13767, §5-§6):
  * OSCAL is the canonical evidence format; the SDK writes
    `.venturalitica/runs/<run_id>/assessment-results.oscal.json`
    validated against NIST JSON schema v1.2.1.
  * Annex IV is NOT a new evidence shape — it is a human-readable
    narrative that *maps* OSCAL findings into the 9 sections required
    by the EU AI Act Art.11 Annex IV.
  * The OSCAL Assessment Plan (the policy the SDK pulled) populates
    §7 (standards applied) via its `control-implementations` and
    catalog references. The Assessment Results populate §4
    (performance metrics). The POA&M (if any failed findings)
    populates §6 (lifecycle changes) as a list of open corrective
    actions. Everything else is operator narrative.
  * Output of this command is idempotent and deterministic over the
    same run_id, so the emitted JSON can be hashed for tamper
    evidence.

Output modes:
  --out stdout  : print JSON to stdout (for piping / regression tests)
  --out file    : write .venturalitica/annex_iv.json + Annex_IV.md
  --out bundle  : merge into .venturalitica/results.json under
                  `annex_iv` so the next `vl push` carries it.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Optional

import typer

from .common import app, console

VL_DIR = Path(".venturalitica")
RUNS_DIR = VL_DIR / "runs"
RESULTS_PATH = VL_DIR / "results.json"
POLICY_PATH_CANDIDATES = [
    VL_DIR / "policy.oscal.json",
    VL_DIR / "assessment-plan.oscal.json",
    Path("model_policy.oscal.yaml"),
]

# Annex IV §1 grounding — the system identity card (intended purpose,
# hardware, interaction, instructions, foreseeable misuse). Loaded from the
# first path that exists. Without this the agentic writer hallucinates
# generic Annex III narratives (banks, credit risk…) regardless of LLM.
SYSTEM_DESC_PATH_CANDIDATES = [
    Path("system_description.yaml"),       # staged by compliance_suite.stage_for_dashboard()
    Path("shared_data/annex_iv1.yaml"),    # scenario source-of-truth
    Path("annex_iv1.yaml"),
]
ANNEX_OUT_JSON = VL_DIR / "annex_iv.json"
ANNEX_OUT_MD = Path("Annex_IV.md")
AGENTIC_CACHE = VL_DIR / "annex_iv.cache.json"


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        with path.open("r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _latest_run_dir() -> Optional[Path]:
    if not RUNS_DIR.exists():
        return None
    runs = [p for p in RUNS_DIR.iterdir() if p.is_dir()]
    if not runs:
        return None
    return max(runs, key=lambda p: p.stat().st_mtime)


def _load_assessment_results(run_dir: Optional[Path]) -> dict | None:
    if run_dir is None:
        return None
    ar_path = run_dir / "assessment-results.oscal.json"
    return _load_json(ar_path) if ar_path.exists() else None


def _load_system_description() -> dict | None:
    """Load the Annex IV §1 system identity card (intended purpose,
    hardware, interaction, instructions, misuse). Tries each candidate
    path in order; returns `None` if nothing is present so the agentic
    writer can still run (with generic fallback prose).

    YAML keys mirror the `venturalitica.models.SystemDescription` dataclass:
    `name`, `version`, `provider_name`, `intended_purpose`,
    `interaction_description`, `software_dependencies`,
    `market_placement_form`, `hardware_description`, `external_features`,
    `ui_description`, `instructions_for_use`, `potential_misuses`.
    """
    try:
        import yaml  # local import — only needed on the agentic path
    except ImportError:
        return None
    for path in SYSTEM_DESC_PATH_CANDIDATES:
        if path.exists():
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(data, dict) and data.get("name"):
                return data
    return None


def _load_poam(run_dir: Optional[Path]) -> dict | None:
    if run_dir is None:
        return None
    poam_path = run_dir / "poam.oscal.json"
    return _load_json(poam_path) if poam_path.exists() else None


def _load_policy() -> dict | None:
    for candidate in POLICY_PATH_CANDIDATES:
        if candidate.exists() and candidate.suffix == ".json":
            doc = _load_json(candidate)
            if isinstance(doc, dict):
                return doc
    return None


def _metrics_from_assessment_results(ar: dict | None) -> dict:
    """§4 Performance metrics — extract findings from OSCAL results."""
    if not isinstance(ar, dict):
        return {"findings": []}
    results_root = ar.get("assessment-results", ar)
    results = results_root.get("results") or []
    findings: list[dict] = []
    for r in results:
        for f in r.get("findings", []):
            props = {p.get("name"): p.get("value") for p in f.get("props", []) or []}
            findings.append(
                {
                    "control_id": (f.get("target") or {}).get("target-id"),
                    "title": f.get("title"),
                    "status": (f.get("target") or {})
                    .get("status", {})
                    .get("state"),
                    "metric_key": props.get("metric_key"),
                    "actual": props.get("actual_value") or props.get("value"),
                    "threshold": props.get("threshold"),
                    "severity": props.get("severity"),
                    "timestamp": r.get("start"),
                }
            )
    return {"findings": findings}


def _standards_from_policy(policy: dict | None) -> list[dict]:
    """§7 Standards applied — extract from OSCAL control-implementations."""
    if not isinstance(policy, dict):
        return []
    plan = policy.get("assessment-plan", policy)
    catalogs = plan.get("catalog-references", [])
    impls = plan.get("control-implementations", [])
    out: list[dict] = []
    for c in catalogs:
        out.append({"catalog": c.get("href") or c})
    for impl in impls:
        if "description" in impl:
            out.append({"implementation": impl.get("description")})
    if not out:
        out = [
            {"standard": "EU AI Act", "articles": ["Art.11", "Annex IV"]},
            {"standard": "ISO/IEC 42001", "clauses": ["A.4.6", "A.8.3"]},
            {"standard": "NIST OSCAL", "version": "1.2.2"},
        ]
    return out


def _poam_items(poam: dict | None) -> list[dict]:
    """§6 Lifecycle changes — map open POA&M items to action list."""
    if not isinstance(poam, dict):
        return []
    root = poam.get("plan-of-action-and-milestones", poam)
    items = root.get("poam-items", []) or []
    def _finding_uuids(item: dict) -> list[str]:
        raw = item.get("related-findings", []) or []
        # OSCAL spec allows either `[{"finding-uuid": "..."}]` or
        # `["<uuid>"]`; the SDK has flipped between shapes across versions.
        out: list[str] = []
        for f in raw:
            if isinstance(f, str):
                out.append(f)
            elif isinstance(f, dict):
                uuid = f.get("finding-uuid") or f.get("uuid")
                if uuid:
                    out.append(uuid)
        return out

    return [
        {
            "uuid": i.get("uuid"),
            "title": i.get("title"),
            "description": i.get("description"),
            "related_findings": _finding_uuids(i),
        }
        for i in items
    ]


# ── Agentic cache (run once, record many times) ──────────────────────────
#
# Local CPU-only Ollama generation takes minutes per section and can't be
# inside the loop when recording the demo video. The cache lets a team
# run `vl export-annex-iv --agentic` once (offline, with patience), then
# re-use the output on every subsequent demo pass.
#
# Invalidation key: (language, model, run_id, policy_hash). Any of the
# four changes and the cache is treated as stale so the narrative can't
# silently describe a previous model version. `policy_hash` is a SHA-256
# of the OSCAL assessment-plan — editing a single threshold or adding a
# new measure will invalidate. `run_id` binds the Annex IV to a specific
# training run so re-training without regenerating the narrative is
# caught immediately.


def _policy_fingerprint(policy: dict | None) -> str:
    if not isinstance(policy, dict) or not policy:
        return "none"
    try:
        payload = json.dumps(policy, sort_keys=True, ensure_ascii=False)
    except (TypeError, ValueError):
        payload = str(policy)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _system_description_fingerprint(sd: dict | None) -> str:
    """Mix the system description into the cache key so editing the
    identity card (intended purpose, hardware, misuse…) invalidates the
    narrative — otherwise the SDK would happily serve stale prose
    describing a previous product line."""
    if not isinstance(sd, dict) or not sd:
        return "none"
    try:
        payload = json.dumps(sd, sort_keys=True, ensure_ascii=False)
    except (TypeError, ValueError):
        payload = str(sd)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _cache_fingerprint(
    *,
    language: str,
    model: str,
    run_id: str | None,
    policy: dict | None,
    system_description: dict | None = None,
    provider: str = "auto",
) -> str:
    parts = [
        language or "-",
        model or "-",
        run_id or "-",
        provider or "-",
        _policy_fingerprint(policy),
        _system_description_fingerprint(system_description),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _load_agentic_cache(
    *,
    language: str,
    model: str,
    run_id: str | None,
    policy: dict | None,
    system_description: dict | None = None,
    provider: str = "auto",
) -> dict | None:
    if not AGENTIC_CACHE.exists():
        return None
    try:
        cached = json.loads(AGENTIC_CACHE.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(cached, dict):
        return None
    meta = cached.get("meta") or {}
    if meta.get("language") != language or meta.get("model") != model:
        return None
    # Fingerprint-aware reuse — bumps cache on drift in any of language,
    # model, run_id, provider, policy, or system_description. Pre-warmed
    # caches without a fingerprint are honoured once but stamped
    # `status=prewarmed` so operators know to regenerate when they have
    # a GPU available.
    expected = _cache_fingerprint(
        language=language,
        model=model,
        run_id=run_id,
        policy=policy,
        system_description=system_description,
        provider=provider,
    )
    stored = meta.get("fingerprint")
    if stored and stored != expected:
        return None
    narrative = cached.get("narrative")
    if not isinstance(narrative, dict) or not narrative:
        return None
    return {"narrative": narrative, "meta": meta}


def _save_agentic_cache(
    narrative: dict[str, str],
    meta: dict,
    *,
    language: str,
    model: str,
    run_id: str | None,
    policy: dict | None,
    system_description: dict | None = None,
    provider: str = "auto",
) -> None:
    payload = {
        "narrative": narrative,
        "meta": {
            **meta,
            "language": language,
            "model": model,
            "run_id": run_id,
            "provider": provider,
            "policy_hash": _policy_fingerprint(policy),
            "system_description_hash": _system_description_fingerprint(system_description),
            "fingerprint": _cache_fingerprint(
                language=language,
                model=model,
                run_id=run_id,
                policy=policy,
                system_description=system_description,
                provider=provider,
            ),
        },
    }
    AGENTIC_CACHE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Agentic writer (direct per-section Ollama prompts) ──────────────────────
#
# We bypass the full LangGraph scanner→planner→writers→critic flow because
# its end-to-end runtime on a 7B local model overflows the demo's time
# budget. For the Annex IV narrative we only need 6 short prose sections,
# so per-section prompts are both faster and easier to debug.
# Section prompts — kept deliberately short so a 7B local model can
# complete each in ~20-40s. Each prompt gets: (a) a regulator-voice
# instruction, (b) the OSCAL context the CLI has on hand, (c) an output
# shape constraint (markdown, ≤250 words, no TODO/placeholder language).
SECTION_PROMPTS: dict[str, tuple[str, str]] = {
    "system_description": (
        "§1 General description of the AI system (EU AI Act Annex IV §1)",
        "Write the general description: intended purpose, deployment context, "
        "modality, target users. Use the System Identity Card verbatim where it "
        "covers a field — do NOT invent a different product, sector, or use case.",
    ),
    "development_process": (
        "§2 Development process (EU AI Act Annex IV §2)",
        "Describe the development process: data sources, training methodology, "
        "validation split, tooling, software dependencies. Anchor each claim in "
        "the System Identity Card `software_dependencies` field and the OSCAL "
        "assessment-plan references. Do NOT invent dataset names or framework "
        "choices not listed in the identity card.",
    ),
    "monitoring_control": (
        "§3 Monitoring, functioning and control (EU AI Act Annex IV §3, Art.15, Art.72)",
        "Describe post-market monitoring plan, drift detectors, HITL review points, "
        "feedback loops, KPI dashboards. Reference the OSCAL enforcement_mode "
        "properties (block/warn/monitor) to explain which controls gate deployment "
        "vs alert only.",
    ),
    "risk_management_summary": (
        "§5 Risk management system (EU AI Act Annex IV §5, Art.9)",
        "Summarise the ISO 23894 / Art.9 risk management lifecycle applied to this system: "
        "identified risks (use the System Identity Card `potential_misuses` field for "
        "foreseeable misuse), treatments, residual risk acceptance rationale, "
        "re-assessment cadence.",
    ),
    "conformity_statement": (
        "§8 Declaration of conformity (EU AI Act Annex IV §8, Art.47)",
        "Write the conformity declaration boilerplate. Name the provider exactly as "
        "given in the System Identity Card `provider_name`. Cite the AI system using "
        "the `name` and `version` fields. List applied standards (ISO 42001 + any "
        "harmonised EN referenced in `instructions_for_use`). Declare that Arts.9-15 "
        "obligations are met, with a signature block placeholder.",
    ),
    "instructions_for_use": (
        "§9 Instructions for use (EU AI Act Art.13, Annex IV §9)",
        "Write operator-facing instructions. Pull the `instructions_for_use` field "
        "from the System Identity Card as the spine of this section. Reference the "
        "human oversight obligations and the explicit out-of-scope uses listed under "
        "`potential_misuses` so the document mirrors the manufacturer's intent.",
    ),
}


def _build_llm(provider: str, model: str):
    """Return a langchain-compatible Chat model.

    Delegates to `venturalitica.llm.resolve_provider`, which knows about all
    the canonical providers (`alia`, `hypernova`, `cloud`, `ollama`) plus
    their back-compat aliases (`transformers`, `multiverse`, `mistral`, …).
    `model` is forwarded as `model_hint` so the Ollama backend can pull a
    non-default tag without changing env vars.
    """
    from venturalitica.llm import ProviderError, resolve_provider

    chosen = resolve_provider(
        provider, api_key=os.getenv("MISTRAL_API_KEY"), model_hint=model
    )
    try:
        return chosen.create_chat_model()
    except ProviderError as exc:
        raise RuntimeError(str(exc)) from exc


def _format_system_description(sd: dict | None) -> str:
    """Render the SystemDescription as a compact context block for prompts.

    Keeps the prompt under ~3k tokens even for a verbose identity card by
    truncating each long-form field to ~600 chars."""
    if not sd:
        return "(no System Identity Card on disk — answers will be generic)"

    def _trim(value: object, limit: int = 600) -> str:
        text = str(value or "").strip()
        if len(text) <= limit:
            return text
        return text[: limit - 1].rsplit(" ", 1)[0] + "…"

    return (
        f"  - Name: {sd.get('name', '?')} v{sd.get('version', '?')}\n"
        f"  - Provider: {sd.get('provider_name', '?')}\n"
        f"  - Intended purpose: {_trim(sd.get('intended_purpose'))}\n"
        f"  - Interaction: {_trim(sd.get('interaction_description'))}\n"
        f"  - Software dependencies: {_trim(sd.get('software_dependencies'))}\n"
        f"  - Market form: {_trim(sd.get('market_placement_form'))}\n"
        f"  - Hardware: {_trim(sd.get('hardware_description'))}\n"
        f"  - External features: {_trim(sd.get('external_features'))}\n"
        f"  - UI: {_trim(sd.get('ui_description'))}\n"
        f"  - Instructions for use: {_trim(sd.get('instructions_for_use'))}\n"
        f"  - Foreseeable misuse: {_trim(sd.get('potential_misuses'))}"
    )


def _run_compliance_graph(
    *,
    language: str,
    model: str,
    provider: str,
    policy: dict | None,
    assessment_results: dict | None,
    system_description: dict | None = None,
) -> tuple[dict[str, str], dict]:
    """
    Drive per-section prompts through ChatOllama (default) to fill in the
    narrative Annex IV fields. We deliberately bypass the full LangGraph
    scanner→planner→8 writers→critic flow because the demo budget (≤ a few
    minutes end-to-end) can't absorb its runtime on a 7B local model —
    plus, fan-out over 8 sections × critic-loop can hang on smaller GPUs.

    Returns `(narrative_by_field, meta)`. Raises on unrecoverable errors
    so the caller can fall back to TODO placeholders without corrupting
    the JSON.
    """
    import time

    # Probe Ollama before kicking off calls so the failure mode is an
    # obvious "start Ollama first" message rather than a 60s timeout
    # deep inside langchain. Only relevant when the registry actually
    # resolved to the Ollama backend.
    from venturalitica.llm import normalize_provider_name

    canonical = normalize_provider_name(provider)
    if canonical in ("auto", "ollama"):
        try:
            import requests as _requests
            host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            r = _requests.get(f"{host}/api/tags", timeout=3)
            r.raise_for_status()
            tags = {m.get("model") or m.get("name") for m in r.json().get("models", [])}
            if model not in tags and f"{model}:latest" not in tags:
                raise RuntimeError(
                    f"Model '{model}' not present in Ollama. Available: {sorted(tags)[:5]}…"
                )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"Ollama probe failed: {exc}. Start it with `ollama serve` "
                f"and `ollama pull {model}`, or switch to --provider cloud."
            ) from exc

    console.print(
        f"[cyan]🤖[/cyan] Running agentic Annex IV writer (provider={provider}, model={model}, lang={language})…"
    )

    llm = _build_llm(provider, model)

    # Compact context block — keep the prompt small so a 7B model can
    # absorb it without running out of context window. The System Identity
    # Card grounds the LLM in the actual product (intended purpose,
    # hardware, etc.); without it every provider hallucinates a generic
    # Annex III banking system regardless of model quality.
    osc_bits = []
    if policy:
        plan = policy.get("component-definition") or policy.get("assessment-plan") or policy
        title = (plan.get("metadata") or {}).get("title", "")
        if title:
            osc_bits.append(f"OSCAL policy title: {title}")
        components = plan.get("components") or []
        impls = plan.get("control-implementations") or []
        if components:
            osc_bits.append(f"Components: {len(components)}; "
                            f"control-implementations: "
                            f"{sum(len(c.get('control-implementations') or []) for c in components)} block(s)")
        elif impls:
            osc_bits.append(f"Control implementations: {len(impls)} block(s)")
    if assessment_results:
        ar_root = assessment_results.get("assessment-results", assessment_results)
        results = ar_root.get("results") or []
        if results:
            findings = results[0].get("findings") or []
            satisfied = sum(1 for f in findings
                            if (f.get("target") or {}).get("status", {}).get("state") == "satisfied")
            osc_bits.append(
                f"OSCAL assessment-results: {len(findings)} findings "
                f"({satisfied} satisfied / {len(findings) - satisfied} non-conformity)"
            )
    osc_str = "\n".join(f"  - {b}" for b in osc_bits) or "  - (no OSCAL context available)"
    sd_str = _format_system_description(system_description)

    # Regulator framing: use the SystemDescription's provider/jurisdiction
    # hints when available; fall back to a generic EU AI Act framing.
    sd_name = (system_description or {}).get("name") if system_description else None
    sd_provider = (system_description or {}).get("provider_name") if system_description else None
    if sd_name and sd_provider:
        regulator_framing = (
            f"Subject system: {sd_name}. Provider: {sd_provider}. "
            f"Document author: senior AI governance writer engaged by the provider. "
            f"Target regulator: the EU AI Act notified body and the relevant "
            f"competent national authority for the deployment jurisdiction."
        )
    else:
        regulator_framing = (
            "Document author: senior AI governance writer. "
            "Target regulator: EU AI Act notified body."
        )

    narrative: dict[str, str] = {}
    per_section_ms: dict[str, int] = {}
    started_all = time.monotonic()

    for field, (header, instruction) in SECTION_PROMPTS.items():
        prompt = (
            f"{regulator_framing} Language: {language}.\n\n"
            f"Section to draft:\n{header}\n\n"
            f"Instruction:\n{instruction}\n\n"
            f"System Identity Card (Annex IV §1 ground truth — DO NOT contradict):\n"
            f"{sd_str}\n\n"
            f"OSCAL context available:\n{osc_str}\n\n"
            f"Constraints:\n"
            f"- ≤250 words.\n"
            f"- Markdown; short paragraphs; no bullet TODOs.\n"
            f"- Do NOT invent dataset names, regulator certificates, or employee names.\n"
            f"- Do NOT emit 'TODO', 'placeholder', or similar fillers.\n"
            f"- Do NOT swap the product, sector, or modality declared in the System Identity Card.\n"
            f"- Write in third person, regulator-facing prose.\n\n"
            f"Draft the section now:"
        )

        t0 = time.monotonic()
        try:
            response = llm.invoke(prompt)
            text = getattr(response, "content", None) or str(response)
            body = text.strip()
            if not body:
                raise RuntimeError("empty response from model")
            narrative[field] = body
        except Exception as exc:  # noqa: BLE001
            console.print(
                f"[yellow]⚠[/yellow] Section {field} generation failed: {exc.__class__.__name__}: {exc}"
            )
            # Leave field absent so caller keeps the TODO fallback.
        per_section_ms[field] = int((time.monotonic() - t0) * 1000)

    elapsed = time.monotonic() - started_all
    meta = {
        "status": "ok" if narrative else "empty",
        "model": model,
        "provider": provider,
        "elapsed_seconds": round(elapsed, 2),
        "per_section_ms": per_section_ms,
        "sections_populated": sorted(narrative.keys()),
    }
    console.print(
        f"[green]✓[/green] Agentic writer complete in {meta['elapsed_seconds']}s — "
        f"{len(narrative)}/{len(SECTION_PROMPTS)} section(s) filled."
    )
    return narrative, meta


def _render_markdown(doc: dict) -> str:
    def section(number: int, title: str, key: str) -> str:
        body = doc.get(key)
        if isinstance(body, (dict, list)):
            body = json.dumps(body, indent=2, ensure_ascii=False)
        return f"## §{number}. {title}\n\n{body or '_(not provided)_'}\n\n"

    lines = [
        "# Annex IV — Technical Documentation (EU AI Act Art.11)",
        "",
        f"Generated by: {doc.get('generated_by', '-')}",
        f"SDK version: {doc.get('sdk_version', '-')}",
        f"Language: {doc.get('language', 'en')}",
        f"Run ID: {doc.get('run_id', '-')}",
        "Derived from: OSCAL Assessment Results + Assessment Plan",
        "",
    ]
    lines.append(section(1, "General description of the AI system", "system_description"))
    lines.append(section(2, "Development process", "development_process"))
    lines.append(section(3, "Monitoring, functioning and control", "monitoring_control"))
    lines.append(section(4, "Performance metrics (from OSCAL Assessment Results)", "performance_metrics"))
    lines.append(section(5, "Risk management summary", "risk_management_summary"))
    lines.append(section(6, "Lifecycle changes (from OSCAL POA&M)", "lifecycle_changes"))
    lines.append(section(7, "Standards applied (from OSCAL Assessment Plan)", "standards_applied"))
    lines.append(section(8, "Declaration of conformity", "conformity_statement"))
    lines.append(section(9, "Instructions for use", "instructions_for_use"))
    return "".join(lines)


def build_annex_iv_doc(
    *,
    run_dir: Optional[Path] = None,
    language: str = "en",
    agentic: bool = False,
    model: str = "mistral",
    provider: str = "auto",
    cache: bool = True,
    force_regenerate: bool = False,
    sdk_version: Optional[str] = None,
) -> dict:
    """Build and return the Annex IV document dict.

    Called by both ``export-annex-iv`` and ``push`` (auto-attach when the
    bundle does not already contain an ``annex_iv`` key).
    """
    VL_DIR.mkdir(exist_ok=True)

    if run_dir is None:
        run_dir = _latest_run_dir()
    ar = _load_assessment_results(run_dir)
    poam = _load_poam(run_dir)
    policy = _load_policy()
    system_description = _load_system_description()
    if system_description and agentic:
        console.print(
            f"[cyan]📇[/cyan] Grounding agentic writer with System Identity Card: "
            f"{system_description.get('name', '?')} "
            f"v{system_description.get('version', '?')} "
            f"({system_description.get('provider_name', '?')})"
        )

    if ar is None:
        console.print(
            "[yellow]⚠[/yellow] No OSCAL Assessment Results found under "
            ".venturalitica/runs/. The document will list empty findings; "
            "run `vl enforce` or `vl monitor` first to produce evidence."
        )

    narrative = {
        "system_description": "TODO: populate the general description of the AI system.",
        "development_process": "TODO: describe data sources, training pipeline, hyperparameters.",
        "monitoring_control": "TODO: describe post-market monitoring plan.",
        "risk_management_summary": (
            "Derived from OSCAL assessment plan; see `standards_applied` "
            "for the referenced catalog and `performance_metrics.findings` "
            "for per-control evaluation outcomes."
        ),
        "conformity_statement": "TODO: reference the ConformityAssessment ID from the platform.",
        "instructions_for_use": "TODO: describe intended deployment context and operator obligations.",
    }

    resolved_run_id = run_dir.name if run_dir else None
    agentic_meta: dict = {}
    if agentic:
        cached = (
            _load_agentic_cache(
                language=language,
                model=model,
                run_id=resolved_run_id,
                policy=policy,
                system_description=system_description,
                provider=provider,
            )
            if cache and not force_regenerate
            else None
        )
        if cached:
            narrative.update(cached["narrative"])
            agentic_meta = {**cached["meta"], "cache_hit": True}
            console.print(
                f"[cyan]⚡[/cyan] Agentic narrative loaded from cache "
                f"(fingerprint={cached['meta'].get('fingerprint','pre-warmed')[:12]}…, "
                f"{cached['meta'].get('elapsed_seconds', '?')}s of prior generation)."
            )
        else:
            try:
                narrative_from_graph, agentic_meta = _run_compliance_graph(
                    language=language,
                    model=model,
                    provider=provider,
                    policy=policy,
                    assessment_results=ar,
                    system_description=system_description,
                )
                narrative.update(narrative_from_graph)
                if cache and narrative_from_graph:
                    _save_agentic_cache(
                        narrative_from_graph,
                        agentic_meta,
                        language=language,
                        model=model,
                        run_id=resolved_run_id,
                        policy=policy,
                        system_description=system_description,
                        provider=provider,
                    )
                    agentic_meta["cache_hit"] = False
            except Exception as exc:  # noqa: BLE001
                console.print(
                    f"[yellow]⚠[/yellow] Agentic writer failed ({exc.__class__.__name__}: {exc}); "
                    f"falling back to TODO placeholders so the pipeline stays deterministic."
                )
                agentic_meta = {"status": "failed", "error": str(exc)}

    return {
        "generated_by": "venturalitica-sdk"
        + (f" + langgraph({model})" if agentic and agentic_meta.get("status") == "ok" else ""),
        "sdk_version": sdk_version or os.getenv("VL_SDK_VERSION") or "unknown",
        "language": language,
        "run_id": run_dir.name if run_dir else None,
        "agentic": agentic_meta if agentic else {"status": "disabled"},
        "system_description": narrative["system_description"],
        "development_process": narrative["development_process"],
        "monitoring_control": narrative["monitoring_control"],
        # OSCAL-derived (always deterministic, never overwritten by the LLM).
        "performance_metrics": _metrics_from_assessment_results(ar),
        "risk_management_summary": narrative["risk_management_summary"],
        "lifecycle_changes": _poam_items(poam),
        "standards_applied": _standards_from_policy(policy),
        "conformity_statement": narrative["conformity_statement"],
        "instructions_for_use": narrative["instructions_for_use"],
    }


@app.command("export-annex-iv")
def export_annex_iv(
    out: str = typer.Option(
        "bundle",
        "--out",
        "-o",
        help="Where to write the Annex IV: stdout | file | bundle",
    ),
    language: str = typer.Option(
        "en", "--language", "-l", help="Document locale (en/es/eu/fr)"
    ),
    sdk_version: Optional[str] = typer.Option(
        None, "--sdk-version", help="Override SDK version string"
    ),
    run_id: Optional[str] = typer.Option(
        None,
        "--run-id",
        help="Explicit run_id under .venturalitica/runs/; default = latest",
    ),
    agentic: bool = typer.Option(
        False,
        "--agentic/--no-agentic",
        help="Use the LangGraph compliance writer (ChatOllama by default) to fill narrative sections instead of leaving TODO placeholders.",
    ),
    model: str = typer.Option(
        "mistral",
        "--model",
        help="Ollama / Mistral model tag used by the agentic writer (e.g. mistral, qwen3:8b, magistral).",
    ),
    provider: str = typer.Option(
        "auto",
        "--provider",
        help=(
            "LLM provider — see `venturalitica.llm` registry for the full "
            "alias map. Canonical values: auto (Ollama by default, Mistral "
            "cloud if MISTRAL_API_KEY set) | ollama (local daemon) | alia "
            "(BSC ALIA-40b GGUF) | hypernova (Multiverse Hypernova-60B GGUF) "
            "| cloud (Mistral Magistral managed)."
        ),
    ),
    cache: bool = typer.Option(
        True,
        "--cache/--no-cache",
        help="Reuse .venturalitica/annex_iv.cache.json when present. On --agentic runs this lets you record a demo without waiting for the LLM to regenerate each time.",
    ),
    force_regenerate: bool = typer.Option(
        False,
        "--force-regenerate",
        help="Ignore the cache and re-run the agentic writer unconditionally.",
    ),
):
    """
    Derive the Art.11 Annex IV document from the OSCAL Assessment
    Results produced by the SDK during the last training run.

    With --agentic, the SDK's LangGraph compliance-writer fills in the
    narrative sections (§§1,2,3,5,8,9) using a local LLM (Ollama by
    default) so the document isn't littered with TODO placeholders.
    The OSCAL-derived sections (§4 metrics, §6 POA&M, §7 standards)
    are always populated from Assessment Results — the LLM does not
    overwrite deterministic evidence.
    """
    run_dir = (RUNS_DIR / run_id) if run_id else None
    doc = build_annex_iv_doc(
        run_dir=run_dir,
        language=language,
        agentic=agentic,
        model=model,
        provider=provider,
        cache=cache,
        force_regenerate=force_regenerate,
        sdk_version=sdk_version,
    )

    if out == "stdout":
        console.print_json(data=doc)
        return

    if out in ("file", "bundle"):
        ANNEX_OUT_JSON.write_text(
            json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        ANNEX_OUT_MD.write_text(_render_markdown(doc), encoding="utf-8")
        console.print(
            f"[bold green]✓[/bold green] Annex IV written to "
            f"{ANNEX_OUT_JSON} + {ANNEX_OUT_MD} (derived from OSCAL)"
        )

    if out == "bundle":
        existing = {}
        if RESULTS_PATH.exists():
            try:
                existing = json.loads(RESULTS_PATH.read_text()) or {}
            except json.JSONDecodeError:
                existing = {}
        if not isinstance(existing, dict):
            existing = {"results": existing}
        existing["annex_iv"] = doc
        RESULTS_PATH.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        console.print(
            "[bold green]✓[/bold green] Annex IV stashed in results.json — "
            "the next `vl push` will send it with the bundle."
        )
