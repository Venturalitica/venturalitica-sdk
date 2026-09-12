#!/usr/bin/env bash
# Guardian of the method kit (`openspec`), in a script of its own so that it can be TESTED.
#
# Why this is not a bare `run: openspec validate --all --strict`, which is what looks sufficient:
#
#   MEASURED IN THIS TREE ON 2026-09-11 with `@fission-ai/openspec@1.11.0`:
#
#     one malformed spec ....... EXIT=1   «Totals: 0 passed, 1 failed (1 items)»
#     EMPTY corpus ............. EXIT=0   «items=0, passed=0, failed=0»
#
#   **By exit code, an empty corpus is indistinguishable from a healthy one.** Emptying
#   `openspec/specs/`, or the instrument failing to find the root, leaves a bare gate GREEN
#   without having checked anything. An assertion of emptiness does not discriminate on its own,
#   and here the defect lands inside a third party's instrument where it cannot be fixed — only
#   wrapped.
#
# Hence the rule that governs this file, which is the house rule applied to someone else's tool:
#
#     A third-party binary's verdict is NOT read from its exit code.
#     It is read from what it says it measured, and contrasted with the tree.
#
# Four demands, and any one of them false is RED:
#
#   1. the output parses as JSON — if the instrument did not speak, it did not measure;
#   2. `summary.totals.items` >= 1 — an empty corpus is not a green;
#   3. the spec ids the instrument reports MATCH the `spec.md` directories in the tree, name by
#      name — nothing invisible, neither surplus nor missing;
#   4. `summary.totals.failed` == 0.
#
# Plus demand 0, which comes first: the running binary is the one this repository pins. Without
# it the pin is a declaration nobody executes, and an instrument with no known calibration state
# is not an instrument (ISO 9001 §7.1.5).
#
# WHAT THIS GUARDIAN DOES NOT MEASURE, and you have to know it before reading its green:
# `openspec validate` is STRUCTURAL. Measured here on 2026-09-11: a requirement whose
# `#### Scenario:` has the single letter `z` for its entire body passes `--all --strict` with
# exit 0. It checks the document is WELL-FORMED, never that the requirement says anything. That
# an acceptance criterion answers what was asked is covered by no gate here or anywhere: it is
# covered by whoever asked for the change, closing their issue against a check of their own
# (CLAUDE.md).
#
# That same limit is why it is admissible inside the gate chain despite being a third party's: a
# structural validator can only fail CLOSED. It cannot green-light a bad product, because it does
# not look at the product. Its red says «our design records are malformed», and that is a
# legitimate reason not to emit a record set that includes them.
#
# JSON is parsed with `python3`, not `jq`: this is a Python repository, python3 is present
# wherever the suite runs, and the guardian must not fall over because a runner image dropped a
# helper.
#
# Input: none. Runs from the repository root.
#   OPENSPEC_BIN    binary path (default: the one from the lock)
#   OPENSPEC_RAIZ   root to inspect (default: cwd) — for the falsifier only
# Output: `::error` annotations plus a summary. 0 green, 1 red.
set -uo pipefail

RAIZ="${OPENSPEC_RAIZ:-$PWD}"
BIN="${OPENSPEC_BIN:-$RAIZ/.github/openspec/node_modules/.bin/openspec}"
MANIFIESTO="${OPENSPEC_MANIFIESTO:-$RAIZ/.github/openspec/package.json}"
SUMMARY="${GITHUB_STEP_SUMMARY:-/dev/null}"
export LC_ALL=C

# Telemetry is switched off here as well as in the workflow, because this script is also run
# locally by hand where no job `env:` covers it. This is transfer to a third party (ISO 27001
# A.5.23, A.8.9) and the kit's own opt-out is NOT versionable — `openspec config` is explicitly
# global and writes to `~/.config/openspec/config.json`. These two variables are the only thing
# this repository can impose. Declared gap, not a papered-over one.
export OPENSPEC_TELEMETRY=0
export DO_NOT_TRACK=1

# The reason goes to BOTH places, and that is not redundancy: the job summary is read by whoever
# opens the tab, the log by whoever is debugging — which is the case that matters when the gate
# goes red for a reason that does not resemble its cause.
rojo() {
  local titulo="$1"; shift
  echo "::error title=openspec-gate::$titulo"
  printf '%s\n' "$@"
  { echo "**RED — $titulo**"; echo; printf '%s\n' "$@"; } >> "$SUMMARY"
  exit 1
}

command -v python3 >/dev/null 2>&1 || rojo "python3 is missing" "The guardian parses the instrument's JSON with python3."
cd "$RAIZ" || rojo "cannot enter $RAIZ"

[ -x "$BIN" ] || rojo "the kit binary is not at \`$BIN\`" \
  "Was \`npm ci --prefix .github/openspec\` skipped? The kit is installed from the lock, never" \
  "from PATH: a global binary does not appear in the commit and its version would not be" \
  "reconstructible (ISO 9001 §7.5.3)."

# ── 0. The running version is the one the repository pins ───────────────────────────────────────
[ -f "$MANIFIESTO" ] || rojo "no manifest at \`$MANIFIESTO\`" "The pin has to live in a file that travels in the commit."

PIN="$(python3 -c '
import json,sys
try:
    d=json.load(open(sys.argv[1]))
except Exception as e:
    print("ERR:"+str(e)); raise SystemExit(0)
print((d.get("devDependencies") or {}).get("@fission-ai/openspec","MISSING"))
' "$MANIFIESTO")"

case "$PIN" in
  ERR:*)    rojo "the manifest does not parse" "$PIN" ;;
  MISSING)  rojo "the manifest does not pin \`@fission-ai/openspec\`" "Without a pin there is nothing to compare the running binary against." ;;
esac

# The pin must be an EXACT version. Otherwise the comparison below can never succeed and the
# guardian sits permanently red — a noisy failure mode, which is the good kind, but only if the
# reason printed is the real one. So a pin that is not a version is named as such.
#
# ALLOWLIST, not a blocklist of range characters. The first version of this check listed the
# forbidden characters (^ ~ > < | * x) and asked whether the pin contained any. Swept on
# 2026-09-11 and it was the same defect this repository had just found elsewhere: a substring test
# standing in for an identity test. It accepted `1.11`, `1` and `latest`, all of which npm
# resolves as ranges — and the guardian would then go red for a VERSION MISMATCH, which is the
# wrong reason, which is precisely what naming the range exists to prevent. So the pin must LOOK
# LIKE an exact version rather than merely not look like a range.
if ! printf '%s' "$PIN" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$'; then
  rojo "the pin \`$PIN\` is not an exact version" \
    "This guardian compares the running binary against the pin, so the pin has to BE a value." \
    "Anything npm can resolve to more than one release — a range like \`^1.11.0\`, a partial" \
    "version like \`1.11\`, or a tag like \`latest\` — would make the comparison fail as a" \
    "mismatch and hide the real cause. Write it in full, e.g. \"1.11.0\"."
fi

VERSION="$("$BIN" --version 2>/dev/null | tr -d '[:space:]')"
[ -n "$VERSION" ] || rojo "the binary did not report a version" "\`$BIN --version\` printed nothing."
[ "$VERSION" = "$PIN" ] || rojo "the running kit is not the pinned one" \
  "manifest pins \`$PIN\`, the binary that ran is \`$VERSION\`." \
  "\`npm ci\` closes manifest against lock; a mismatch means something installed outside it."

# ── 1..4. Read what the instrument says it measured, and contrast it with the tree ──────────────
SALIDA="$("$BIN" validate --all --strict --json 2>/dev/null)"

# The tree's census is taken HERE, independently of the instrument, so that demand 3 compares two
# sources rather than one source with itself.
mapfile -t EN_ARBOL < <(find openspec/specs -mindepth 2 -maxdepth 2 -name spec.md 2>/dev/null \
  | sed 's#^openspec/specs/##; s#/spec.md$##' | sort)

VEREDICTO="$(printf '%s' "$SALIDA" | python3 -c '
import json,sys
crudo=sys.stdin.read()
try:
    d=json.loads(crudo)
except Exception:
    print("NOJSON"); raise SystemExit(0)
try:
    t=d["summary"]["totals"]
    ids=sorted(i.get("id","") for i in d.get("items",[]) if i.get("type","spec")=="spec")
except Exception as e:
    print("NOFORMA:"+str(e)); raise SystemExit(0)
print("OK")
print(int(t.get("items",0)))
print(int(t.get("failed",0)))
print(" ".join(ids))
')"

ESTADO="$(printf '%s' "$VEREDICTO" | sed -n 1p)"
case "$ESTADO" in
  NOJSON)
    rojo "the instrument did not emit parseable JSON" \
      "If the instrument did not speak, it did not measure. Its exit code is not read here." \
      "What it printed:" "$(printf '%s' "$SALIDA" | head -20)" ;;
  NOFORMA:*)
    rojo "the instrument's JSON does not have the expected shape" \
      "Expected \`summary.totals\` and \`items[]\`. Detail: ${ESTADO#NOFORMA:}" \
      "A kit upgrade can move this shape: that is a reason to look, not to wave through." ;;
esac

ITEMS="$(printf '%s' "$VEREDICTO" | sed -n 2p)"
FALLIDOS="$(printf '%s' "$VEREDICTO" | sed -n 3p)"
read -r -a REPORTADOS <<< "$(printf '%s' "$VEREDICTO" | sed -n 4p)"

# ── 2. An empty corpus is not a green ──────────────────────────────────────────────────────────
if [ "$ITEMS" -lt 1 ]; then
  rojo "the instrument validated NOTHING (items=0) and still exited 0" \
    "This is the measured trap: by exit code an empty corpus is indistinguishable from a healthy" \
    "one. Either \`openspec/specs/\` is empty, or the instrument did not find the root." \
    "Directories with a spec.md found in the tree: ${#EN_ARBOL[@]}"
fi

# ── 3. Census before verdict: what it says it saw against what is there ────────────────────────
FALTAN=(); SOBRAN=()
for c in "${EN_ARBOL[@]}"; do
  printf '%s\n' "${REPORTADOS[@]}" | grep -qxF -- "$c" || FALTAN+=("$c")
done
for r in "${REPORTADOS[@]}"; do
  [ -n "$r" ] || continue
  printf '%s\n' "${EN_ARBOL[@]}" | grep -qxF -- "$r" || SOBRAN+=("$r")
done

if [ "${#FALTAN[@]}" -gt 0 ] || [ "${#SOBRAN[@]}" -gt 0 ]; then
  rojo "the tree and the instrument's report disagree" \
    "In the tree but NOT validated: ${FALTAN[*]:-none}" \
    "Validated but NOT in the tree: ${SOBRAN[*]:-none}" \
    "A spec the instrument never saw is a design record nobody checked, and its absence would" \
    "otherwise read exactly like a pass."
fi

# ── 4. Nothing failed ──────────────────────────────────────────────────────────────────────────
if [ "$FALLIDOS" -gt 0 ]; then
  DETALLE="$("$BIN" validate --all --strict 2>&1 | head -40)"
  rojo "$FALLIDOS design record(s) are malformed" "$DETALLE"
fi

# The green is never printed bare. It carries the name of what it covers, because a green read
# as more than it covers is how a gate becomes decorative.
MSG="GREEN — and only for what it covers: ${ITEMS} design record(s) are WELL-FORMED under
openspec ${VERSION} (--all --strict), and the instrument's report matches the tree name by name.
This says NOTHING about whether any requirement is true, whether its scenario says anything, or
whether its test proves it. A scenario whose whole body is the letter 'z' passes this gate."
echo "$MSG"
{ echo "**openspec-gate — $MSG**"; } >> "$SUMMARY"
exit 0
