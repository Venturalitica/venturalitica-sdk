"""El BOM tiene que ser determinista, o no se puede versionar — y si no se versiona,
no está donde el motor lo busca."""
import importlib.metadata
import json

from venturalitica.scanner import BOMScanner


def test_dos_corridas_con_las_mismas_entradas_dan_el_mismo_documento(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "1.0"\ndependencies = ["rich==13.0.0"]\n'
    )
    a = BOMScanner(str(tmp_path)).scan()
    b = BOMScanner(str(tmp_path)).scan()
    assert a == b, (
        "dos corridas con las mismas entradas producen documentos distintos: "
        "el BOM no se puede versionar, así que la bóveda tiene que ignorarse en git, "
        "así que el BOM solo existe donde corrió la medición"
    )


def test_ni_el_serial_ni_la_marca_de_tiempo_dependen_del_reloj(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "1.0"\n')
    doc = json.loads(BOMScanner(str(tmp_path)).scan())
    serial = doc.get("serialNumber")
    ts = doc.get("metadata", {}).get("timestamp")
    otro = json.loads(BOMScanner(str(tmp_path)).scan())
    assert serial == otro.get("serialNumber"), "el serialNumber no puede ser un UUID nuevo por corrida"
    assert ts == otro.get("metadata", {}).get("timestamp"), "el timestamp no puede venir del reloj"


def test_el_pin_declarado_que_coincide_con_lo_instalado_no_rompe_el_determinismo(tmp_path):
    """El caso SANO, no el raro: el entorno cumple su propio pin. `_scan_pyproject`
    emite el paquete como `product` y `_scan_imports` lo emite otra vez como
    `measurement-environment` -- mismo PURL, mismo bom-ref espejado. Antes de la
    tarea 2 el `SortedSet` fusionaba los dos `Component` (eran iguales); la
    propiedad `venturalitica:subject` los distingue y ahora conviven con el
    MISMO `bom-ref`, así que `BomRefDiscriminator._make_unique()` le asigna uno
    aleatorio a uno de los dos en cada serialización.

    La versión se deriva de `importlib.metadata` -- si se clava a mano, el test
    caduca en cuanto alguien actualice el entorno y deja de cazar nada, que es
    exactamente por lo que `test_dos_corridas_con_las_mismas_entradas_dan_el_mismo_documento`
    (arriba, `rich==13.0.0` con 14.3.2 instalado) no vio esto: los dos sujetos
    nunca coexistían.
    """
    version_instalada = importlib.metadata.version("click")
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname = "p"\nversion = "1.0"\n'
        f'dependencies = ["click=={version_instalada}"]\n'
    )
    (tmp_path / "m.py").write_text("import click\n")

    a = BOMScanner(str(tmp_path)).scan()
    b = BOMScanner(str(tmp_path)).scan()
    assert a == b, (
        "el pin declarado coincide con el instalado (el caso normal de un cliente "
        "cuyo entorno cumple sus propios pines) y el documento sigue cambiando "
        "de una corrida a otra: bom-ref aleatorio por colisión de PURL"
    )


def test_el_pin_coincidente_fusiona_en_UN_componente_con_los_dos_sujetos(tmp_path):
    """El arreglo no es cualificar el bom-ref -- eso rompería
    `test_bom_scanner_library_components_have_pypi_purl` (bom-ref == purl). Es
    fusionar el duplicado: mismo PURL, mismo componente, con las dos etiquetas
    de `venturalitica:subject` puestas a la vez."""
    version_instalada = importlib.metadata.version("click")
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname = "p"\nversion = "1.0"\n'
        f'dependencies = ["click=={version_instalada}"]\n'
    )
    (tmp_path / "m.py").write_text("import click\n")

    doc = json.loads(BOMScanner(str(tmp_path)).scan())
    click_components = [c for c in doc["components"] if c["name"] == "click"]
    assert len(click_components) == 1, (
        f"mismo PURL, mismo paquete, misma versión -- tiene que ser UN componente, "
        f"no {len(click_components)}"
    )
    subjects = {
        p["value"]
        for p in click_components[0].get("properties", [])
        if p["name"] == "venturalitica:subject"
    }
    assert subjects == {"product", "measurement-environment"}, (
        "el componente fusionado tiene que llevar las DOS etiquetas de sujeto -- "
        f"es el producto y lo que midió el banco a la vez: {subjects}"
    )
    # bom-ref sigue siendo el PURL, sin cualificar -- el ingestor resuelve por ahí.
    assert click_components[0]["bom-ref"] == click_components[0]["purl"]


def test_versiones_distintas_siguen_siendo_DOS_componentes(tmp_path):
    """Cuando el pin declarado NO coincide con lo instalado (el caso del
    piloto: torch 2.0.1 declarado frente a 2.13.0 instalado), los PURL son
    distintos y la divergencia tiene que seguir siendo visible como dos
    componentes -- fusionarlos aquí sería cambiar el bug de #971 por otro peor."""
    version_instalada = importlib.metadata.version("click")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "p"\nversion = "1.0"\n'
        'dependencies = ["click==0.0.0-does-not-match"]\n'
    )
    (tmp_path / "m.py").write_text("import click\n")

    doc = json.loads(BOMScanner(str(tmp_path)).scan())
    click_components = [c for c in doc["components"] if c["name"] == "click"]
    versions = {c["version"] for c in click_components}
    assert versions == {"0.0.0-does-not-match", version_instalada}, (
        f"versiones distintas tienen que seguir siendo componentes distintos: {versions}"
    )


def test_un_cambio_real_de_componentes_si_cambia_el_documento(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "1.0"\n')
    antes = BOMScanner(str(tmp_path)).scan()
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "1.0"\ndependencies = ["rich==13.0.0"]\n'
    )
    despues = BOMScanner(str(tmp_path)).scan()
    assert antes != despues, (
        "determinista no es constante: si cambian los componentes, el documento tiene que cambiar"
    )
