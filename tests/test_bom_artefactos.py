"""El ML-BOM tiene que inventariar el ARTEFACTO gobernado, no solo las librerías
del entorno — y tiene que decir DE QUÉ ETAPA habla.

Nace de una medición del piloto de CyberSurgery (27-ago-2026), producto sanitario
clase IIb bajo MDR:

    BOM de adopción del modelo  → 18 componentes · TODOS type: "library"
    BOM de la validación        → 18 componentes · TODOS type: "library"
    sha256 dbc77ee3…            → IDÉNTICOS BYTE A BYTE
    ¿aparece el .pth gobernado? → NO

Dos consecuencias, y la segunda es peor que la primera:

1. `cl.mdr.soup-inventory` (IEC 62304 §8.1.2) pide los componentes de terceros
   inventariados por nombre/versión/purl en un BOM firmado. Sin el artefacto, el
   inventario está incompleto sobre el objeto que de verdad se despliega.

2. Si dos etapas cualesquiera dan SIEMPRE el mismo BOM, ese BOM no describe la
   etapa: describe el entorno de Python. Como linaje del Anexo IV §2 no aporta
   nada — es un artefacto que no puede salir distinto.

Nada de esto inventa vocabulario: CycloneDX ≥1.5 ya tiene `machine-learning-model`
y `data` como tipos de componente, `hashes` para el digest, y `metadata.component`
para declarar el SUJETO del documento.
"""
import json

from venturalitica.scanner import BOMScanner


def _doc(scanner):
    return json.loads(scanner.scan())


def _por_nombre(doc):
    return {c["name"]: c for c in doc.get("components", [])}


def test_el_modelo_gobernado_entra_en_el_inventario_con_su_digest(tmp_path):
    pesos = tmp_path / "vertebrae_segmentation_model.pth"
    pesos.write_bytes(b"pesos-del-modelo")

    sc = BOMScanner(str(tmp_path))
    sc.declarar_artefactos([{"name": pesos.name, "path": str(pesos), "fingerprint": "a" * 64}])
    comps = _por_nombre(_doc(sc))

    assert pesos.name in comps, "el artefacto gobernado tiene que APARECER en el inventario"
    c = comps[pesos.name]
    assert c["type"] == "machine-learning-model", (
        "un fichero de pesos es un modelo, no una librería: CycloneDX ya tiene el tipo"
    )
    algs = {h["alg"]: h["content"] for h in c.get("hashes", [])}
    assert algs.get("SHA-256") == "a" * 64, (
        "sin digest, el inventario no ancla nada: IEC 62304 §8.1.2 pide identificar el componente"
    )


def test_un_dataset_declarado_no_se_marca_como_modelo(tmp_path):
    datos = tmp_path / "cohorte.csv"
    datos.write_text("a,b\n1,2\n")

    sc = BOMScanner(str(tmp_path))
    sc.declarar_artefactos([{"name": datos.name, "path": str(datos), "fingerprint": "b" * 64}])
    c = _por_nombre(_doc(sc))[datos.name]

    assert c["type"] == "data", "un csv no es un modelo; CycloneDX distingue `data` de `machine-learning-model`"


def test_dos_ETAPAS_del_mismo_entorno_ya_no_dan_el_mismo_documento(tmp_path):
    """El defecto medido: mismo entorno de Python ⇒ BOM idéntico byte a byte.

    Con el sujeto declarado y los artefactos de cada etapa dentro, dos fases que
    hacen cosas distintas dejan de ser indistinguibles.
    """
    modelo = tmp_path / "modelo.pth"
    modelo.write_bytes(b"m")
    cohorte = tmp_path / "cohorte.csv"
    cohorte.write_text("x\n")

    derivacion = BOMScanner(str(tmp_path))
    derivacion.declarar_sujeto("adopcion-modelo-terceros")
    derivacion.declarar_artefactos([{"name": modelo.name, "path": str(modelo), "fingerprint": "c" * 64}])

    validacion = BOMScanner(str(tmp_path))
    validacion.declarar_sujeto("medicion-cohorte-validacion")
    validacion.declarar_artefactos([{"name": cohorte.name, "path": str(cohorte), "fingerprint": "d" * 64}])

    assert derivacion.scan() != validacion.scan(), (
        "dos etapas distintas no pueden producir el MISMO documento: "
        "un BOM que no puede salir distinto no está describiendo la etapa"
    )


def test_el_sujeto_del_documento_viaja_en_metadata_component(tmp_path):
    """`metadata.component` es el campo CycloneDX que dice DE QUÉ trata el BOM.
    Estaba sin poner, y por eso el documento no sabía nombrar su propia etapa."""
    sc = BOMScanner(str(tmp_path))
    sc.declarar_sujeto("medicion-cohorte-validacion")
    meta = _doc(sc).get("metadata", {})

    assert meta.get("component", {}).get("name") == "medicion-cohorte-validacion"


def test_sin_artefactos_ni_sujeto_el_BOM_sigue_saliendo(tmp_path):
    """La otra dirección: esto es ADITIVO. Un guion que no declara nada sigue
    produciendo su BOM como antes — si no, el arreglo rompería a quien no lo pidió."""
    doc = _doc(BOMScanner(str(tmp_path)))
    assert doc.get("bomFormat") == "CycloneDX"


def test_el_inventario_completo_del_entorno_es_OPT_IN(tmp_path, monkeypatch):
    """La delegación en `cyclonedx-py` existe pero NO es el camino por defecto, y las
    dos razones están medidas: 5,78 s por llamada dentro del pipeline del cliente, y
    163 componentes donde el escaneo propio pone 21 — sepultando el pin DECLARADO del
    producto, que es justo la distinción que #971 estableció.

    Esta sonda fija la puerta, no la herramienta: sin la variable, no se invoca.
    """
    monkeypatch.delenv("VL_BOM_ENV_COMPLETO", raising=False)
    llamadas = []

    sc = BOMScanner(str(tmp_path))
    sc._scan_environment_with_cyclonedx = lambda: llamadas.append(1) or True  # type: ignore[method-assign]
    sc.scan()

    assert llamadas == [], "sin `VL_BOM_ENV_COMPLETO=1` NO se paga el subproceso"
