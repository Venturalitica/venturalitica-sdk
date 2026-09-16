"""The openspec guardians are inside the chain of the single required check.

Why this lives in the pytest suite and not as a step inside the `openspec` job: a check that
lives inside the job it protects cannot notice its own absence. Unwire the job from `ci-gate` and
a step inside it still runs and still passes, while the ruleset stops caring whether it passed.
Running the check in the `test` job — which is already required — means unwiring the guardian
while leaving it in place turns this suite red.

What this does NOT cover, stated rather than papered over: deleting the `openspec` job and this
test in the same change. No automated guard survives its own deletion. That one is closed by
review.

`ci-gate` is the single required check on `main`, and the workflow already carries the warning in
its own comments: a job outside `ci-gate.needs` is decorative.
"""
from pathlib import Path

import yaml

CI = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"


def _jobs():
    return yaml.safe_load(CI.read_text())["jobs"]


def _pasos(job):
    return " ".join(str(p.get("run", "")) for p in job.get("steps", []))


def test_el_job_openspec_esta_en_la_cadena_de_ci_gate():
    jobs = _jobs()
    assert "openspec" in jobs, "the `openspec` job has disappeared from the workflow"
    needs = jobs["ci-gate"]["needs"]
    assert "openspec" in needs, (
        "`openspec` is not in `ci-gate.needs`, so the only required check on `main` does not wait "
        f"for it: the guardian would run and be ignored. needs={needs}"
    )


def test_ci_gate_comprueba_el_resultado_de_openspec_y_no_solo_lo_espera():
    """Listing a job in `needs` makes the gate wait for it; it does not make the gate read its
    result. With `if: always()` a failed dependency does not fail this job automatically, which is
    why the gate loops over the results explicitly."""
    guion = _pasos(_jobs()["ci-gate"])
    assert "needs.openspec.result" in guion, (
        "`ci-gate` waits for `openspec` but never reads its result, so an openspec failure would "
        "not fail the gate"
    )


def test_los_tres_guardianes_del_job_openspec_corren_con_sus_falsadores():
    guion = _pasos(_jobs()["openspec"])
    for script in (
        "openspec-gate.test.sh",
        "trazabilidad.test.sh",
        "aceptacion.test.sh",
        "openspec-gate.sh",
        "trazabilidad.sh",
        "aceptacion.sh",
    ):
        assert script in guion, f"the `openspec` job no longer runs {script}"
    assert guion.index("openspec-gate.test.sh") < guion.index("openspec-gate.sh"), (
        "the falsifier has to run BEFORE the guardian: if a guardian cannot turn red, that has to "
        "be known before believing its green"
    )
    assert "npm ci --prefix .github/openspec" in guion, (
        "the kit must be installed from the lock, never from PATH: a global binary does not "
        "appear in the commit and its version would not be reconstructible"
    )


def test_el_job_openspec_clona_la_historia_completa():
    """`aceptacion.sh` attributes a claim's introducing commit with `git blame`. On a shallow
    clone blame resolves every line to the grafted commit, so the one check with teeth — that the
    closer is not the author — would compare against the wrong person and could pass by accident.
    A silent wrong answer there is worse than no check."""
    pasos = _jobs()["openspec"]["steps"]
    checkout = next(p for p in pasos if "checkout" in str(p.get("uses", "")))
    assert checkout.get("with", {}).get("fetch-depth") == 0, (
        "the `openspec` job checks out shallow, so `git blame` cannot attribute a claim to the "
        "commit that introduced it"
    )


def test_el_guardian_de_vigencia_corre_donde_se_produce_la_evidencia():
    guion = _pasos(_jobs()["test"])
    assert "--junitxml" in guion, (
        "pytest no longer writes a JUnit report, so `vigencia.sh` has no evidence that any cited "
        "test actually ran"
    )
    assert "vigencia.sh" in guion, "the `test` job no longer runs the currency guardian"
    assert "vigencia.test.sh" in guion, "the currency guardian runs without its falsifier"
    assert guion.index("vigencia.test.sh") < guion.index("vigencia.sh junit.xml"), (
        "the falsifier has to run before the guardian"
    )


def test_el_guardian_de_lo_que_sale_corre_donde_se_construye_el_artefacto():
    """Su sujeto es el paquete, no el árbol, así que vive en el job que lo construye. Y como los
    demás, va precedido de su falsador: si no sabe ponerse rojo, su verde no vale."""
    guion = _pasos(_jobs()["build"])
    assert "que-sale.sh" in guion, "the `build` job no longer runs the shipping guardian"
    assert "que-sale.test.sh" in guion, "the shipping guardian runs without its falsifier"
    assert guion.index("que-sale.test.sh") < guion.index("que-sale.sh"), (
        "the falsifier has to run before the guardian"
    )


def test_el_pin_del_kit_es_exacto_y_no_un_rango():
    """A range makes «the pin» not a value: the kit guardian compares the running binary against
    it, so a range would leave that guardian permanently red."""
    import json

    manifiesto = CI.resolve().parents[1] / "openspec" / "package.json"
    if not manifiesto.exists():
        manifiesto = CI.resolve().parents[1] / ".github" / "openspec" / "package.json"
    pin = json.loads(manifiesto.read_text())["devDependencies"]["@fission-ai/openspec"]
    assert not any(c in pin for c in "^~><* |"), f"the kit pin `{pin}` is a range, not a version"
