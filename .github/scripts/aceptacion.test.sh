#!/usr/bin/env bash
# Falsifier for `aceptacion.sh`. Same discipline as the other three: every case fixes what it
# believes it is provoking, moves nothing else, and requires the expected REASON, because a red
# from the wrong assertion reads exactly like a good one.
#
# THE CASE THAT MUST NOT BE MISSING is the third check, the only one that can go green by
# accident: whoever closed the event is whoever authored the claim. Checks 1, 2 and 4 fail on
# their own when they fail — an unresolvable pointer, an open event, a date out of order all
# announce themselves. Self-certification announces nothing: it looks exactly like an acceptance.
# So it is falsified here, and with its contrast, because a detector that fires on every pointer
# detects nothing either.
#
# DECLARED LIMIT: the event and author resolvers are STUBBED here. These cases exercise the
# guardian's comparison logic, which is what it owns; they do not exercise the `gh` calls, which
# belong to a third party and need the network. No consequence in this corpus carries a pointer
# yet, so the `gh` path has never run against a real event. The first real pointer will exercise
# it for the first time, and that is stated rather than implied.
set -uo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUARDIAN="$AQUI/aceptacion.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export GITHUB_STEP_SUMMARY=/dev/null
ok=0; mal=0

# A committed root: `git blame` needs the claim to be in a commit, which is the point.
#
# It sets a global instead of echoing its path, and that is not style. A builder used as
# `raiz ...; R="$RAIZ_OUT"` runs in a SUBSHELL, so an `exit 1` inside it kills only the subshell and the
# caller carries on with a broken fixture. That is how this file spent several runs reporting
# «went red for the wrong reason» when the real story was a fixture with no commit in it — a
# falsifier manufacturing the very defect it exists to detect.
RAIZ_OUT=""
raiz() {  # $1 nombre, $2 linea de aceptacion (vacia = sin campo), $3 autor del commit
  local R="$TMP/$1" quien="${3:-implementador}" err
  rm -rf "$R"; mkdir -p "$R/openspec/specs/muestra" "$R/tests"
  printf 'def test_x():\n    assert True\n' > "$R/tests/test_muestra.py"
  {
    echo '# muestra'; echo
    echo '## Purpose'; echo
    echo 'A sample capability used only by the falsifier, long enough to satisfy the minimum.'; echo
    echo '## Requirements'; echo
    echo '### Requirement: The sample holds'; echo
    echo 'The system SHALL hold the sample.'; echo
    echo '#### Scenario: The sample is held'
    echo '- **Status:** CURRENT'
    echo '- **Proof:** `tests/test_muestra.py::test_x`'
    [ -n "$2" ] && echo "$2"
    echo '- **WHEN** taken'
    echo '- **THEN** held'
  } > "$R/openspec/specs/muestra/spec.md"

  err="$TMP/git.err"
  git -C "$R" init -q . 2>"$err" \
    && git -C "$R" -c user.email="$quien@example.invalid" -c user.name="$quien" \
           -c commit.gpgsign=false -c gpg.format=openpgp add -A 2>>"$err" \
    && git -C "$R" -c user.email="$quien@example.invalid" -c user.name="$quien" \
           -c commit.gpgsign=false -c gpg.format=openpgp commit -qm "claim" >/dev/null 2>>"$err"

  # The builder verifies its OWN postcondition and says what git said. Without this a silent
  # commit failure makes every case built on the fixture report «not committed yet», regardless
  # of what it was testing.
  if ! git -C "$R" rev-parse HEAD >/dev/null 2>&1; then
    echo "::error title=aceptacion.test::fixture '$1' has no commit, so every assertion built on"
    echo "  it would report «not committed yet» whatever it was testing. git said:"
    sed 's/^/    /' "$err"
    exit 1
  fi
  RAIZ_OUT="$R"
}

stub_evento() {  # $1 destino, $2 state, $3 closer, $4 closed_at
  printf '#!/usr/bin/env bash\nprintf "%%s\\n%%s\\n%%s\\n" "%s" "%s" "%s"\n' "$2" "$3" "$4" > "$1"
  chmod +x "$1"
}
stub_autor() {  # $1 destino, $2 login
  printf '#!/usr/bin/env bash\necho "%s"\n' "$2" > "$1"
  chmod +x "$1"
}
stub_roto() { printf '#!/usr/bin/env bash\nexit 3\n' > "$1"; chmod +x "$1"; }

caso() {  # $1 nombre, $2 raiz, $3 motivo, resto: entorno extra
  local nombre="$1" R="$2" motivo="$3"; shift 3
  local salida rc
  salida="$(ACEPTACION_RAIZ="$R" "$@" bash "$GUARDIAN" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "  ✗ $nombre — stayed GREEN; should have gone red for: $motivo"; mal=$((mal+1)); return
  fi
  if ! printf '%s' "$salida" | grep -qF -- "$motivo"; then
    echo "  ✗ $nombre — went red, but NOT for the expected reason."
    echo "      expected: $motivo"
    echo "      said:     $(printf '%s' "$salida" | head -3 | tr '\n' ' ')"
    mal=$((mal+1)); return
  fi
  echo "  ✓ $nombre"; ok=$((ok+1))
}

echo "falsifier for aceptacion.sh"

PTR='- **Accepted:** `example/repo#1`'

# ── THE ONE WITH TEETH, and its contrast ───────────────────────────────────────────────────────
raiz autocert "$PTR" ana; R="$RAIZ_OUT"
stub_evento "$R/ev" closed ana 2030-01-01T00:00:00Z; stub_autor "$R/au" ana
caso "the closer is the claim's own author" "$R" "both authored the claim and closed" \
  env ACEPTACION_RESOLUTOR="$R/ev" ACEPTACION_AUTOR="$R/au"

raiz otrapersona "$PTR" ana; R="$RAIZ_OUT"
stub_evento "$R/ev" closed beltza 2030-01-01T00:00:00Z; stub_autor "$R/au" ana
if ACEPTACION_RAIZ="$R" ACEPTACION_RESOLUTOR="$R/ev" ACEPTACION_AUTOR="$R/au" \
   bash "$GUARDIAN" >/dev/null 2>&1; then
  echo "  ✓ a different person closing it IS accepted (the detector is not always-on)"; ok=$((ok+1))
else
  echo "  ✗ a different closer must be accepted, or the check detects nothing"; mal=$((mal+1))
fi

# ── the three that announce themselves ─────────────────────────────────────────────────────────
raiz abierta "$PTR" ana; R="$RAIZ_OUT"
stub_evento "$R/ev" open beltza 2030-01-01T00:00:00Z; stub_autor "$R/au" ana
caso "a pointer to an event that is still open" "$R" "is \`open\`, not closed" \
  env ACEPTACION_RESOLUTOR="$R/ev" ACEPTACION_AUTOR="$R/au"

raiz irresoluble "$PTR" ana; R="$RAIZ_OUT"
stub_roto "$R/ev"; stub_autor "$R/au" ana
caso "a pointer that cannot be resolved fails, it does not certify" "$R" "could not be resolved" \
  env ACEPTACION_RESOLUTOR="$R/ev" ACEPTACION_AUTOR="$R/au"

raiz antesdetiempo "$PTR" ana; R="$RAIZ_OUT"
stub_evento "$R/ev" closed beltza 2001-01-01T00:00:00Z; stub_autor "$R/au" ana
caso "an acceptance dated before the claim it accepts" "$R" "BEFORE the claim it accepts" \
  env ACEPTACION_RESOLUTOR="$R/ev" ACEPTACION_AUTOR="$R/au"

# ── the claim has to be committed for there to be an author at all ─────────────────────────────
# The first attempt at this case provoked the wrong thing: the file was un-staged but the claim
# line was still in HEAD, so blame resolved it and the guardian was right to stay green. What has
# to be uncommitted is the CLAIM, so the fixture keeps the whole tree out of any commit.
raiz sincommit "$PTR" ana; R="$RAIZ_OUT"; rm -rf "$R/.git"; git -C "$R" init -q .
stub_evento "$R/ev" closed beltza 2030-01-01T00:00:00Z; stub_autor "$R/au" ana
caso "an acceptance of a claim that is not committed yet" "$R" "not committed yet" \
  env ACEPTACION_RESOLUTOR="$R/ev" ACEPTACION_AUTOR="$R/au"

# ── THE THREE DESTINATIONS STAY APART ──────────────────────────────────────────────────────────
# «nobody said anything» is not «somebody said no». If these two collapsed, the guardian would
# report a state nobody declared — the defect closed one floor down, rebuilt here.
raiz sinacampo "" ana; R="$RAIZ_OUT"
salida="$(ACEPTACION_RAIZ="$R" bash "$GUARDIAN" 2>&1)"
if printf '%s' "$salida" | grep -qE "unaccepted 0 · not declared 1"; then
  echo "  ✓ an absent field counts as NOT DECLARED, not as unaccepted"; ok=$((ok+1))
else
  echo "  ✗ an absent field must count as not declared"; printf '%s\n' "$salida" | grep accepted; mal=$((mal+1))
fi

raiz campovacio '- **Accepted:**' ana; R="$RAIZ_OUT"
salida="$(ACEPTACION_RAIZ="$R" bash "$GUARDIAN" 2>&1)"
if printf '%s' "$salida" | grep -qE "unaccepted 1 · not declared 0"; then
  echo "  ✓ a present but empty field counts as UNACCEPTED, not as undeclared"; ok=$((ok+1))
else
  echo "  ✗ a present empty field must count as unaccepted"; printf '%s\n' "$salida" | grep accepted; mal=$((mal+1))
fi

# ── both spellings, because a third one is how a dialect divergence starts ─────────────────────
raiz castellano '- **Aceptada:** `example/repo#1`' ana; R="$RAIZ_OUT"
stub_evento "$R/ev" closed beltza 2030-01-01T00:00:00Z; stub_autor "$R/au" ana
if ACEPTACION_RAIZ="$R" ACEPTACION_RESOLUTOR="$R/ev" ACEPTACION_AUTOR="$R/au" \
   bash "$GUARDIAN" 2>&1 | grep -qE "accepted 1 "; then
  echo "  ✓ the Spanish spelling of the field is read too"; ok=$((ok+1))
else
  echo "  ✗ both spellings must be read"; mal=$((mal+1))
fi

# ── and the corpus-empty trap, same as the other three guardians ───────────────────────────────
R="$TMP/sincorpus"; mkdir -p "$R/openspec/specs"
caso "an empty corpus is not a green" "$R" "no corpus to certify" env

echo
if [ "$mal" -gt 0 ]; then
  echo "::error title=aceptacion.test::$mal of $((ok+mal)) contracts unmet"
  exit 1
fi
echo "aceptacion.sh knows how to go red: $ok/$ok contracts, each for its named reason."
