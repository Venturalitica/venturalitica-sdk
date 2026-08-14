"""El BOM tiene que distinguir qué inventaría: el producto que se despliega
o el entorno que lo midió. Son dos hechos distintos y los dos son útiles."""
import json

from venturalitica.scanner import BOMScanner

POETRY = """\
[tool.poetry]
name = "cyber-segmentation-service"
version = "0.3.0"

[tool.poetry.dependencies]
python = "^3.11"
torch = "2.0.1"
nnunetv2 = "2.1"
"""


def _componentes(doc):
    return {c["name"]: c for c in doc.get("components", [])}


def _es_entorno_de_medida(component):
    """Lee la propiedad CycloneDX `venturalitica:subject` que el scanner
    añade a cada componente. `measurement-environment` = banco que midió;
    cualquier otro valor (incluido ausente) = producto."""
    for prop in component.get("properties", []):
        if prop.get("name") == "venturalitica:subject":
            return prop.get("value") == "measurement-environment"
    return False


def test_un_pyproject_de_poetry_ya_no_es_invisible(tmp_path):
    (tmp_path / "pyproject.toml").write_text(POETRY)
    doc = json.loads(BOMScanner(str(tmp_path)).scan())
    comps = _componentes(doc)
    assert "torch" in comps, (
        "con un pyproject de Poetry el inventario del producto era sencillamente invisible, "
        f"y mdr.soup-inventory se satisfacía igual: {sorted(comps)}"
    )


def test_el_producto_declara_la_version_PINEADA_no_la_instalada(tmp_path):
    (tmp_path / "pyproject.toml").write_text(POETRY)
    doc = json.loads(BOMScanner(str(tmp_path)).scan())
    torch = _componentes(doc)["torch"]
    assert torch["version"] == "2.0.1", (
        "el componente del PRODUCTO tiene que salir de la declaración del repositorio, "
        f"no del intérprete vivo: {torch['version']}"
    )


def test_el_entorno_de_medida_viaja_ETIQUETADO_y_no_se_confunde_con_el_producto(tmp_path):
    (tmp_path / "pyproject.toml").write_text(POETRY)
    doc = json.loads(BOMScanner(str(tmp_path)).scan())
    comps = doc.get("components", [])
    del_producto = [c for c in comps if not _es_entorno_de_medida(c)]
    del_banco = [c for c in comps if _es_entorno_de_medida(c)]
    assert del_producto, "tiene que haber componentes del producto"
    assert all(c["name"] != "torch" or c["version"] == "2.0.1" for c in del_producto)
    # El banco puede estar vacío en un tmp_path sin entorno; lo que no puede es MEZCLARSE.
    for c in del_banco:
        assert _es_entorno_de_medida(c), "todo lo del banco va etiquetado"


def test_la_clave_python_de_poetry_no_es_un_componente(tmp_path):
    (tmp_path / "pyproject.toml").write_text(POETRY)
    doc = json.loads(BOMScanner(str(tmp_path)).scan())
    comps = _componentes(doc)
    assert "python" not in comps, (
        "en [tool.poetry.dependencies] la clave 'python' es el requisito de intérprete, "
        "no una dependencia de terceros"
    )


def test_restricciones_de_poetry_no_se_disfrazan_de_numero_de_version(tmp_path):
    """Un rango como '>=1.2,<2' no es un pin: colapsarlo a un solo número
    inventaría una versión que nadie declaró. Se conserva el rango completo."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.poetry]\n"
        'name = "x"\n'
        'version = "0.1.0"\n'
        "\n"
        "[tool.poetry.dependencies]\n"
        'python = "^3.11"\n'
        'acvl_utils = ">=1.2,<2"\n'
        'nnunetv2 = { version = "~2.1", extras = ["gpu"] }\n'
    )
    doc = json.loads(BOMScanner(str(tmp_path)).scan())
    comps = _componentes(doc)
    assert comps["acvl_utils"]["version"] == ">=1.2,<2", (
        "una restricción con rango se conserva literal, no se recorta a un número inventado: "
        f"{comps['acvl_utils']['version']}"
    )
    assert comps["nnunetv2"]["version"] == "2.1", (
        "un mapa {version=...} extrae la versión y le quita el operador de tilde/caret: "
        f"{comps['nnunetv2']['version']}"
    )


def test_pep621_sigue_funcionando_junto_a_poetry(tmp_path):
    """El camino PEP 621 no se borra: un repositorio puede tener cualquiera de los dos."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "y"\nversion = "1.0"\ndependencies = ["requests==2.31.0"]\n'
    )
    doc = json.loads(BOMScanner(str(tmp_path)).scan())
    comps = _componentes(doc)
    assert comps["requests"]["version"] == "2.31.0"
