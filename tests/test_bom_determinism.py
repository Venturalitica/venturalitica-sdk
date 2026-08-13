"""El BOM tiene que ser determinista, o no se puede versionar — y si no se versiona,
no está donde el motor lo busca."""
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
