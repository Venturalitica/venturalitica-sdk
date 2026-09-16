#!/usr/bin/env bash
# Guardian of the baseline's TRACE: every CONSEQUENCE declares its state, and the one claiming to
# describe today's SDK has to NAME the test that demonstrates it — and that test has to exist.
#
# Why it exists, and why `openspec validate` is not enough:
#
#   `openspec validate` checks the FORM of the document. It cannot know whether a requirement
#   describes what the SDK does or what we wish it did, and that difference is what decides
#   whether a baseline is a baseline or a backlog under another name. The sibling MET-SPEC
#   repository measured 74% of its own corpus describing behaviour that does not yet exist. A
#   corpus that is three quarters backlog scores perfect on form.
#
#   Hence the rule that governs this file:
#
#       A consequence is not classified by where its citation is written.
#       It is classified because it declares itself, and the declaration is checked.
#
# WHY STATE HANGS FROM THE CONSEQUENCE AND NOT FROM THE REQUIREMENT.
# The sibling repository declares state on the `### Requirement:`. Measured on a third repository
# over 12 requirements and 74 verifiable consequences, that is wrong in both directions: a
# requirement can be one third built and two thirds not, and calling it wholly current or wholly
# pending lies either way. So this guardian reads `#### Scenario:` blocks, and a requirement's
# state is DERIVED from its consequences rather than declared over them.
#
# The three states, and why three rather than two:
#
#   CURRENT    describes what the SDK does today, and names the test demonstrating it.
#   UNPROVEN   describes what the SDK does today, and NOTHING pins it.  ← the dangerous one
#   PENDING    describes what the SDK SHOULD do. It is backlog and is counted as backlog.
#
#   UNPROVEN is what justifies three. With two states, real behaviour that no test holds would be
#   filed as CURRENT and nobody would know it can vanish in silence.
#
# WHAT THIS GUARDIAN CANNOT MEASURE, and you have to know it before reading its green: it checks
# the named test EXISTS, never that it demonstrates the requirement. It does not check that the
# test RAN or that it CAN FAIL either — that is `vigencia.sh`, which answers a different question
# and does not substitute for this one, nor this one for it. Two guardians answering different
# questions never stand in for each other, and a green is only ever worth the name attached to it.
#
# The backlog proportion is MEASURED and NOT GATED. A guardian that also imposed a ceiling would
# turn a measurement into a policy nobody decided.
#
# Input: none. Runs from the repository root.
#   TRAZA_RAIZ   root to inspect (default: cwd) — for the falsifier only
# Output: `::error` annotations plus a summary. 0 green, 1 red.
set -uo pipefail

RAIZ="${TRAZA_RAIZ:-$PWD}"
SUMMARY="${GITHUB_STEP_SUMMARY:-/dev/null}"
export LC_ALL=C

cd "$RAIZ" || { echo "::error title=trazabilidad::cannot enter $RAIZ"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "::error title=trazabilidad::python3 is missing"; exit 1; }

SALIDA="$(python3 - "$RAIZ" <<'PY'
import os, re, sys

raiz = sys.argv[1]
ESTADOS = ("CURRENT", "UNPROVEN", "PENDING")

# The baseline AND the deltas of in-flight changes. A delta lands in `openspec/specs/` when
# archived, so a consequence with no state smuggled into a delta ends up in the baseline
# undeclared — and there nobody looks at it again, because the guardian would only demand a state
# of what was already inside. Demanding it in the change is failing early. The archive is left
# out: it is history, and rewriting history is not tracing.
specs = []
base = os.path.join(raiz, "openspec", "specs")
for d in sorted(os.listdir(base)) if os.path.isdir(base) else []:
    f = os.path.join(base, d, "spec.md")
    if os.path.isfile(f):
        specs.append(f)
cambios = os.path.join(raiz, "openspec", "changes")
for dirpath, _dirnames, filenames in sorted(os.walk(cambios)) if os.path.isdir(cambios) else []:
    if os.sep + "archive" + os.sep in dirpath + os.sep:
        continue
    if "spec.md" in filenames and os.sep + "specs" in dirpath:
        specs.append(os.path.join(dirpath, "spec.md"))

if not specs:
    print("VACIO")
    raise SystemExit(0)

RE_REQ = re.compile(r"^### Requirement:\s*(.+?)\s*$", re.M)
RE_ESC = re.compile(r"^#### Scenario:\s*(.+?)\s*$", re.M)
RE_EST = re.compile(r"\*\*Status:\*\*\s*([A-Z ]+?)(?:\s|$)", re.M)
RE_PRU = re.compile(r"\*\*Proof:\*\*\s*`([^`]+)`", re.M)
RE_MOT = re.compile(r"\*\*Reason:\*\*\s*(\S)", re.M)

cuenta = {e: 0 for e in ESTADOS}
por_capacidad = {}
total = 0
fallos = []
repetidos = []
sin_consecuencia = []

def trozos(texto, regex):
    """(title, body) for each header match, body running to the next header of the same level."""
    ms = list(regex.finditer(texto))
    for i, m in enumerate(ms):
        fin = ms[i + 1].start() if i + 1 < len(ms) else len(texto)
        yield m.group(1), texto[m.end():fin]

for f in specs:
    rel = os.path.relpath(f, raiz)
    cap = os.path.basename(os.path.dirname(f))
    texto = open(f, encoding="utf-8").read()

    # A repeated requirement title within one file makes `openspec archive`'s MODIFIED matching
    # ambiguous — it matches on the literal header text. Worse and quieter: a repeated name hides
    # a requirement WITHOUT lowering the count. Checked per file and not globally on purpose: a
    # change delta legitimately repeats the header of the requirement it modifies.
    titulos = [t for t, _ in trozos(texto, RE_REQ)]
    for t in sorted({t for t in titulos if titulos.count(t) > 1}):
        repetidos.append("%s :: repeated requirement title %r" % (rel, t))

    for titulo, cuerpo in trozos(texto, RE_REQ):
        consecuencias = list(trozos(cuerpo, RE_ESC))
        if not consecuencias:
            sin_consecuencia.append("%s :: %s" % (cap, titulo))
            continue
        for nombre, bloque in consecuencias:
            total += 1
            donde = "%s :: %s → %s" % (cap, titulo, nombre)
            encontrados = [e.strip() for e in RE_EST.findall(bloque)]
            validos = [e for e in encontrados if e in ESTADOS]
            if len(validos) != 1:
                fallos.append("%s → declares %d valid **Status:** (needs exactly one of %s); found %r"
                              % (donde, len(validos), "/".join(ESTADOS), encontrados))
                continue
            estado = validos[0]
            cuenta[estado] += 1
            por_capacidad.setdefault(cap, {e: 0 for e in ESTADOS})[estado] += 1
            if estado == "CURRENT":
                ref = RE_PRU.search(bloque)
                if not ref:
                    fallos.append("%s → CURRENT with no **Proof:**" % donde)
                    continue
                ref = ref.group(1)
                if "::" not in ref:
                    fallos.append("%s → **Proof:** `%s` is not `path::test_name`. A path alone is "
                                  "satisfied by any file and a name alone anchors to nothing." % (donde, ref))
                    continue
                ruta, nombre_test = ref.split("::", 1)
                abs_ruta = os.path.join(raiz, ruta)
                if not os.path.isfile(abs_ruta):
                    fallos.append("%s → **Proof:** names `%s`, which does NOT exist" % (donde, ruta))
                elif nombre_test not in open(abs_ruta, encoding="utf-8", errors="replace").read():
                    fallos.append("%s → `%s` exists but does not contain `%s`" % (donde, ruta, nombre_test))
            elif estado in ("PENDING", "UNPROVEN"):
                # UNPROVEN is demanded a reason for the same cause as PENDING: without one it is
                # indistinguishable from an oversight, and UNPROVEN is the dangerous state — real
                # behaviour that nothing pins, which regresses without any red announcing it.
                if not RE_MOT.search(bloque):
                    fallos.append("%s → %s with no **Reason:**. A state that is not CURRENT and "
                                  "carries no written reason is indistinguishable from an "
                                  "oversight." % (donde, estado))

print("OK")
print(len(specs))
print(total)
print(cuenta["CURRENT"], cuenta["UNPROVEN"], cuenta["PENDING"])
print(len(fallos) + len(repetidos) + len(sin_consecuencia))
# The breakdown behind the total. A number has nowhere to put a footnote: read on its own, a
# census cannot distinguish a consequence that was retired from a test that disappeared, and
# both move it by the same amount. The list can be attributed; the total cannot.
for cap in sorted(por_capacidad):
    c = por_capacidad[cap]
    print("CAP\t%s\t%d\t%d\t%d" % (cap, c["CURRENT"], c["UNPROVEN"], c["PENDING"]))
for x in repetidos + sin_consecuencia + fallos:
    print("  " + x)
PY
)"

ESTADO="$(printf '%s' "$SALIDA" | sed -n 1p)"

rojo() {
  local titulo="$1"; shift
  echo "::error title=trazabilidad::$titulo"
  printf '%s\n' "$@"
  { echo "**RED — $titulo**"; echo; printf '%s\n' "$@"; } >> "$SUMMARY"
  exit 1
}

if [ "$ESTADO" = "VACIO" ]; then
  rojo "there is no spec in \`openspec/specs/\` nor any delta in \`openspec/changes/\`" \
    "This guardian certifies nothing about an empty corpus, exactly like the kit's."
fi
[ "$ESTADO" = "OK" ] || rojo "the census did not run" "$SALIDA"

FICHEROS="$(printf '%s' "$SALIDA" | sed -n 2p)"
TOTAL="$(printf '%s' "$SALIDA" | sed -n 3p)"
read -r VIG UNP PEN <<< "$(printf '%s' "$SALIDA" | sed -n 4p)"
NFALLOS="$(printf '%s' "$SALIDA" | sed -n 5p)"
DETALLE="$(printf '%s' "$SALIDA" | sed -n '6,$p' | grep -v '^CAP	')"
DESGLOSE="$(printf '%s' "$SALIDA" | grep '^CAP	' | awk -F'\t' '{printf "  %-18s %3d · %2d · %2d\n", $2, $3, $4, $5}')"

if [ "$NFALLOS" -gt 0 ]; then
  rojo "$NFALLOS consequence(s) do not declare their state or their proof does not resolve" "$DETALLE"
fi

# Measured, never gated. The threshold, if there is to be one, belongs to the management system
# and not to this repository.
PROP="$(python3 -c "print('%.0f' % (100.0*$PEN/$TOTAL) if $TOTAL else 0)")"
MSG="GREEN — and only for what it covers: across ${FICHEROS} capability file(s), all ${TOTAL}
consequences declare exactly one state, every CURRENT names a test whose path exists and whose
name appears inside it, and every PENDING and UNPROVEN carries a reason.
  CURRENT ${VIG} · UNPROVEN ${UNP} · PENDING ${PEN} · total ${TOTAL}
                     current · unproven · pending
${DESGLOSE}
  backlog: ${PROP}% of the corpus describes something that does not exist yet (measured, not gated)
This says NOTHING about whether the named test RAN, whether it CAN FAIL, or whether it proves the
requirement. The first two are vigencia.sh. The third is whoever asked for the change."
echo "$MSG"
{ echo "**trazabilidad — $MSG**"; } >> "$SUMMARY"
exit 0
