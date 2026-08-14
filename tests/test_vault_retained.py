"""La bóveda no puede contradecir al metrics.json autoritativo (#977).

El registro de riesgos del piloto exige dos granularidades (por caso y por
vértebra), así que `vl.enforce` se llama dos veces con particiones
distintas y el pipeline filtra después, leyendo la partición del OSCAL
compilado. Antes de este arreglo, `session.save_results` cacheaba TODO lo
evaluado -- la unión de ambas llamadas -- y esa unión es exactamente lo que
`_generate_oscal_artifacts` convertía en `assessment-results.oscal.json`,
el documento que `vl push` sube. El `metrics.json` autoritativo del
pipeline (tras el filtro) podía decir una cosa y la bóveda otra distinta,
sin ninguna marca de cuál mandaba.
"""
import json
import threading

import pandas as pd
import pytest

import venturalitica as vl
from venturalitica.models import InternalControl, InternalPolicy
from venturalitica.session import GovernanceSession


@pytest.fixture(autouse=True)
def _isolate_session(tmp_path, monkeypatch):
    """Cada test corre en un directorio temporal aislado y sin sesión previa.

    `monkeypatch.setattr` (en vez de reasignar `GovernanceSession._local` a
    pelo) revierte el atributo de clase solo al terminar el test -- si no,
    la sustitución se filtra a cualquier test que corra después en el mismo
    proceso.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(GovernanceSession, "_local", threading.local())


def _k_anonymity_policy(control_id: str) -> InternalPolicy:
    """Una política mínima con un único control de k-anonimato."""
    return InternalPolicy(
        title=f"policy-{control_id}",
        controls=[
            InternalControl(
                id=control_id,
                description="k-anonimato sobre quasi-identificadores",
                severity="medium",
                metric_key="k_anonymity",
                threshold=2.0,
                operator="ge",
                input_mapping={},
                params={"quasi_identifiers": ["age", "zip"]},
            )
        ],
    )


# Partición por caso: 3 pacientes reales, cada uno con su propia combinación
# de quasi-identificadores -> k=1 (grupos de tamaño 1).
_BY_CASE = pd.DataFrame({"age": [40, 55, 70], "zip": ["A", "B", "C"]})

# Partición por vértebra: los mismos 3 pacientes, una fila por vértebra
# tratada -> k=4 (el grupo más pequeño tiene 4 filas), aunque solo hay 3
# personas reales detrás.
_BY_VERTEBRA = pd.DataFrame(
    {
        "age": [40] * 5 + [55] * 4 + [70] * 6,
        "zip": ["A"] * 5 + ["B"] * 4 + ["C"] * 6,
    }
)


def test_la_boveda_guarda_lo_RETENIDO_no_todo_lo_evaluado():
    """El pipeline llama a enforce dos veces con particiones distintas y filtra después.
    Lo que la bóveda guarde tiene que ser lo que sobrevive al filtro, no la suma."""
    session = GovernanceSession.start("piloto")
    try:
        results_case = vl.enforce(data=_BY_CASE, policy=_k_anonymity_policy("PRIV-CASO"))
        results_vertebra = vl.enforce(
            data=_BY_VERTEBRA, policy=_k_anonymity_policy("PRIV-VERTEBRA")
        )
        assert {r.control_id for r in results_case + results_vertebra} == {
            "PRIV-CASO",
            "PRIV-VERTEBRA",
        }

        # El pipeline filtra externamente -- leyendo la partición del OSCAL
        # compilado -- y solo el control por-caso sobrevive al filtro. Eso
        # es lo que el pipeline escribiría en su propio metrics.json.
        vl.retain(results_case)

        # La bóveda de "evaluado" (Dashboard local) sigue viendo la unión
        # completa: eso es intencional, no lo que rompe la contradicción.
        evaluated_on_disk = json.loads(session.results_file.read_text())
        assert {r["control_id"] for r in evaluated_on_disk} == {
            "PRIV-CASO",
            "PRIV-VERTEBRA",
        }

        # Pero lo retenido -- lo único que un `vl push` puede subir -- es
        # SOLO lo que sobrevivió al filtro del pipeline.
        retained_on_disk = json.loads(session.retained_results_file.read_text())
        assert {r["control_id"] for r in retained_on_disk} == {"PRIV-CASO"}
    finally:
        GovernanceSession.stop()


def test_cada_resultado_retenido_declara_sobre_que_particion_se_computo():
    """Sin eso, «lo retenido» es una lista curada a mano: k=41 y k=3 son los dos
    «k-anonimato» y solo el digest de la tabla dice cuál mide pacientes y cuál vértebras."""
    session = GovernanceSession.start("piloto-digest")
    try:
        # Mismo control_id en las dos llamadas: el mismo "k-anonimato" del issue,
        # una vez por caso y otra por vértebra.
        r_case = vl.enforce(data=_BY_CASE, policy=_k_anonymity_policy("PRIV-K"))
        r_vertebra = vl.enforce(data=_BY_VERTEBRA, policy=_k_anonymity_policy("PRIV-K"))

        assert len(r_case) == 1 and len(r_vertebra) == 1
        assert r_case[0].control_id == r_vertebra[0].control_id == "PRIV-K"
        # Los mismos quasi-identificadores, dos tablas distintas: k=1 (pacientes)
        # frente a k=4 (vértebras) -- indistinguibles por control_id solo.
        assert r_case[0].actual_value != r_vertebra[0].actual_value

        vl.retain(r_case + r_vertebra)

        retained_on_disk = json.loads(session.retained_results_file.read_text())
        assert len(retained_on_disk) == 2
        digests = [row["metadata"].get("partition_digest") for row in retained_on_disk]
        # Ningún digest vacío, y las dos particiones tienen que producir
        # digests DISTINTOS -- si no, "k-anonimato" seguiría siendo
        # indistinguible por inspección.
        assert all(digests)
        assert len(set(digests)) == 2
    finally:
        GovernanceSession.stop()


# ---------------------------------------------------------------------------
# El criterio de aceptación real: el DOCUMENTO que sale de la máquina.
#
# La revisión de rama demostró por mutación que romper `_generate_oscal_
# artifacts` para que SIEMPRE lea `results.json` (es decir, deshacer el
# arreglo entero) dejaba los dos tests de arriba en verde -- porque miran
# los cachés JSON, no el `assessment-results.oscal.json` que `vl push`
# realmente sube. Este test cierra ese círculo.
# ---------------------------------------------------------------------------


def _findings_and_observations(run_dir):
    ar = json.loads((run_dir / "assessment-results.oscal.json").read_text())
    ar_root = ar["assessment-results"]
    return ar_root["results"][0]["findings"], ar_root["results"][0]["observations"]


def test_el_ar_que_sube_vl_push_contiene_solo_lo_retenido():
    """Dentro de un `monitor()` real, dos `enforce` sobre particiones distintas
    con el MISMO control_id, `retain()` de una sola, y el AR final tiene que
    quedarse solo con esa -- no con la unión de las dos."""
    run_dir_holder = {}
    with vl.monitor("piloto-ar-real"):
        r_case = vl.enforce(data=_BY_CASE, policy=_k_anonymity_policy("PRIV-K"))
        r_vertebra = vl.enforce(data=_BY_VERTEBRA, policy=_k_anonymity_policy("PRIV-K"))
        vl.retain(r_case)
        run_dir_holder["dir"] = GovernanceSession.get_current().base_dir

    findings, observations = _findings_and_observations(run_dir_holder["dir"])
    # No dos (uno por partición) -- solo el retenido.
    assert len(findings) == 1
    assert len(observations) == 1

    props = {p["name"]: p["value"] for p in observations[0]["props"]}
    # Es el valor de la partición por-caso (k=1), no el de por-vértebra (k=4).
    assert props["actual-value"] == str(r_case[0].actual_value)
    assert props["actual-value"] != str(r_vertebra[0].actual_value)
    # Y trae su propio digest de partición -- el mismo que el resultado retenido.
    assert props.get("partition-digest") == r_case[0].metadata["partition_digest"]


def test_el_digest_llega_al_ar_incluso_si_el_control_pasa():
    """Antes del arreglo, `partition_digest` solo llegaba al AR por las facetas
    de riesgo de un control que FALLA (`builder.py`, `if not cr.passed`). El
    ejemplo del issue es al revés: el resultado engañoso (k=41) es el que PASA,
    y es justo el que se firma y archiva sin marca de partición."""
    lax_policy = InternalPolicy(
        title="lax",
        controls=[
            InternalControl(
                id="PRIV-K",
                description="k-anon",
                severity="medium",
                metric_key="k_anonymity",
                threshold=0.5,  # k=1 sobrepasa esto de sobra -> PASA
                operator="ge",
                input_mapping={},
                params={"quasi_identifiers": ["age", "zip"]},
            )
        ],
    )
    run_dir_holder = {}
    with vl.monitor("piloto-pasa"):
        r = vl.enforce(data=_BY_CASE, policy=lax_policy)
        assert r[0].passed
        run_dir_holder["dir"] = GovernanceSession.get_current().base_dir

    _, observations = _findings_and_observations(run_dir_holder["dir"])
    props = {p["name"]: p["value"] for p in observations[0]["props"]}
    assert props.get("partition-digest")


def test_retain_vacio_no_deja_que_el_ar_caiga_a_lo_evaluado_sin_filtrar():
    """Si el pipeline filtra y no le queda nada, `retain([])` es una declaración
    válida -- «nada sobrevivió» -- y tiene que dejar constancia (un
    `retained_results.json` vacío) en vez de desaparecer y dejar que
    `_generate_oscal_artifacts` caiga de vuelta al caché completo sin filtrar."""
    run_dir_holder = {}
    with vl.monitor("piloto-vacio"):
        vl.enforce(data=_BY_CASE, policy=_k_anonymity_policy("PRIV-K"))
        vl.enforce(data=_BY_VERTEBRA, policy=_k_anonymity_policy("PRIV-K"))
        vl.retain([])
        run_dir_holder["dir"] = GovernanceSession.get_current().base_dir

    run_dir = run_dir_holder["dir"]
    assert json.loads((run_dir / "retained_results.json").read_text()) == []
    # Sin nada retenido no se genera NINGÚN AR -- `vl push` falla alto y
    # claro (No OSCAL assessment-results found) en vez de subir por
    # accidente la unión sin filtrar de las dos llamadas a enforce.
    assert not (run_dir / "assessment-results.oscal.json").exists()


def test_retain_fuera_de_monitor_avisa_y_no_rompe_nada(capsys):
    """Sin sesión activa (p.ej. tras salir del `with monitor():`, o llamado a
    pelo) `vl.retain()` no tiene dónde escribir -- pero tiene que decirlo, no
    fallar en silencio y dejar que el próximo `vl push` suba lo evaluado sin
    filtrar como si nada."""
    assert GovernanceSession.get_current() is None
    r_case = vl.enforce(data=_BY_CASE, policy=_k_anonymity_policy("PRIV-K"))

    out = vl.retain(r_case)

    assert out == r_case  # sigue siendo encadenable, no rompe el flujo
    captured = capsys.readouterr()
    assert "⚠" in captured.out
    assert "retain" in captured.out.lower()


def test_retain_es_idempotente_no_duplica_al_repetirse():
    """Llamar a `retain()` dos veces con la misma lista es una re-declaración
    del mismo subconjunto, no una segunda aportación -- no puede dejar el
    control duplicado (eso duplicaría observación y finding en el AR)."""
    session = GovernanceSession.start("piloto-idempotente")
    try:
        r_case = vl.enforce(data=_BY_CASE, policy=_k_anonymity_policy("PRIV-K"))
        vl.retain(r_case)
        vl.retain(r_case)

        retained_on_disk = json.loads(session.retained_results_file.read_text())
        assert len(retained_on_disk) == 1
    finally:
        GovernanceSession.stop()


def test_digest_no_colisiona_cuando_hash_pandas_object_falla():
    """Columnas con listas (no hasheables) tumban `hash_pandas_object`; el
    respaldo antiguo (`repr(data)`) trunca el DataFrame y dos particiones
    grandes que difieren solo pasado el corte daban el MISMO digest -- la
    propiedad invertida. El respaldo nuevo (`to_csv`) tiene que distinguirlas."""
    from venturalitica.api import _partition_digest

    df1 = pd.DataFrame({"a": range(401), "seg": [[1, 2] for _ in range(401)]})
    df2 = pd.DataFrame({"a": range(401), "seg": [[1, 2] for _ in range(401)]})
    df2.at[200, "seg"] = [9, 9]

    d1 = _partition_digest(data=df1)
    d2 = _partition_digest(data=df2)
    assert d1 and d2
    assert d1 != d2
