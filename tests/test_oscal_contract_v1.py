"""The normative OSCAL contract is compared against the code, every run.

`docs/contracts/oscal-contract-v1.md` replaces a contract that was deleted in the 0.6.4 hotfix.
Measured on 2026-09-14, that one's two leading invariants were INVERTED with respect to the code:
they required the envelope this SDK now refuses and denied the one that is now canonical. The
canonical root migrated in May 2026 and the contract did not move with it.

It was typed, versioned and normative. What it lacked was a way to expire. This file is that way.

If the code moves and the contract does not, these tests fail and name the file. The right
response is to RE-MEASURE THE CONTRACT, not to edit the expected value until the test passes.
"""
import re
from pathlib import Path

import pytest
import yaml

from venturalitica.loader import OSCALPolicyLoader
from venturalitica.oscal.models import OSCAL_VERSION

CONTRATO = Path(__file__).resolve().parents[1] / "docs" / "contracts" / "oscal-contract-v1.md"


def _hechos() -> dict:
    """The machine-checked block at the top of the contract."""
    texto = CONTRATO.read_text(encoding="utf-8")
    bloque = re.search(r"```yaml\n(.*?)```", texto, re.S)
    assert bloque, "the contract no longer carries its machine-checked block"
    return yaml.safe_load(bloque.group(1))


def test_el_contrato_existe_y_el_readme_puede_citarlo():
    """A normative reference that does not resolve is a defect, not a typo — the repository's own
    CLAUDE.md says so, and the previous contract's absence is why this one exists."""
    assert CONTRATO.is_file(), f"the normative contract is missing at {CONTRATO}"


def test_el_sobre_retirado_se_rechaza(tmp_path):
    """A2, and the reason this whole file exists.

    The retired `assessment-plan` envelope was refused only incidentally — by not appearing in the
    accepted list — and nothing named it. Putting it back would have broken no test. This is the
    exact invariant the previous contract had backwards, so it is the one that gets a test of its
    own rather than being left to the generic unsupported-root case.

    Loading empty would be worse than raising: every control would be skipped and the run would
    report clean.
    """
    ruta = tmp_path / "politica-retirada.yaml"
    ruta.write_text(yaml.dump({
        "assessment-plan": {
            "metadata": {"title": "legacy", "version": "1.0"},
            "control-implementations": [{
                "uuid": "impl-1",
                "implemented-requirements": [{
                    "control-id": "C1",
                    "props": [
                        {"name": "metric_key", "value": "accuracy_score"},
                        {"name": "operator", "value": "ge"},
                        {"name": "threshold", "value": "0.8"},
                    ],
                }],
            }],
        }
    }))
    with pytest.raises(ValueError, match="Unsupported OSCAL format"):
        OSCALPolicyLoader(str(ruta)).load()


def test_las_raices_aceptadas_son_las_que_el_contrato_declara(tmp_path):
    """Each root the contract lists as accepted actually loads, and the canonical one is among
    them. Checked by feeding the loader a minimal document under each root rather than by reading
    the loader's source: a contract verified against the implementation's own literals would agree
    with itself by construction."""
    hechos = _hechos()
    # An empty list would make every loop below vacuous and this test green without having
    # checked anything — the same defect as a validator that exits 0 on an empty corpus. The
    # contract is asserted to still say something before its contents are checked.
    assert hechos["policy_roots_accepted"], "the contract lists no accepted root at all"
    for raiz in hechos["policy_roots_accepted"]:
        ruta = tmp_path / f"{raiz}.yaml"
        ruta.write_text(yaml.dump({raiz: {"metadata": {"title": raiz}}}))
        politica = OSCALPolicyLoader(str(ruta)).load()
        assert politica is not None, f"the contract says `{raiz}` is accepted and it is not"
    assert hechos["policy_root_canonical"] in hechos["policy_roots_accepted"]


def test_las_raices_rechazadas_son_las_que_el_contrato_declara(tmp_path):
    hechos = _hechos()
    # Same trap, and here it is the dangerous one: emptying this list is exactly how the retired
    # envelope would quietly become acceptable again, and a vacuous loop would report green while
    # the contract's central invariant disappeared.
    assert "assessment-plan" in hechos["policy_roots_refused"], (
        "the contract no longer refuses `assessment-plan`. That is the invariant the previous "
        "contract had inverted; removing it needs a measurement, not an edit."
    )
    for raiz in hechos["policy_roots_refused"]:
        ruta = tmp_path / f"{raiz}.yaml"
        ruta.write_text(yaml.dump({raiz: {"metadata": {"title": raiz}}}))
        with pytest.raises(ValueError):
            OSCALPolicyLoader(str(ruta)).load()


def test_la_version_oscal_del_contrato_es_la_que_el_emisor_declara():
    """The binding that expires the contract when the emitter migrates."""
    hechos = _hechos()
    assert hechos["oscal_version"] == OSCAL_VERSION, (
        f"the contract declares OSCAL {hechos['oscal_version']} and the emitter declares "
        f"{OSCAL_VERSION}. RE-MEASURE {CONTRATO.name} against the code; do not edit the expected "
        "value until this passes."
    )


def test_el_contrato_declara_las_raices_de_salida_que_el_emisor_EMITE():
    """B1 and B4, checked against an emitted document rather than against the emitter's source.

    The first version of this test grepped `builder.py` for the root names and failed, because the
    names are not literals there. That failure was correct and the test was wrong: reading the
    source to confirm what the source produces is the same defect this repository refuses
    elsewhere — a verdict read from the instrument instead of from what it measured.
    """
    import json

    from venturalitica.models import ComplianceResult
    from venturalitica.oscal.builder import AssessmentResultsBuilder, POAMBuilder
    from venturalitica.oscal.serializer import to_json

    hechos = _hechos()
    fallo = ComplianceResult(
        control_id="contract-check",
        description="a failing control, so that the remediation document is emitted too",
        metric_key="disparate_impact",
        threshold=0.8,
        actual_value=0.4,
        operator="gt",
        passed=False,
        severity="high",
    )
    ar = AssessmentResultsBuilder.build([fallo])
    assert hechos["evidence_root"] in json.loads(to_json(ar)), (
        f"the contract declares `{hechos['evidence_root']}` as the evidence root and the emitted "
        f"document is not rooted there. RE-MEASURE {CONTRATO.name}."
    )

    poam = POAMBuilder.build(ar)
    assert poam is not None, "a failing control has to produce a remediation document (B4)"
    assert hechos["remediation_root"] in json.loads(to_json(poam)), (
        f"the contract declares `{hechos['remediation_root']}` as the remediation root and the "
        f"emitted document is not rooted there. RE-MEASURE {CONTRATO.name}."
    )


def test_el_contrato_declara_la_divergencia_conocida():
    """The dashboard's policy form still writes the envelope A2 refuses. While that is true, the
    contract has to say so: a contract that described only the parts that agree would be a
    description of what we wish were true, which is the defect that produced the document this one
    replaces.

    When the divergence is fixed, this test fails — and the right fix is to remove the section
    from the contract, not to delete this test.
    """
    editor = Path(__file__).resolve().parents[1] / "src" / "venturalitica" / "dashboard" / "views" / "policy_editor.py"
    sigue_divergiendo = '"assessment-plan": {' in editor.read_text(encoding="utf-8")
    declarada = "Known divergence" in CONTRATO.read_text(encoding="utf-8")
    assert sigue_divergiendo == declarada, (
        "the dashboard writes the retired envelope and the contract no longer says so, or the "
        "other way round. Both states are wrong: the contract must declare the divergence for "
        "exactly as long as it exists."
    )
