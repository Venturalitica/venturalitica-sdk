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
    """Cada test corre en un directorio temporal aislado y sin sesión previa."""
    monkeypatch.chdir(tmp_path)
    GovernanceSession._local = threading.local()


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
