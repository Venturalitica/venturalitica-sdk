#!/usr/bin/env bash
# Guardian of WHAT LEAVES: the distribution contains what this repository declared it would, and
# nothing cites what a reader outside cannot resolve.
#
# Why it exists. `pyproject.toml` controls the distribution with an `exclude` list — a blocklist.
# It names what must not ship and lets through everything nobody thought to name. Measured on
# 2026-09-16, that had let through a stray LaTeX log, the git ignore file, the pre-commit config,
# the repository's CODEOWNERS, and — the one that mattered — a citation to a PRIVATE repository
# inside `src/venturalitica/assurance/power.py`, which is code that people import.
#
# A blocklist's coverage grows one line per incident. It gets long and respectable while its shape
# stays permissive.
#
# TWO CHECKS, AND NEITHER COVERS THE OTHER. That distinction is the whole design, and it was
# nearly lost: an allowlist of FILES answers «what ships», and says nothing about what is written
# inside a file that legitimately ships. The private citation travelled inside `power.py`, which
# belongs in the package. Believing one check covers the other is the failure this repository has
# now made three times in a week.
#
#   1. EVERY non-code file in the artefact is declared in `.github/packaging/ships.yml`.
#   2. NOTHING in the artefact cites what a reader outside the organisation cannot resolve:
#      an issue in another repository, or a dated design record that exists in neither the
#      package nor this repository.
#
# WHAT THIS GUARDIAN DOES NOT COVER, and it has to be read with its green: whether the prose of a
# shipped file identifies a customer indirectly. A device class, a patient count and a date can
# name somebody without containing a name, and no pattern here catches that. That half is read by
# a person.
#
# Input:
#   $1 or QUE_SALE_SDIST   path to the built sdist (default: the newest under dist/)
#   QUE_SALE_RAIZ          root to inspect (default: cwd) — for the falsifier only
# Output: `::error` annotations plus a summary. 0 green, 1 red.
set -uo pipefail

RAIZ="${QUE_SALE_RAIZ:-$PWD}"
MANIFIESTO="${QUE_SALE_MANIFIESTO:-$RAIZ/.github/packaging/ships.yml}"
SUMMARY="${GITHUB_STEP_SUMMARY:-/dev/null}"
export LC_ALL=C

rojo() {
  local titulo="$1"; shift
  echo "::error title=que-sale::$titulo"
  printf '%s\n' "$@"
  { echo "**RED — $titulo**"; echo; printf '%s\n' "$@"; } >> "$SUMMARY"
  exit 1
}

command -v python3 >/dev/null 2>&1 || rojo "python3 is missing"
[ -f "$MANIFIESTO" ] || rojo "no manifest at \`$MANIFIESTO\`" \
  "Without it there is nothing to compare the artefact against, and an artefact compared with" \
  "nothing is the empty-corpus trap in another costume."

SDIST="${1:-${QUE_SALE_SDIST:-$(ls -t "$RAIZ"/dist/*.tar.gz 2>/dev/null | head -1)}}"
[ -n "$SDIST" ] && [ -f "$SDIST" ] || rojo "no sdist to inspect" \
  "Pass it as \$1 or build it first. This guardian FAILS without the artefact rather than" \
  "certifying nothing: a green that cannot tell «clean» from «not built» is worthless."

SALIDA="$(python3 - "$RAIZ" "$MANIFIESTO" "$SDIST" <<'PY'
import os, re, sys, tarfile

raiz, manifiesto, sdist = sys.argv[1], sys.argv[2], sys.argv[3]

try:
    import yaml
    datos = yaml.safe_load(open(manifiesto, encoding="utf-8")) or {}
except Exception as e:
    print("NOMANIFIESTO:" + str(e)); raise SystemExit(0)

declarados = set(datos.get("ships") or [])
pendientes = set(datos.get("pending_decision") or [])
if not declarados:
    print("VACIO"); raise SystemExit(0)

# ── What is actually in the artefact ────────────────────────────────────────────────────────────
try:
    tar = tarfile.open(sdist)
except Exception as e:
    print("NOSDIST:" + str(e)); raise SystemExit(0)

contenido = {}   # ruta relativa a la raíz del sdist -> bytes (sólo texto)
for m in tar.getmembers():
    if not m.isfile():
        continue
    rel = m.name.split("/", 1)[1] if "/" in m.name else m.name
    try:
        contenido[rel] = tar.extractfile(m).read()
    except Exception:
        contenido[rel] = b""

no_codigo = sorted(r for r in contenido if not r.endswith(".py"))
if not no_codigo:
    print("ARTEFACTOVACIO"); raise SystemExit(0)

# ── 1. Allowlist ────────────────────────────────────────────────────────────────────────────────
permitidos = declarados | pendientes
sin_declarar = [r for r in no_codigo if r not in permitidos]
muertos = sorted(r for r in permitidos if r not in contenido)

# Filenames present anywhere in the repository, so that a record we do keep is not flagged.
en_repo = set()
for dirpath, _dn, fns in os.walk(raiz):
    if "/.git" in dirpath:
        continue
    en_repo.update(fns)

# ── 2. References nothing outside can resolve ───────────────────────────────────────────────────
# An issue in another repository. This repository's own `#N` is fine and so is `Venturalitica/
# venturalitica-sdk#N`; anything else points somewhere a reader may not be able to open.
RE_AJENA = re.compile(rb"\b([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)#(\d+)")
ESTE = (b"Venturalitica", b"venturalitica-sdk")
# A DESIGN DOCUMENT cited by its dated filename. Narrowed on purpose, and the first version was
# wrong in a way worth recording: it flagged every `.md` filename that was not in the package or
# the repository, and produced 22 hits of which 20 were noise — `Annex_IV.md`,
# `assurance_report.md` and friends are output filenames the SDK GENERATES, not citations of
# anything. A guardian that fires twenty times to catch two gets ignored, and then it catches
# nothing.
#
# Telling a citation from a generated filename is not mechanisable without false positives. What
# IS mechanisable is the naming convention of an internal design record: a leading date. Nothing
# this SDK writes is named that way.
RE_DOC = re.compile(rb"\b(\d{4}-\d{2}-\d{2}-[A-Za-z0-9._-]+)\.md\b")

# 2c. UNA REFERENCIA A ISSUE SIN CUALIFICAR, en el código que se instala. `#977` se lee como la
# issue 977 de ESTE repositorio, que no existe: apunta a un tracker privado. Cualificarla sería
# peor —citaría el repositorio privado desde el paquete— así que la regla es que el código que
# viaja no lleve el número, y que la prosa se sostenga sola.
#
# Sólo `src/`. El CHANGELOG queda fuera a propósito y con motivo: es un registro fechado de lo que
# se dijo en cada versión, y reescribirlo para que resuelva hoy sería falsificar lo que decía
# entonces. Es la misma distinción que separa un contrato, que debe estar vigente, de una entrada
# de changelog, que debe ser fiel.
# El `#` tiene que abrir la referencia: principio de línea, espacio, `(` o `[`. Sin eso la
# comprobación marcaba el número DENTRO de la forma cualificada que la comprobación anterior
# permite —`Venturalitica/venturalitica-sdk#10`— y las dos se contradecían. Lo cazó el falsador.
RE_DESNUDA = re.compile(rb"(?:^|(?<=[\s(\[]))#(\d{2,4})(?![0-9a-fA-F])")
RE_COLOR = re.compile(rb"fill=|stop-color=|color:|background")

colgantes = []
for ruta in sorted(contenido):
    if not ruta.startswith("src/") or not ruta.endswith(".py"):
        continue
    for linea in contenido[ruta].split(b"\n"):
        if RE_COLOR.search(linea):
            continue
        for m in RE_DESNUDA.finditer(linea):
            colgantes.append("%s cites `%s` — a bare issue number. It reads as this repository's "
                             "issue and is not one; qualifying it would cite a private tracker "
                             "from an installed package" % (ruta, m.group(0).decode()))

for ruta in sorted(contenido):
    texto = contenido[ruta]
    for m in RE_AJENA.finditer(texto):
        if (m.group(1), m.group(2)) != ESTE:
            colgantes.append("%s cites `%s` — an issue in another repository"
                             % (ruta, m.group(0).decode("utf-8", "replace")))
    for m in RE_DOC.finditer(texto):
        nombre = m.group(0).decode("utf-8", "replace")
        if nombre in contenido or nombre in en_repo:
            continue
        colgantes.append("%s cites `%s` — a dated design record that is in neither the package "
                         "nor the repository" % (ruta, nombre))

print("OK")
print(len(no_codigo), len(declarados), len(pendientes))
print("SINDECLARAR\t" + "\t".join(sin_declarar))
print("MUERTOS\t" + "\t".join(muertos))
print("PENDIENTES\t" + "\t".join(sorted(pendientes)))
for c in colgantes:
    print("COLGANTE\t" + c)
PY
)"

ESTADO="$(printf '%s' "$SALIDA" | sed -n 1p)"
case "$ESTADO" in
  NOMANIFIESTO:*)  rojo "the manifest does not parse" "${ESTADO#NOMANIFIESTO:}" ;;
  NOSDIST:*)       rojo "the sdist could not be read" "${ESTADO#NOSDIST:}" ;;
  VACIO)           rojo "the manifest declares nothing" \
                     "An empty allowlist would make every comparison below vacuous and this gate green." ;;
  ARTEFACTOVACIO)  rojo "the artefact holds no non-code file at all" \
                     "Even a correct package carries its licence and its metadata. Something is wrong upstream." ;;
  OK)              ;;
  *)               rojo "the census did not run" "$SALIDA" ;;
esac

read -r N_ARCH N_DECL N_PEND <<< "$(printf '%s' "$SALIDA" | sed -n 2p)"
SIN="$(printf '%s' "$SALIDA" | grep '^SINDECLARAR' | cut -f2- | tr '\t' '\n' | grep -v '^$')"
MUERTOS="$(printf '%s' "$SALIDA" | grep '^MUERTOS' | cut -f2- | tr '\t' '\n' | grep -v '^$')"
PEND="$(printf '%s' "$SALIDA" | grep '^PENDIENTES' | cut -f2- | tr '\t' '\n' | grep -v '^$')"
COLG="$(printf '%s' "$SALIDA" | grep '^COLGANTE' | cut -f2-)"

if [ -n "$SIN" ]; then
  rojo "$(printf '%s\n' "$SIN" | grep -c .) file(s) leave this repository undeclared" \
    "$SIN" "" \
    "They are in the distribution and not in \`.github/packaging/ships.yml\`. Either they belong" \
    "there, or they belong in \`pyproject.toml\`'s exclude list. Deciding which is the point of" \
    "this gate: it refuses to let the question stay unanswered."
fi

if [ -n "$MUERTOS" ]; then
  rojo "$(printf '%s\n' "$MUERTOS" | grep -c .) declared file(s) do not ship" \
    "$MUERTOS" "" \
    "A dead entry is worse than a missing one: it reads as coverage. Either the file stopped" \
    "shipping and the manifest was not updated, or it never shipped and the entry was a guess."
fi

if [ -n "$COLG" ]; then
  rojo "$(printf '%s\n' "$COLG" | grep -c .) reference(s) in the distribution resolve for nobody outside" \
    "$COLG" "" \
    "A published artefact is installed on other people's machines. A citation to a private" \
    "repository or to a document that exists nowhere public is a dangling reference there, and" \
    "the reader has no way to know that. This is the rule the design corpus already holds itself" \
    "to, applied to the other thing that leaves this repository."
fi

MSG="GREEN — and only for what it covers: all ${N_ARCH} non-code file(s) in the distribution are
declared, every declared entry actually ships, and nothing in it cites another repository's issues
a dated design record that exists nowhere public, or a bare issue number in shipped code.
  declared ${N_DECL} · shipping today but pending a decision ${N_PEND}
$(printf '%s' "$PEND" | sed 's/^/    /')
Those are not failures and not approvals: they ship, nobody decided they should, and removing them
changes the published artefact. They are printed every run so the decision stays visible.
It does NOT catch every unresolvable filename. Distinguishing a citation from a filename the SDK
generates is not mechanisable without noise, and the first version of this check produced twenty
false alarms for two real findings. It catches what has a convention: cross-repository issues and
dated design records.
This says NOTHING about whether the PROSE of a shipped file identifies somebody indirectly. A
device class, a patient count and a date can name a customer without containing a name, and no
pattern here catches that. A person reads that half."
echo "$MSG"
{ echo "**que-sale — $MSG**"; } >> "$SUMMARY"
exit 0
