"""The corpus declares which norm each register identifier is published as, and cannot drift.

`openspec/norms.yml` is the half of the mapping only this repository can state: the management
system's register owns each norm's official title, but the name this public corpus cites it by is
a drafting decision taken here. A control that had to bridge the two by matching prose would be
guessing, and one that kept its own copy of the mapping would be a guardian holding its own copy
of its subject.

The condition those identifiers entered under is the one these tests enforce: **the identifier
accompanies the name, it never replaces it.** An internal register key is unresolvable to a reader
outside the organisation; beside the full name of the norm it costs that reader nothing. A public
corpus that said only `LEX-EU-PLD` would be a dangling reference.
"""
import re
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
DECLARACION = RAIZ / "openspec" / "norms.yml"
CORPUS = RAIZ / "openspec"

# Identifier shape. Deliberately a pattern and not a list: a new norm cited without being declared
# has to be caught, and a list of the ones we already know about could not catch it.
RE_ID = re.compile(r"`(LEX-[A-Z0-9-]+)`")


def _declaradas() -> list:
    datos = yaml.safe_load(DECLARACION.read_text(encoding="utf-8")) or {}
    return datos.get("norms") or []


def _texto_del_corpus() -> dict:
    """Every corpus file, with whitespace collapsed.

    Collapsed because the prose is hard-wrapped and a norm's name routinely straddles a line
    break: `Product Liability\\n  Directive`. Checking adjacency against the raw text would fail
    on formatting rather than on substance, which is a red for the wrong reason.
    """
    fuera = {}
    for f in sorted(CORPUS.rglob("*.md")):
        fuera[str(f.relative_to(RAIZ))] = " ".join(f.read_text(encoding="utf-8").split())
    return fuera


def test_la_declaracion_no_esta_vacia():
    """Every check below iterates over the declaration. An empty file would make all of them
    vacuous and this suite green without having compared anything — the same defect as a validator
    that exits 0 on an empty corpus."""
    declaradas = _declaradas()
    assert declaradas, "`openspec/norms.yml` declares no norm at all"
    for n in declaradas:
        assert n.get("id") and n.get("published_as"), f"incomplete entry: {n}"


def test_todo_identificador_usado_esta_declarado():
    """A norm cited in the corpus without an entry here breaks the consumer silently: the control
    would find an identifier it cannot resolve to a name."""
    declarados = {n["id"] for n in _declaradas()}
    usados = set()
    for ruta, texto in _texto_del_corpus().items():
        usados |= set(RE_ID.findall(texto))
    huerfanos = usados - declarados
    assert not huerfanos, (
        f"cited in the corpus and not declared in {DECLARACION.name}: {sorted(huerfanos)}"
    )


def test_toda_norma_declarada_se_usa_de_verdad():
    """The other direction. A dead entry is worse than a missing one: it reads as coverage."""
    textos = _texto_del_corpus()
    for n in _declaradas():
        assert any(f"`{n['id']}`" in t for t in textos.values()), (
            f"`{n['id']}` is declared in {DECLARACION.name} and cited nowhere in the corpus"
        )


def test_el_identificador_nunca_aparece_sin_su_norma_al_lado():
    """THE condition the identifiers entered under.

    Every occurrence has to carry a significant word of the norm's published name within reach.
    Checked on every occurrence and not just one, because the erosion this guards against is
    somebody abbreviating a later mention — the first citation is never the one that goes bare.
    """
    VENTANA = 90
    for n in _declaradas():
        significativas = [p for p in n["published_as"].split() if len(p) > 3 and p != "EU"]
        assert significativas, f"cannot check `{n['id']}`: its name has no distinctive word"
        for ruta, texto in _texto_del_corpus().items():
            for m in re.finditer(re.escape(f"`{n['id']}`"), texto):
                antes = texto[max(0, m.start() - VENTANA):m.start()]
                assert any(p in antes for p in significativas), (
                    f"{ruta}: `{n['id']}` appears with no part of \"{n['published_as']}\" in the "
                    f"{VENTANA} characters before it. The identifier accompanies the name, it "
                    f"never replaces it — a public corpus citing only the key is a dangling "
                    f"reference. Context: …{antes[-70:]}"
                )


def test_el_nombre_publicado_y_el_identificador_se_emparejan_al_menos_una_vez():
    """Somewhere the full published name must sit directly against the identifier, so that the
    pairing is established in the text and not only asserted in a side file."""
    textos = _texto_del_corpus()
    for n in _declaradas():
        emparejado = any(
            re.search(re.escape(n["published_as"]) + r"[^`]{0,30}`" + re.escape(n["id"]) + "`", t)
            for t in textos.values()
        )
        assert emparejado, (
            f"\"{n['published_as']}\" is never written immediately against `{n['id']}`. The "
            f"declaration would then rest on this file alone, which is the copy-of-the-subject "
            f"defect it exists to avoid."
        )


def test_el_fichero_citado_por_cada_norma_existe_y_la_contiene():
    for n in _declaradas():
        ruta = n.get("cited_in")
        assert ruta, f"`{n['id']}` declares no `cited_in`"
        f = RAIZ / ruta
        assert f.is_file(), f"`{n['id']}` names `{ruta}`, which does not exist"
        assert f"`{n['id']}`" in f.read_text(encoding="utf-8"), (
            f"`{n['id']}` names `{ruta}`, which does not cite it"
        )
