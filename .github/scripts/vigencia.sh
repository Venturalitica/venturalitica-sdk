#!/usr/bin/env bash
# Guardian of CURRENCY: a consequence filed as CURRENT is backed by a test that RAN and that CAN
# FAIL. It is not in the sibling MET-SPEC repository's precedent, and it exists because the person
# who operates that precedent named the gap himself:
#
#     «trazabilidad.sh checks the NAMED test EXISTS, not that it demonstrates the requirement.
#      A test that exists and cannot fail passes the guardian.»
#
# With this tree's numbers, that would happen on day one. MEASURED HERE 2026-09-11:
#
#     844 test_* functions · 841 collected by pytest · 840 passing
#      21 NEVER COLLECTED AT ALL — tests/test_graph_nodes.py and tests/test_imaging_metrics.py
#         call pytest.importorskip on langchain_core and monai, extras that
#         `uv sync --group dev` does not install. Because the skip fires at module level during
#         COLLECTION, those 21 are never reported as skipped individually. They do not appear in
#         the run at all. The suite prints `840 passed, 3 skipped` and the 21 vanish inside a green.
#      26 collected, always run, containing NO ASSERTION of any kind
#       1 skipped explicitly with @pytest.mark.skip
#
# TWO FAMILIES, NEVER SUMMED, and this guardian reports them apart:
#   · ENVIRONMENT gap — they exist and could run; installing the extras fixes them.
#   · SUBJECT gap — they always run and cannot fail; nothing fixes them but writing the assertion.
# Summing them means believing, one day, that installing the extras closed sixty-one.
#
# Hence the rule that governs this file:
#
#     A claim whose only support is a test that never executes is not CURRENT.
#     Neither is one whose only support cannot fail.
#
# WHY IT READS A JUNIT REPORT AND NOT THE TREE. Whether a test ran is a property of the RUN, not
# of the source. Inferring it by reading `importorskip` calls would be re-deriving, from the same
# text, the thing the run already knows — and it would miss every skip decided at runtime. So this
# guardian is fed the report pytest just produced, and it runs in the job that produced it. The
# same rule as the kit's gate, applied to our own instrument: read what it says it measured.
#
# It FAILS rather than passing when the report is missing. A currency guardian that skips its
# cases when the evidence is absent is exactly the green that cannot distinguish «passed» from
# «was not asked», which is the defect this whole file exists to answer.
#
# WHAT THIS GUARDIAN DOES NOT COVER: that the assertion is about the right subject. A test that
# ran, that contains an assertion, and that asserts something irrelevant passes here. That half is
# not mechanisable and is not pretended to be: it is closed by whoever asked for the change,
# against a check of their own (CLAUDE.md).
#
# Input:
#   $1 or VIGENCIA_JUNIT   path to the JUnit XML from the run being certified (required)
#   VIGENCIA_RAIZ          root to inspect (default: cwd) — for the falsifier only
# Output: `::error` annotations plus a summary. 0 green, 1 red.
set -uo pipefail

RAIZ="${VIGENCIA_RAIZ:-$PWD}"
JUNIT="${1:-${VIGENCIA_JUNIT:-}}"
SUMMARY="${GITHUB_STEP_SUMMARY:-/dev/null}"
export LC_ALL=C

rojo() {
  local titulo="$1"; shift
  echo "::error title=vigencia::$titulo"
  printf '%s\n' "$@"
  { echo "**RED — $titulo**"; echo; printf '%s\n' "$@"; } >> "$SUMMARY"
  exit 1
}

cd "$RAIZ" || rojo "cannot enter $RAIZ"
command -v python3 >/dev/null 2>&1 || rojo "python3 is missing"

[ -n "$JUNIT" ] || rojo "no JUnit report was given" \
  "Pass it as \$1 or in VIGENCIA_JUNIT. This guardian FAILS without the report instead of" \
  "certifying nothing and exiting 0 — a green that cannot tell «passed» from «was not asked» is" \
  "the exact defect it exists to answer."
[ -f "$JUNIT" ] || rojo "the JUnit report \`$JUNIT\` does not exist" \
  "Did the pytest step run with --junitxml? Without the report there is no evidence that any" \
  "cited test executed, and absence of evidence is not evidence of a pass."

SALIDA="$(python3 - "$RAIZ" "$JUNIT" <<'PY'
import ast, os, re, sys
import xml.etree.ElementTree as ET

raiz, junit = sys.argv[1], sys.argv[2]

# ── What the run says it executed ───────────────────────────────────────────────────────────────
try:
    arbol = ET.parse(junit)
except Exception as e:
    print("NOXML:" + str(e)); raise SystemExit(0)

# Indexed by (module, function), never by function alone. Matching on the bare name would let a
# citation to `tests/b.py::test_x` be satisfied by `tests/a.py::test_x` having run — a false green
# on exactly the question this guardian exists to answer. pytest writes the module in `classname`
# (`tests.test_vault_retained`, or `tests.test_oscal_output.TestSomething` for a class), so the
# module is the prefix.
ejecutados, saltados = set(), set()
for caso in arbol.getroot().iter("testcase"):
    nombre = caso.get("name") or ""
    # pytest parametrisation appends [id]; the citation names the function.
    base = nombre.split("[", 1)[0]
    if not base:
        continue
    clase = caso.get("classname") or ""
    destino = saltados if caso.find("skipped") is not None else ejecutados
    destino.add((clase, base))

if not ejecutados:
    print("VACIO"); raise SystemExit(0)


def modulo_de(ruta):
    """`tests/test_x.py` -> `tests.test_x`, the prefix pytest writes into `classname`."""
    return ruta[:-3].replace("/", ".").replace("\\", ".") if ruta.endswith(".py") else ruta


def consta(conjunto, ruta, nombre):
    pref = modulo_de(ruta)
    return any(n == nombre and (c == pref or c.startswith(pref + "."))
               for c, n in conjunto)

# ── Which cited functions can fail ──────────────────────────────────────────────────────────────
_cache = {}

def afirma(ruta, nombre):
    """True when the named function contains something that can fail the test.

    `assert`, plus pytest.raises / warns / approx and unittest-style assert* calls, which are
    assertions of observable behaviour even though they are not `assert` statements. The same
    classification used for the 2026-09-11 census, kept identical on purpose: a guardian that
    counted differently from the measurement behind the decision would produce a third number.
    """
    if ruta not in _cache:
        try:
            _cache[ruta] = ast.parse(open(os.path.join(raiz, ruta), encoding="utf-8").read())
        except Exception:
            _cache[ruta] = None
    arbol = _cache[ruta]
    if arbol is None:
        return None
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)) and nodo.name == nombre:
            for n in ast.walk(nodo):
                if isinstance(n, ast.Assert):
                    return True
                if isinstance(n, ast.Attribute) and (n.attr.startswith("assert") or
                                                     n.attr in ("raises", "warns", "approx")):
                    return True
            return False
    return None

# ── The CURRENT consequences ────────────────────────────────────────────────────────────────────
RE_REQ = re.compile(r"^### Requirement:\s*(.+?)\s*$", re.M)
RE_ESC = re.compile(r"^#### Scenario:\s*(.+?)\s*$", re.M)
RE_EST = re.compile(r"\*\*Status:\*\*\s*([A-Z ]+?)(?:\s|$)", re.M)
RE_PRU = re.compile(r"\*\*Proof:\*\*\s*`([^`]+)`", re.M)

def trozos(texto, regex):
    ms = list(regex.finditer(texto))
    for i, m in enumerate(ms):
        fin = ms[i + 1].start() if i + 1 < len(ms) else len(texto)
        yield m.group(1), texto[m.end():fin]

specs = []
base = os.path.join(raiz, "openspec", "specs")
for d in sorted(os.listdir(base)) if os.path.isdir(base) else []:
    f = os.path.join(base, d, "spec.md")
    if os.path.isfile(f):
        specs.append(f)
cambios = os.path.join(raiz, "openspec", "changes")
for dirpath, _dn, fns in sorted(os.walk(cambios)) if os.path.isdir(cambios) else []:
    if os.sep + "archive" + os.sep in dirpath + os.sep:
        continue
    if "spec.md" in fns and os.sep + "specs" in dirpath:
        specs.append(os.path.join(dirpath, "spec.md"))

if not specs:
    print("SINCORPUS"); raise SystemExit(0)

revisados = 0
entorno, sujeto, ausente = [], [], []

for f in specs:
    cap = os.path.basename(os.path.dirname(f))
    texto = open(f, encoding="utf-8").read()
    for titulo, cuerpo in trozos(texto, RE_REQ):
        for nombre_esc, bloque in trozos(cuerpo, RE_ESC):
            est = [e.strip() for e in RE_EST.findall(bloque)]
            if "CURRENT" not in est:
                continue
            ref = RE_PRU.search(bloque)
            if not ref:
                continue  # trazabilidad.sh owns that failure; not this guardian's subject
            ruta, _, nombre = ref.group(1).partition("::")
            revisados += 1
            donde = "%s :: %s → %s" % (cap, titulo, nombre_esc)

            if consta(saltados, ruta, nombre) and not consta(ejecutados, ruta, nombre):
                entorno.append("%s\n      cites `%s`, which the run reports as SKIPPED." % (donde, nombre))
            elif not consta(ejecutados, ruta, nombre):
                entorno.append(
                    "%s\n      cites `%s`, which DOES NOT APPEAR in the run at all — not even as a\n"
                    "      skip, under module `%s`. A module-level importorskip removes its tests\n"
                    "      during collection, so they vanish inside a green. ENVIRONMENT family."
                    % (donde, nombre, modulo_de(ruta)))
            else:
                puede = afirma(ruta, nombre)
                if puede is None:
                    ausente.append("%s\n      cites `%s` in `%s`, which cannot be parsed or does not\n"
                                   "      define that function." % (donde, nombre, ruta))
                elif not puede:
                    sujeto.append("%s\n      cites `%s`, which RUNS and contains NO ASSERTION, so it\n"
                                  "      cannot fail. Installing extras will never fix this one.\n"
                                  "      SUBJECT family." % (donde, nombre))

print("OK")
print(revisados)
print(len(entorno), len(sujeto), len(ausente))
print(len(ejecutados), len(saltados))
for x in entorno + sujeto + ausente:
    print("  - " + x)
PY
)"

ESTADO="$(printf '%s' "$SALIDA" | sed -n 1p)"
case "$ESTADO" in
  NOXML:*)   rojo "the JUnit report does not parse" "${ESTADO#NOXML:}" "If pytest did not speak, it did not measure." ;;
  VACIO)     rojo "the JUnit report records no executed test" \
               "A report with nothing in it certifies nothing, and reads exactly like a healthy one." ;;
  SINCORPUS) rojo "there is no corpus to certify" "Same trap as the other two guardians: nothing is not a green." ;;
  OK)        ;;
  *)         rojo "the census did not run" "$SALIDA" ;;
esac

REVISADOS="$(printf '%s' "$SALIDA" | sed -n 2p)"
read -r N_ENT N_SUJ N_AUS <<< "$(printf '%s' "$SALIDA" | sed -n 3p)"
read -r N_EJEC N_SALT <<< "$(printf '%s' "$SALIDA" | sed -n 4p)"
DETALLE="$(printf '%s' "$SALIDA" | sed -n '5,$p')"

TOTAL_FALLOS=$((N_ENT + N_SUJ + N_AUS))
if [ "$TOTAL_FALLOS" -gt 0 ]; then
  rojo "$TOTAL_FALLOS CURRENT consequence(s) are backed by a test that did not run or cannot fail" \
    "$DETALLE" \
    "" \
    "Counted APART and never summed:" \
    "  environment gap (did not run, extras would fix it) : $N_ENT" \
    "  subject gap (ran, no assertion, nothing fixes it)  : $N_SUJ" \
    "  citation does not resolve to a function            : $N_AUS" \
    "" \
    "A consequence in this state is NOT CURRENT — and that does not make it PENDING. If the" \
    "behaviour exists and nothing that RUNS pins it, it is UNPROVEN; if the behaviour does not" \
    "exist yet, it is PENDING. Either way the reason is written. Fabricating coverage here is" \
    "the failure this SDK exists to prevent."
fi

MSG="GREEN — and only for what it covers: all ${REVISADOS} CURRENT consequence(s) cite a test that
the run reports as EXECUTED and that contains at least one assertion, so it can fail.
  run: ${N_EJEC} executed · ${N_SALT} skipped
This says NOTHING about whether the assertion is about the right subject. A test that ran, asserts
something, and asserts the wrong thing passes this gate. That half is closed by whoever asked for
the change, against a check of their own."
echo "$MSG"
{ echo "**vigencia — $MSG**"; } >> "$SUMMARY"
exit 0
