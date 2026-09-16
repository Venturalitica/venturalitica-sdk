#!/usr/bin/env bash
# Falsifier for `que-sale.sh`: proves it goes RED, and FOR THE NAMED REASON.
#
# Same discipline as the other four. Each case fixes what it believes it is provoking, moves
# nothing else, and requires the expected reason in the output — a red from the wrong assertion
# reads exactly like a good one.
#
# It builds tiny synthetic sdists rather than the real package. The guardian's subject is «what is
# inside the artefact», and a tarball is a tarball; using the real build would make this file slow
# and would couple it to whatever the packaging config happens to do that day.
set -uo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUARDIAN="$AQUI/que-sale.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export GITHUB_STEP_SUMMARY=/dev/null
ok=0; mal=0

# $1 nombre, resto: «ruta=contenido» dentro del sdist
sdist() {
  local nombre="$1"; shift
  local d="$TMP/$nombre" raiz="paquete-0.0.0"
  rm -rf "$d"; mkdir -p "$d/$raiz"
  for par in "$@"; do
    local ruta="${par%%=*}" cuerpo="${par#*=}"
    mkdir -p "$d/$raiz/$(dirname "$ruta")"
    printf '%s\n' "$cuerpo" > "$d/$raiz/$ruta"
  done
  tar czf "$d.tar.gz" -C "$d" "$raiz"
  echo "$d.tar.gz"
}

manifiesto() {  # $1 destino, $2 lista `ships`, $3 lista `pending_decision`
  mkdir -p "$(dirname "$1")"
  { echo "ships:"; for x in $2; do echo "  - $x"; done
    echo "pending_decision:"; for x in ${3:-}; do echo "  - $x"; done; } > "$1"
}

# Una raíz mínima: manifiesto propio y ningún fichero suelto que contamine `en_repo`.
raiz() {
  local R="$TMP/raiz-$1"; rm -rf "$R"; mkdir -p "$R/.github/packaging"
  manifiesto "$R/.github/packaging/ships.yml" "$2" "${3:-}"
  echo "$R"
}

caso() {  # $1 nombre, $2 raiz, $3 sdist, $4 motivo
  local salida rc
  salida="$(QUE_SALE_RAIZ="$2" bash "$GUARDIAN" "$3" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "  ✗ $1 — stayed GREEN; should have gone red for: $4"; mal=$((mal+1)); return
  fi
  if ! printf '%s' "$salida" | grep -qF -- "$4"; then
    echo "  ✗ $1 — went red, but NOT for the expected reason."
    echo "      expected: $4"
    echo "      said:     $(printf '%s' "$salida" | head -3 | tr '\n' ' ')"
    mal=$((mal+1)); return
  fi
  echo "  ✓ $1"; ok=$((ok+1))
}

echo "falsifier for que-sale.sh"

# ── el artefacto tiene que estar ────────────────────────────────────────────────────────────────
R="$(raiz sinartefacto "LICENSE")"
salida="$(QUE_SALE_RAIZ="$R" bash "$GUARDIAN" "$TMP/no-existe.tar.gz" 2>&1)"
if printf '%s' "$salida" | grep -qF "no sdist to inspect"; then
  echo "  ✓ no artefact to inspect fails instead of certifying"; ok=$((ok+1))
else
  echo "  ✗ a missing artefact must fail, not pass"; mal=$((mal+1))
fi

# ── 1. la lista blanca ──────────────────────────────────────────────────────────────────────────
# EL CASO QUE JUSTIFICA EL GUARDIÁN: un fichero que nadie declaró se cuela. Es lo que pasó de
# verdad con un log de LaTeX y con el fichero de ignorados de git.
R="$(raiz cuela "LICENSE")"
S="$(sdist cuela "LICENSE=x" "texput.log=basura")"
caso "an undeclared file leaves the repository" "$R" "$S" "leave this repository undeclared"

R="$(raiz muerta "LICENSE README.md")"
S="$(sdist muerta "LICENSE=x")"
caso "a declared file that does not ship" "$R" "$S" "do not ship"

# Vacuidad: un manifiesto vacío haría vacua la comparación y verde el guardián.
R="$(raiz vacio "")"
S="$(sdist vacio "LICENSE=x")"
caso "an empty manifest is not a green" "$R" "$S" "declares nothing"

# Y el artefacto sin ningún fichero no-código: aunque el manifiesto esté lleno, comparar contra
# nada no discrimina.
R="$(raiz artefactovacio "LICENSE")"
S="$(sdist artefactovacio "modulo.py=x")"
caso "an artefact with no non-code file at all" "$R" "$S" "holds no non-code file"

# ── 2. referencias que no resuelven fuera ───────────────────────────────────────────────────────
# LA QUE DE VERDAD IMPORTA: viaja DENTRO de un fichero que legítimamente sale, así que la lista
# blanca del apartado 1 no la ve. Dos controles, y ninguno cubre al otro.
R="$(raiz ajena "LICENSE")"
S="$(sdist ajena "LICENSE=x" "src/m.py=# see Venturalitica/otro-repo#42")"
caso "a cross-repository issue cited from inside a shipped file" "$R" "$S" "an issue in another repository"

R="$(raiz fechado "LICENSE")"
S="$(sdist fechado "LICENSE=x" "src/m.py=# see 2026-05-22-algo-design.md §3")"
caso "a dated design record that exists nowhere public" "$R" "$S" "a dated design record"

# ── y los contrastes, sin los cuales los dos de arriba no detectan nada ─────────────────────────
R="$(raiz propia "LICENSE")"
S="$(sdist propia "LICENSE=x" "src/m.py=# see Venturalitica/venturalitica-sdk#10")"
if QUE_SALE_RAIZ="$R" bash "$GUARDIAN" "$S" >/dev/null 2>&1; then
  echo "  ✓ this repository's OWN issue is not flagged"; ok=$((ok+1))
else
  echo "  ✗ citing our own issue must be allowed, or the check fires on everything"; mal=$((mal+1))
fi

# El caso que hundió la primera versión: `Annex_IV.md` y compañía son nombres que el SDK GENERA,
# no citas. Veintidós hallazgos de los que veinte eran ruido. Un guardián que grita veinte veces
# para acertar dos se ignora, y entonces no caza nada.
R="$(raiz generados "LICENSE")"
S="$(sdist generados "LICENSE=x" "src/m.py=ruta = 'Annex_IV.md'; otra = 'assurance_report.md'")"
if QUE_SALE_RAIZ="$R" bash "$GUARDIAN" "$S" >/dev/null 2>&1; then
  echo "  ✓ filenames the SDK generates are not mistaken for citations"; ok=$((ok+1))
else
  echo "  ✗ generated filenames must not be flagged — that noise is what got the first version ignored"; mal=$((mal+1))
fi

R="$(raiz sana "LICENSE README.md" "texput.log")"
S="$(sdist sana "LICENSE=x" "README.md=y" "texput.log=z")"
if QUE_SALE_RAIZ="$R" bash "$GUARDIAN" "$S" >/dev/null 2>&1; then
  echo "  ✓ a declared artefact is GREEN (the guardian is not hardwired to red)"; ok=$((ok+1))
else
  echo "  ✗ a declared artefact went RED — every case above is worthless"; mal=$((mal+1))
fi

# Lo pendiente de decisión pasa, y se IMPRIME. Si dejara de imprimirse, la decisión envejecería
# hasta volverse la norma sin que nadie la tomara.
salida="$(QUE_SALE_RAIZ="$R" bash "$GUARDIAN" "$S" 2>&1)"
if printf '%s' "$salida" | grep -qF "texput.log"; then
  echo "  ✓ what ships pending a decision is named in the green, not just tolerated"; ok=$((ok+1))
else
  echo "  ✗ the pending-decision list must be printed every run"; mal=$((mal+1))
fi

echo
if [ "$mal" -gt 0 ]; then
  echo "::error title=que-sale.test::$mal of $((ok+mal)) contracts unmet"
  exit 1
fi
echo "que-sale.sh knows how to go red: $ok/$ok contracts, each for its named reason."
