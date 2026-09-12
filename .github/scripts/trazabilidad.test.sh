#!/usr/bin/env bash
# Falsifier for `trazabilidad.sh`: proves the guardian goes RED, and FOR THE NAMED REASON.
#
# Same discipline as the kit's falsifier: a red from the wrong assertion reads exactly like a good
# one, so every case fixes what it believes it is provoking, moves nothing else, and then requires
# the expected reason in the output.
#
# It needs no binary at all: this guardian reads the tree, not the instrument. That is also why it
# is a separate guardian rather than a flag on the other one — two guardians answering different
# questions never substitute for each other.
set -uo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUARDIAN="$AQUI/trazabilidad.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export GITHUB_STEP_SUMMARY=/dev/null
ok=0; mal=0

# A root with one capability and a real test file the citations can resolve against.
raiz() {
  local R="$TMP/$1"; rm -rf "$R"; mkdir -p "$R/openspec/specs/muestra" "$R/tests"
  cat > "$R/tests/test_muestra.py" <<'PY'
def test_la_muestra_se_sostiene():
    assert True
PY
  cat > "$R/openspec/specs/muestra/spec.md" <<'MD'
# muestra

## Purpose

A sample capability used only by the falsifier, long enough to satisfy the minimum.

## Requirements

### Requirement: The sample holds

The system SHALL hold the sample.

#### Scenario: The sample is held
- **Status:** CURRENT
- **Proof:** `tests/test_muestra.py::test_la_muestra_se_sostiene`
- **WHEN** the sample is taken
- **THEN** it is held
MD
  echo "$R"
}

caso() {  # $1 nombre, $2 raiz, $3 motivo-esperado
  local salida rc
  salida="$(TRAZA_RAIZ="$2" bash "$GUARDIAN" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "  ✗ $1 — stayed GREEN; should have gone red for: $3"; mal=$((mal+1)); return
  fi
  if ! printf '%s' "$salida" | grep -qF -- "$3"; then
    echo "  ✗ $1 — went red, but NOT for the expected reason."
    echo "      expected: $3"
    echo "      said:     $(printf '%s' "$salida" | head -3 | tr '\n' ' ')"
    mal=$((mal+1)); return
  fi
  echo "  ✓ $1"; ok=$((ok+1))
}

echo "falsifier for trazabilidad.sh"

R="$TMP/vacio"; mkdir -p "$R/openspec/specs"
caso "an empty corpus is not a green" "$R" "there is no spec in"

R="$(raiz sinestado)"; sed -i '/\*\*Status:\*\*/d' "$R/openspec/specs/muestra/spec.md"
caso "a consequence that declares no state" "$R" "declares 0 valid"

R="$(raiz dosestados)"; sed -i 's/- \*\*Status:\*\* CURRENT/- **Status:** CURRENT\n- **Status:** PENDING/' "$R/openspec/specs/muestra/spec.md"
caso "a consequence that declares two states" "$R" "declares 2 valid"

R="$(raiz inventado)"; sed -i 's/\*\*Status:\*\* CURRENT/**Status:** VIGENTE/' "$R/openspec/specs/muestra/spec.md"
caso "a state outside the three" "$R" "declares 0 valid"

R="$(raiz sinprueba)"; sed -i '/\*\*Proof:\*\*/d' "$R/openspec/specs/muestra/spec.md"
caso "a CURRENT with no proof" "$R" "CURRENT with no **Proof:**"

R="$(raiz mitad)"; sed -i 's#`tests/test_muestra.py::test_la_muestra_se_sostiene`#`tests/test_muestra.py`#' "$R/openspec/specs/muestra/spec.md"
caso "a proof that is a path with no test name" "$R" "is not \`path::test_name\`"

R="$(raiz rutamala)"; sed -i 's#tests/test_muestra.py::#tests/test_no_existe.py::#' "$R/openspec/specs/muestra/spec.md"
caso "a proof whose path does not exist" "$R" "which does NOT exist"

R="$(raiz nombremalo)"; sed -i 's#::test_la_muestra_se_sostiene#::test_que_no_esta_ahi#' "$R/openspec/specs/muestra/spec.md"
caso "a proof whose path exists but does not contain the name" "$R" "does not contain"

R="$(raiz sinmotivo)"; sed -i 's/\*\*Status:\*\* CURRENT/**Status:** PENDING/; /\*\*Proof:\*\*/d' "$R/openspec/specs/muestra/spec.md"
caso "a PENDING with no reason" "$R" "PENDING with no **Reason:**"

# UNPROVEN is the dangerous state: real behaviour nothing pins. Without a written reason it is
# indistinguishable from someone forgetting to fill the field in.
R="$(raiz sinmotivounproven)"; sed -i 's/\*\*Status:\*\* CURRENT/**Status:** UNPROVEN/; /\*\*Proof:\*\*/d' "$R/openspec/specs/muestra/spec.md"
caso "an UNPROVEN with no reason" "$R" "UNPROVEN with no **Reason:**"

# A repeated title hides a requirement WITHOUT lowering the count, and makes archive's MODIFIED
# matching ambiguous. It is the quiet one, so it is checked explicitly.
R="$(raiz repetido)"
cat >> "$R/openspec/specs/muestra/spec.md" <<'MD'

### Requirement: The sample holds

The system SHALL hold the sample a second time.

#### Scenario: Held again
- **Status:** PENDING
- **Reason:** it does not exist yet
- **WHEN** taken again
- **THEN** held again
MD
caso "a repeated requirement title in one file" "$R" "repeated requirement title"

R="$(raiz sinconsecuencia)"; python3 - "$R/openspec/specs/muestra/spec.md" <<'PY'
import sys
p = sys.argv[1]
t = open(p).read()
open(p, "w").write(t.split("#### Scenario:")[0])
PY
caso "a requirement with no consequence at all" "$R" "muestra :: The sample holds"

# ── controls ───────────────────────────────────────────────────────────────────────────────────
R="$(raiz sana)"
if TRAZA_RAIZ="$R" bash "$GUARDIAN" >/dev/null 2>&1; then
  echo "  ✓ a healthy corpus is GREEN (the guardian is not hardwired to red)"; ok=$((ok+1))
else
  echo "  ✗ a healthy corpus went RED — every case above is worthless"; mal=$((mal+1))
fi

# The backlog proportion is MEASURED and NOT GATED. A corpus that is entirely backlog is a fact
# about the corpus, not a failure of this guardian — the threshold, if there is to be one, belongs
# to the management system and not to this repository.
R="$(raiz todopendiente)"
sed -i 's/\*\*Status:\*\* CURRENT/**Status:** PENDING/; s#- \*\*Proof:\*\* .*#- **Reason:** it does not exist yet#' "$R/openspec/specs/muestra/spec.md"
salida="$(TRAZA_RAIZ="$R" bash "$GUARDIAN" 2>&1)"; rc=$?
if [ "$rc" -eq 0 ] && printf '%s' "$salida" | grep -qF "backlog: 100%"; then
  echo "  ✓ a corpus that is 100% backlog is MEASURED and not gated"; ok=$((ok+1))
else
  echo "  ✗ a fully-backlog corpus should exit 0 while reporting 100%; exit=$rc"
  printf '%s\n' "$salida" | head -4; mal=$((mal+1))
fi

echo
if [ "$mal" -gt 0 ]; then
  echo "::error title=trazabilidad.test::$mal of $((ok+mal)) contracts unmet"
  exit 1
fi
echo "trazabilidad.sh knows how to go red: $ok/$ok contracts, each for its named reason."
