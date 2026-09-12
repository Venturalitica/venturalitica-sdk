#!/usr/bin/env bash
# Falsifier for `openspec-gate.sh`: proves the guardian knows how to go RED, and goes red FOR THE
# NAMED REASON.
#
# Why the reason is asserted and not just the exit code. Learned the hard way in the sibling
# MET-SPEC repository on 2026-09-11: a red from the wrong assertion reads exactly like a good one.
# A mutation was seeded to watch a guardian bite, it went red, and it went red because of a
# formatting slip introduced by accident — not because of the subject under test. So each case
# below FIXES what it believes it is provoking and moves nothing else, and then requires the
# reason it expected to appear in the output.
#
# WHY THIS LIVES IN THE openspec JOB and not in a general helper batch: three of its cases
# exercise the REAL pinned binary's behaviour (the empty-corpus trap, a malformed scenario, a
# requirement with no English SHALL), and the pin cases need it present. If the kit is absent this
# falsifier FAILS rather than skipping those cases in silence — a suite that quietly drops the
# cases needing the instrument is the same green that cannot tell «passed» from «was not asked».
#
# The other cases use a STUB binary on purpose. They are about the guardian's own contract — that
# it reads what the instrument says it measured and contrasts it with the tree — and the only
# honest way to falsify a comparison of two sources is to make the sources disagree.
set -uo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$AQUI/../.." && pwd)"
GUARDIAN="$AQUI/openspec-gate.sh"
REAL="$REPO/.github/openspec/node_modules/.bin/openspec"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export GITHUB_STEP_SUMMARY=/dev/null
ok=0; mal=0

# The kit has to be there. Declared as a contract, not assumed.
if [ ! -x "$REAL" ]; then
  echo "::error title=openspec-gate.test::the pinned kit is not installed at $REAL"
  echo "Cases below need the REAL binary. Failing instead of skipping them: a falsifier that"
  echo "drops the cases needing the instrument certifies nothing while looking green."
  exit 1
fi

# ── fixtures ────────────────────────────────────────────────────────────────────────────────────
spec_sana() {
  mkdir -p "$1/openspec/specs/muestra"
  cat > "$1/openspec/specs/muestra/spec.md" <<'MD'
# muestra

## Purpose

A sample capability used only by the falsifier, long enough to satisfy the fifty-character
minimum that a new capability's Purpose has to meet.

## Requirements

### Requirement: The sample holds

The system SHALL hold the sample.

#### Scenario: The sample is held
- **Status:** CURRENT
- **WHEN** the sample is taken
- **THEN** it is held
MD
}

manifiesto() {  # $1 raiz, $2 pin
  mkdir -p "$1/.github/openspec"
  printf '{"devDependencies":{"@fission-ai/openspec":"%s"}}\n' "$2" > "$1/.github/openspec/package.json"
}

stub() {  # $1 destino, $2 version, $3 json
  mkdir -p "$(dirname "$1")"
  { echo '#!/usr/bin/env bash'
    echo "if [ \"\${1:-}\" = \"--version\" ]; then echo '$2'; exit 0; fi"
    printf 'cat <<%s\n%s\n%s\n' "JSONEOF" "$3" "JSONEOF"
  } > "$1"
  chmod +x "$1"
}

caso() {  # $1 nombre, $2 motivo-esperado, resto: entorno...
  local nombre="$1" motivo="$2"; shift 2
  local salida rc
  salida="$("$@" bash "$GUARDIAN" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "  ✗ $nombre — the guardian stayed GREEN; it should have gone red for: $motivo"
    mal=$((mal+1)); return
  fi
  if ! printf '%s' "$salida" | grep -qF -- "$motivo"; then
    echo "  ✗ $nombre — went red, but NOT for the expected reason."
    echo "      expected: $motivo"
    echo "      said:     $(printf '%s' "$salida" | head -3 | tr '\n' ' ')"
    mal=$((mal+1)); return
  fi
  echo "  ✓ $nombre"
  ok=$((ok+1))
}

echo "falsifier for openspec-gate.sh"

# ── 1. REAL binary: an empty corpus is not a green ─────────────────────────────────────────────
# This is THE measured trap: openspec exits 0 on an empty corpus. Nothing else is moved.
R="$TMP/vacio"; mkdir -p "$R/openspec/specs"; manifiesto "$R" "$(cat <<<"$($REAL --version)")"
caso "empty corpus is not a green" "validated NOTHING" \
  env OPENSPEC_RAIZ="$R" OPENSPEC_BIN="$REAL"

# ── 2. REAL binary: a malformed scenario (three hashes) ────────────────────────────────────────
R="$TMP/tres"; spec_sana "$R"; manifiesto "$R" "$($REAL --version)"
sed -i 's/^#### Scenario:/### Scenario:/' "$R/openspec/specs/muestra/spec.md"
caso "a scenario demoted to three hashes" "malformed" \
  env OPENSPEC_RAIZ="$R" OPENSPEC_BIN="$REAL"

# ── 3. REAL binary: the requirement loses its English SHALL ────────────────────────────────────
R="$TMP/shall"; spec_sana "$R"; manifiesto "$R" "$($REAL --version)"
sed -i 's/SHALL hold/DEBERÁ sostener/' "$R/openspec/specs/muestra/spec.md"
caso "a requirement without SHALL/MUST in English" "malformed" \
  env OPENSPEC_RAIZ="$R" OPENSPEC_BIN="$REAL"

# ── 4. the pin is a range, and it is named AS a range ──────────────────────────────────────────
# Without this case the guardian would still go red, but for a version mismatch — the wrong
# reason for a permanently-red guardian, and the hardest kind of red to diagnose.
R="$TMP/rango"; spec_sana "$R"; manifiesto "$R" "^1.11.0"
caso "a ranged pin is named as such" "is not an exact version" \
  env OPENSPEC_RAIZ="$R" OPENSPEC_BIN="$REAL"

# The three the FIRST version of this check let through. It listed forbidden range characters and
# asked whether the pin contained any — a substring test doing the work of an identity test, the
# same defect this repository found in its own blame handling the same day. npm resolves all three
# to whatever it likes, and the guardian would then have gone red for a version MISMATCH: the
# wrong reason, which is exactly what naming the pin exists to prevent.
R="$TMP/parcial"; spec_sana "$R"; manifiesto "$R" "1.11"
caso "a partial version is not an exact pin" "is not an exact version" \
  env OPENSPEC_RAIZ="$R" OPENSPEC_BIN="$REAL"

R="$TMP/mayor"; spec_sana "$R"; manifiesto "$R" "1"
caso "a bare major is not an exact pin" "is not an exact version" \
  env OPENSPEC_RAIZ="$R" OPENSPEC_BIN="$REAL"

R="$TMP/etiqueta"; spec_sana "$R"; manifiesto "$R" "latest"
caso "a dist-tag is not an exact pin" "is not an exact version" \
  env OPENSPEC_RAIZ="$R" OPENSPEC_BIN="$REAL"

# ── 5. the manifest pins nothing ───────────────────────────────────────────────────────────────
R="$TMP/sinpin"; spec_sana "$R"; mkdir -p "$R/.github/openspec"
echo '{"devDependencies":{}}' > "$R/.github/openspec/package.json"
caso "a manifest that pins nothing" "does not pin" \
  env OPENSPEC_RAIZ="$R" OPENSPEC_BIN="$REAL"

# ── 6. STUB: the running binary is not the pinned one ──────────────────────────────────────────
R="$TMP/version"; spec_sana "$R"; manifiesto "$R" "1.11.0"
stub "$R/bin/openspec" "9.9.9" '{"items":[{"id":"muestra","type":"spec","valid":true}],"summary":{"totals":{"items":1,"passed":1,"failed":0}}}'
caso "a binary whose version is not the pin" "is not the pinned one" \
  env OPENSPEC_RAIZ="$R" OPENSPEC_BIN="$R/bin/openspec"

# ── 7. STUB: the instrument did not speak ──────────────────────────────────────────────────────
R="$TMP/mudo"; spec_sana "$R"; manifiesto "$R" "1.11.0"
stub "$R/bin/openspec" "1.11.0" 'this is not json at all'
caso "output that is not parseable JSON" "did not emit parseable JSON" \
  env OPENSPEC_RAIZ="$R" OPENSPEC_BIN="$R/bin/openspec"

# ── 8. STUB: the JSON has lost its shape (a kit upgrade moving the contract) ───────────────────
R="$TMP/forma"; spec_sana "$R"; manifiesto "$R" "1.11.0"
stub "$R/bin/openspec" "1.11.0" '{"resultado":"todo bien"}'
caso "JSON without the expected shape" "does not have the expected shape" \
  env OPENSPEC_RAIZ="$R" OPENSPEC_BIN="$R/bin/openspec"

# ── 9. STUB: a spec in the tree the instrument never saw ───────────────────────────────────────
# The quiet one. The instrument reports a clean pass over a corpus that is missing a record, and
# by totals alone that is indistinguishable from a healthy run.
R="$TMP/invisible"; spec_sana "$R"; manifiesto "$R" "1.11.0"
mkdir -p "$R/openspec/specs/oculta"; cp "$R/openspec/specs/muestra/spec.md" "$R/openspec/specs/oculta/spec.md"
stub "$R/bin/openspec" "1.11.0" '{"items":[{"id":"muestra","type":"spec","valid":true}],"summary":{"totals":{"items":1,"passed":1,"failed":0}}}'
caso "a spec in the tree that was never validated" "tree and the instrument's report disagree" \
  env OPENSPEC_RAIZ="$R" OPENSPEC_BIN="$R/bin/openspec"

# ── 10. STUB: the instrument reports a spec that is not in the tree ────────────────────────────
R="$TMP/fantasma"; spec_sana "$R"; manifiesto "$R" "1.11.0"
stub "$R/bin/openspec" "1.11.0" '{"items":[{"id":"muestra","type":"spec","valid":true},{"id":"fantasma","type":"spec","valid":true}],"summary":{"totals":{"items":2,"passed":2,"failed":0}}}'
caso "a validated spec that is not in the tree" "tree and the instrument's report disagree" \
  env OPENSPEC_RAIZ="$R" OPENSPEC_BIN="$R/bin/openspec"

# ── 11. the binary is simply absent ────────────────────────────────────────────────────────────
R="$TMP/ausente"; spec_sana "$R"; manifiesto "$R" "1.11.0"
caso "the kit binary is absent" "the kit binary is not at" \
  env OPENSPEC_RAIZ="$R" OPENSPEC_BIN="$R/bin/no-existe"

# ── and the control: the guardian goes GREEN on a healthy corpus ───────────────────────────────
# Without this, every case above would pass on a guardian hardwired to exit 1.
R="$TMP/sana"; spec_sana "$R"; manifiesto "$R" "$($REAL --version)"
if OPENSPEC_RAIZ="$R" OPENSPEC_BIN="$REAL" bash "$GUARDIAN" >/dev/null 2>&1; then
  echo "  ✓ a healthy corpus is GREEN (the guardian is not hardwired to red)"
  ok=$((ok+1))
else
  echo "  ✗ a healthy corpus went RED — every case above is worthless"
  mal=$((mal+1))
fi

echo
if [ "$mal" -gt 0 ]; then
  echo "::error title=openspec-gate.test::$mal of $((ok+mal)) contracts unmet"
  exit 1
fi
echo "openspec-gate.sh knows how to go red: $ok/$ok contracts, each for its named reason."
