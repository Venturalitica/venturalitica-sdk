#!/usr/bin/env bash
# Falsifier for `vigencia.sh`: proves the currency guardian goes RED, and FOR THE NAMED REASON.
#
# This is the falsifier that matters most, because `vigencia.sh` is the one guardian with no
# precedent to lean on. Its whole job is to stop a CURRENT from being backed by a test that never
# ran or that cannot fail — which is to say, to stop coverage being fabricated. A falsifier that
# certified that loosely would be the same defect one level up.
#
# Same discipline throughout: each case fixes what it believes it is provoking, moves nothing
# else, and requires the expected reason in the output. A red from the wrong assertion reads
# exactly like a good one.
set -uo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUARDIAN="$AQUI/vigencia.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export GITHUB_STEP_SUMMARY=/dev/null
ok=0; mal=0

# A root with two test functions — one that can fail, one that cannot — and a spec citing the
# first. The second is only cited by the cases that need it.
raiz() {
  local R="$TMP/$1"; rm -rf "$R"; mkdir -p "$R/openspec/specs/muestra" "$R/tests"
  cat > "$R/tests/test_muestra.py" <<'PY'
def test_que_puede_fallar():
    assert 1 == 1


def test_que_no_puede_fallar():
    """Runs always, asserts nothing. The subject family, in miniature."""
    resultado = 1 + 1
    print(resultado)


def test_parametrizado():
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
- **Proof:** `tests/test_muestra.py::test_que_puede_fallar`
- **WHEN** the sample is taken
- **THEN** it is held
MD
  echo "$R"
}

# $1 destino, resto: "nombre", "nombre:skip", o "nombre@modulo" para escribir otro `classname`.
# The module matters: the guardian indexes by (module, function), so a homonym in another file
# must not satisfy a citation.
junit() {
  local dest="$1"; shift
  { echo '<?xml version="1.0" encoding="utf-8"?>'
    echo '<testsuites><testsuite name="pytest">'
    for t in "$@"; do
      local clase="tests.test_muestra" n="$t"
      case "$n" in *@*) clase="${n##*@}"; n="${n%@*}";; esac
      if [ "${n##*:}" = "skip" ]; then
        printf '<testcase classname="%s" name="%s"><skipped message="x"/></testcase>\n' "$clase" "${n%:skip}"
      else
        printf '<testcase classname="%s" name="%s"/>\n' "$clase" "$n"
      fi
    done
    echo '</testsuite></testsuites>'
  } > "$dest"
}

caso() {  # $1 nombre, $2 raiz, $3 junit-path, $4 motivo
  local salida rc
  salida="$(VIGENCIA_RAIZ="$2" bash "$GUARDIAN" "$3" 2>&1)"; rc=$?
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

echo "falsifier for vigencia.sh"

# ── the evidence itself has to be there ────────────────────────────────────────────────────────
# A currency guardian that certifies nothing when the report is absent is the green that cannot
# tell «passed» from «was not asked». These three cases are the reason it fails instead.
R="$(raiz sinarg)"; junit "$R/j.xml" test_que_puede_fallar
salida="$(VIGENCIA_RAIZ="$R" bash "$GUARDIAN" 2>&1)"; rc=$?
if [ "$rc" -ne 0 ] && printf '%s' "$salida" | grep -qF "no JUnit report was given"; then
  echo "  ✓ no report given at all"; ok=$((ok+1))
else
  echo "  ✗ no report given at all — should fail, not certify"; mal=$((mal+1))
fi

R="$(raiz noexiste)"
caso "a report path that does not exist" "$R" "$R/no-esta.xml" "does not exist"

R="$(raiz noxml)"; echo 'esto no es xml <<<' > "$R/j.xml"
caso "a report that does not parse" "$R" "$R/j.xml" "does not parse"

R="$(raiz sincasos)"; junit "$R/j.xml"
caso "a report recording no executed test" "$R" "$R/j.xml" "records no executed test"

# ── the environment family ─────────────────────────────────────────────────────────────────────
# The measured defect of this tree: a module-level importorskip removes its tests during
# collection, so they never appear in the report at all — not even as a skip.
R="$(raiz norecolectado)"; junit "$R/j.xml" test_otra_cosa
caso "a CURRENT citing a test that never appears in the run" "$R" "$R/j.xml" "DOES NOT APPEAR in the run"

R="$(raiz saltado)"; junit "$R/j.xml" test_parametrizado test_que_puede_fallar:skip
caso "a CURRENT citing a test the run reports as skipped" "$R" "$R/j.xml" "SKIPPED"

# A HOMONYM IN ANOTHER FILE MUST NOT SATISFY THE CITATION. Matching on the bare function name
# would let `tests/a.py::test_x` having run stand in for a citation of `tests/b.py::test_x` that
# never ran — a false green on the exact question this guardian answers. Test names repeat across
# files often enough that this is not hypothetical.
R="$(raiz homonimo)"; junit "$R/j.xml" "test_que_puede_fallar@tests.test_otra_cosa"
caso "a homonym in another module does not satisfy the citation" "$R" "$R/j.xml" "DOES NOT APPEAR in the run"

# And its contrast: a test inside a CLASS is still reported under its own module, and has to keep
# satisfying the citation. A detector that fires on those would fire on most of this suite.
R="$(raiz enclase)"; junit "$R/j.xml" "test_que_puede_fallar@tests.test_muestra.TestAlgo"
if VIGENCIA_RAIZ="$R" bash "$GUARDIAN" "$R/j.xml" >/dev/null 2>&1; then
  echo "  ✓ a test reported under a class of the cited module still satisfies it"; ok=$((ok+1))
else
  echo "  ✗ a class-nested test must still satisfy a citation of its module"; mal=$((mal+1))
fi

# ── the subject family ─────────────────────────────────────────────────────────────────────────
# Runs always, cannot fail. This is the one `trazabilidad.sh` lets through, and the reason this
# guardian exists at all.
R="$(raiz sinasercion)"; sed -i 's/::test_que_puede_fallar/::test_que_no_puede_fallar/' "$R/openspec/specs/muestra/spec.md"
junit "$R/j.xml" test_que_no_puede_fallar
caso "a CURRENT citing a test that runs and cannot fail" "$R" "$R/j.xml" "NO ASSERTION"

R="$(raiz noresuelve)"; sed -i 's/::test_que_puede_fallar/::test_que_no_esta_definido/' "$R/openspec/specs/muestra/spec.md"
junit "$R/j.xml" test_que_no_esta_definido
caso "a CURRENT whose citation resolves to no function" "$R" "$R/j.xml" "cannot be parsed or does not"

R="$(raiz sincorpus)"; rm -rf "$R/openspec/specs/muestra"; junit "$R/j.xml" test_que_puede_fallar
caso "no corpus to certify" "$R" "$R/j.xml" "no corpus to certify"

# ── THE TWO FAMILIES ARE REPORTED APART AND NEVER SUMMED ───────────────────────────────────────
# The correction that is easiest to lose. If they were summed, installing the extras one day would
# look like it closed both — and the subject family is the one nothing but an assertion can close.
R="$(raiz dosfamilias)"
cat >> "$R/openspec/specs/muestra/spec.md" <<'MD'

### Requirement: The sample holds a second way

The system SHALL hold the sample a second way.

#### Scenario: Held by something that cannot fail
- **Status:** CURRENT
- **Proof:** `tests/test_muestra.py::test_que_no_puede_fallar`
- **WHEN** taken
- **THEN** held
MD
sed -i '0,/::test_que_puede_fallar/s//::test_nunca_recolectado/' "$R/openspec/specs/muestra/spec.md"
junit "$R/j.xml" test_que_no_puede_fallar
salida="$(VIGENCIA_RAIZ="$R" bash "$GUARDIAN" "$R/j.xml" 2>&1)"; rc=$?
if [ "$rc" -ne 0 ] \
   && printf '%s' "$salida" | grep -qE "environment gap .*: 1" \
   && printf '%s' "$salida" | grep -qE "subject gap .*: 1"; then
  echo "  ✓ the two families are counted APART (environment 1, subject 1), never summed"; ok=$((ok+1))
else
  echo "  ✗ the two families must be reported separately; exit=$rc"
  printf '%s\n' "$salida" | grep -E "gap|summed" | head -4; mal=$((mal+1))
fi

# ── controls ───────────────────────────────────────────────────────────────────────────────────
R="$(raiz sana)"; junit "$R/j.xml" test_que_puede_fallar
if VIGENCIA_RAIZ="$R" bash "$GUARDIAN" "$R/j.xml" >/dev/null 2>&1; then
  echo "  ✓ a healthy corpus is GREEN (the guardian is not hardwired to red)"; ok=$((ok+1))
else
  echo "  ✗ a healthy corpus went RED — every case above is worthless"; mal=$((mal+1))
fi

# pytest appends [id] to a parametrised case. The citation names the function, so the report's
# parametrised entries have to satisfy it — otherwise every parametrised test would read as
# never having run, which is a false red of exactly the kind this file is trying to avoid.
R="$(raiz parametrizado)"; sed -i 's/::test_que_puede_fallar/::test_parametrizado/' "$R/openspec/specs/muestra/spec.md"
junit "$R/j.xml" "test_parametrizado[caso-uno]" "test_parametrizado[caso-dos]"
if VIGENCIA_RAIZ="$R" bash "$GUARDIAN" "$R/j.xml" >/dev/null 2>&1; then
  echo "  ✓ a parametrised test satisfies a citation of its function name"; ok=$((ok+1))
else
  echo "  ✗ a parametrised test should satisfy a citation of its function name"; mal=$((mal+1))
fi

echo
if [ "$mal" -gt 0 ]; then
  echo "::error title=vigencia.test::$mal of $((ok+mal)) contracts unmet"
  exit 1
fi
echo "vigencia.sh knows how to go red: $ok/$ok contracts, each for its named reason."
