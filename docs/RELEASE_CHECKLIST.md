# v0.6.x Release Checklist

## E2 — TestPyPI smoke (v0.6.0)

- Date: 2026-05-01
- Branch SHA: `9678dc2` on `staging`
- Workflow: `Publish` → `testpypi` env → completed success.
- TestPyPI: <https://test.pypi.org/project/venturalitica/0.6.0/>
- Smoke install: `uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ --index-strategy unsafe-best-match venturalitica==0.6.0` → installed.
- `python -c "import venturalitica; print(venturalitica.__version__)"` → `0.6.0` ✅
- 5 public symbols import OK: `enforce, monitor, wrap, quickstart, PolicyManager`.
- **Issue surfaced**: `vl` binary missing. Docs reference `vl pull/push/login/ui` but pyproject only declared `venturalitica` script. Hotfixed in v0.6.1.

## D9 — v0.6.1 hotfix (vl CLI alias)

- Date: 2026-05-01
- Branch SHA: `658c912` on `staging`
- Change: `[project.scripts]` adds `vl = "venturalitica.cli:app"`. Both binaries dispatch to the same Typer app.
- Workflow: `Publish` v0.6.1 → `testpypi` env → completed success.
- TestPyPI: <https://test.pypi.org/project/venturalitica/0.6.1/>
- Smoke install: same command with `==0.6.1` (after TestPyPI index propagated, `--refresh` flag needed once).
- `vl --help` → Typer Usage banner with 5 subcommands (export-annex-iv, login, ui, pull, push) ✅
- `venturalitica --help` → identical Typer app ✅
- `python -c "import venturalitica; print(venturalitica.__version__)"` → `0.6.1` ✅
- CI workflow on `658c912`: completed success (coverage gate 80% met, measured 84%).

## F3 — Notebooks against TestPyPI wheel (v0.6.1)

- Date: 2026-05-01
- Source: `notebooks/00-quickstart.ipynb`, `notebooks/01-training-tutorial.ipynb` from the repo, executed against v0.6.1 TestPyPI wheel.
- Tooling: `jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=180`.
- 00-quickstart.ipynb: 5 cells, **0 errors** (12034 bytes output).
- 01-training-tutorial.ipynb: 13 cells, **0 errors** (24149 bytes output).
- Both notebooks complete without exceptions; the bundled `policy.oscal.yaml` is consumed correctly by the published wheel.

## F4 — Streamlit dashboard E2E (Playwright mission lifecycle)

- Date: 2026-05-01
- Branch: `feature/v060-release-stabilization`
- Branch SHA: `8274d63b2848a25c2affef5dee9856c5ff8cdff9`
- Test file: `tests/e2e/test_dashboard_missions.py`
- Result: **PARTIAL / DEFERRED to v0.6.1**
- Runtime: ~57s before failure (Step 3 of 7)
- Marker: `pytestmark = [pytest.mark.e2e]` added; marker registered in
  `tests/e2e/conftest.py` via `pytest_configure` to avoid touching
  in-flight `pyproject.toml`.

### Environment

- `streamlit==1.57.0` installed via `uv sync --extra dashboard`.
- `playwright==1.59.0` + `pytest-playwright==0.7.2` installed via
  `uv pip install` (transient — not pinned in `pyproject.toml`,
  considered dev-only).
- Chromium binary already present at `~/.cache/ms-playwright/chromium-1217`.
  Playwright refused fresh install on Ubuntu 26.04 (officially unsupported
  host) but the cached binary launches fine.

### Triage

- **Step 1 (System Identity)**: PASS after surgical rename
  `"Start Mission 1"` → `"Start Step 1"` (UI was renamed
  Mission→Step in the home cards in v0.6.0; see
  `src/venturalitica/dashboard/main.py:270`).
- **Step 2 (Data Policy)**: PASS — uses programmatic fallback,
  bypasses UI.
- **Step 3 (Model Policy via UI)**: FAIL — Playwright cannot find
  `input[type="number"]` inside the "Add Control" `stVerticalBlock`.
  Root cause is Streamlit DOM-selector fragility / Streamlit version
  drift from when the test was authored. The `Add Control` subheader,
  `Add Rule` button, and `st.number_input("Threshold", ...)` widget
  all still exist in `src/venturalitica/dashboard/views/policy_editor.py:188-225`,
  so this is selector drift, not feature loss.
- Steps 4–7 not exercised.

### Recommendation

Defer the deep selector rewrite to v0.6.1. The test is environmentally
stable (browser launches, Streamlit boots, Step 1 + Step 2 pass), so
it remains valuable as scaffolding. For v0.6.0 ship:

1. Keep `pytestmark = [pytest.mark.e2e]` so default `pytest` runs skip
   it (already enforced via `addopts = "--ignore=tests/e2e"` in
   `pyproject.toml`).
2. v0.6.1: rewrite `_add_control_ui()` with stabler selectors
   (prefer `page.get_by_label("Threshold")` over nested
   `stVerticalBlock` filters), and re-validate Steps 4–7.

### Artifacts

- Failure video: `tests/e2e/videos/page@2a269e90d5b2432ecf288610cbbe3cd5.webm`
- Reference policy fixtures verified at
  `venturalitica-sdk-samples/scenarios/loan-credit-scoring/policies/loan/`.
