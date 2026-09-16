"""Every relative link on the public front page resolves.

`README.md` is the first screen of a public repository, and its line 9 cites a document as *the
normative OSCAL contract*, in the same sentence as the arXiv preprint. That citation pointed at a
file deleted by the 0.6.4 hotfix and stayed broken for months. Nobody noticed, because nothing
checked.

This repository's own `CLAUDE.md` calls that class of thing a defect rather than a typo: a
normative reference that does not resolve is a promise the repository cannot keep. So it gets a
check, and the check is the cheap half — the expensive half was already paid by writing a contract
that is true.

Only relative links are checked. External URLs are not: verifying them needs the network, would
make the suite fail for reasons that have nothing to do with this repository, and a red for
somebody else's outage is a red for the wrong reason.
"""
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
README = RAIZ / "README.md"

# `[text](./path)` and `[text](path)`, excluding anything with a scheme or an anchor-only target.
RE_ENLACE = re.compile(r"\[[^\]]*\]\((?!https?://|mailto:|#)([^)\s]+)\)")


def _enlaces_relativos() -> list:
    texto = README.read_text(encoding="utf-8")
    vistos = []
    for m in RE_ENLACE.finditer(texto):
        destino = m.group(1).split("#", 1)[0]  # drop in-page anchors
        if destino:
            linea = texto.count("\n", 0, m.start()) + 1
            vistos.append((linea, destino))
    return vistos


def test_el_readme_tiene_enlaces_relativos_que_comprobar():
    """Without this, emptying the README or changing its link syntax would make the check below
    vacuous and green. An assertion over nothing does not discriminate."""
    assert _enlaces_relativos(), "no relative link found in README.md — has the syntax changed?"


@pytest.mark.parametrize("linea,destino", _enlaces_relativos(), ids=lambda v: str(v))
def test_cada_enlace_relativo_del_readme_resuelve(linea, destino):
    ruta = (RAIZ / destino).resolve()
    assert ruta.exists(), (
        f"README.md:{linea} links to `{destino}`, which does not exist. On a public front page a "
        f"reference that does not resolve is a defect, not a typo — and this one cost months the "
        f"last time, because the citation read as normative and nobody could open it."
    )
