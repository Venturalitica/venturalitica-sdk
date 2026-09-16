#!/usr/bin/env bash
# Guardian of ACCEPTANCE: the semantic half — that the named test is about the right subject — was
# closed by someone other than whoever implemented it.
#
# This is the half no other guardian reaches, and it is the one CLAUDE.md already names:
#
#     «the issue is not closed by whoever implements it, but by whoever asked for it,
#      against a check of their own»
#
# WHY THE ACCEPTANCE IS NOT A FIELD. The obvious design is a fourth bullet beside `Status` and
# `Proof` saying who accepted. It certifies nothing: whoever writes the spec is normally whoever
# implements, so that bullet lands in the SAME COMMIT as the claim it accepts. Self-certification
# with an extra line is worse than no line, because it reads as closed.
#
#     The acceptance is an EVENT the implementer cannot author alone.
#     The field in the corpus is only a POINTER to that event.
#
# FOUR CHECKS, and only the third has teeth:
#
#   1. the pointer RESOLVES — it is not a promise;
#   2. the event is CLOSED;
#   3. whoever closed it is NOT whoever authored the commit that introduced the claim;  ← teeth
#   4. the closure is LATER than that commit — an acceptance predating what it accepts is not one.
#
# Checks 1, 2 and 4 fail on their own when they fail. Check 3 is the one that can go green by
# accident, so its falsifier is mandatory and exists.
#
# THREE DESTINATIONS, never two:
#
#   ACCEPTED       the pointer is there and the four checks hold.
#   UNACCEPTED     the field is present and carries no pointer. A declared, counted gap.
#   NOT DECLARED   the field is absent. Nobody said anything, which is not the same as saying no.
#
# If the last two read alike, the defect that was closed one floor down gets rebuilt here: a
# counter that maps «nothing said» onto «said no» reports a state nobody declared.
#
# WHAT THIS GUARDIAN DOES NOT ESTABLISH: that the check the accepter performed was any good. It
# gives the slot a floor, never a ceiling. Someone other than the author looked and said yes; what
# they looked at is not mechanisable and is not pretended to be.
#
# POINTER FORMAT: `owner/repo#N`, fully qualified. A bare `#N` resolves only for a reader who
# already knows which repository they are in, and this repository is public: a reference that does
# not resolve from outside is a defect rather than a shorthand. Both `**Accepted:**` and
# `**Aceptada:**` are read, because the method's counter reads both and a third spelling is how a
# dialect divergence starts.
#
# Input: none. Runs from the repository root.
#   ACEPTACION_RAIZ       root to inspect (default: cwd) — for the falsifier only
#   ACEPTACION_RESOLUTOR  event resolver (default: the `gh` one below) — for the falsifier only.
#                         Called as `RESOLVER owner/repo N` and must print three lines:
#                         state, closer login, closure date (ISO 8601).
#   ACEPTACION_AUTOR      commit-author resolver, called as `RESOLVER sha` printing the login.
# Output: `::error` annotations plus a summary. 0 green, 1 red.
set -uo pipefail

RAIZ="${ACEPTACION_RAIZ:-$PWD}"
SUMMARY="${GITHUB_STEP_SUMMARY:-/dev/null}"
export LC_ALL=C

rojo() {
  local titulo="$1"; shift
  echo "::error title=aceptacion::$titulo"
  printf '%s\n' "$@"
  { echo "**RED — $titulo**"; echo; printf '%s\n' "$@"; } >> "$SUMMARY"
  exit 1
}

cd "$RAIZ" || rojo "cannot enter $RAIZ"
command -v python3 >/dev/null 2>&1 || rojo "python3 is missing"

# ── The census: which consequences declare what ────────────────────────────────────────────────
CENSO="$(python3 - "$RAIZ" <<'PY'
import os, re, sys

raiz = sys.argv[1]
RE_REQ = re.compile(r"^### Requirement:\s*(.+?)\s*$", re.M)
RE_ESC = re.compile(r"^#### Scenario:\s*(.+?)\s*$", re.M)
RE_EST = re.compile(r"\*\*Status:\*\*\s*([A-Z ]+?)(?:\s|$)", re.M)
# Both spellings, deliberately. A third one is how a dialect divergence starts.
RE_ACE = re.compile(r"^\s*-\s*\*\*(?:Accepted|Aceptada):\*\*(.*)$", re.M)
RE_PTR = re.compile(r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#(\d+)")
RE_PRU = re.compile(r"^\s*-\s*\*\*Proof:\*\*", re.M)

specs = []
base = os.path.join(raiz, "openspec", "specs")
for d in sorted(os.listdir(base)) if os.path.isdir(base) else []:
    f = os.path.join(base, d, "spec.md")
    if os.path.isfile(f):
        specs.append(f)

if not specs:
    print("SINCORPUS"); raise SystemExit(0)

def trozos(texto, regex):
    ms = list(regex.finditer(texto))
    for i, m in enumerate(ms):
        fin = ms[i + 1].start() if i + 1 < len(ms) else len(texto)
        yield m.group(1), texto[m.end():fin], m.end()

filas = []
for f in specs:
    rel = os.path.relpath(f, raiz)
    cap = os.path.basename(os.path.dirname(f))
    texto = open(f, encoding="utf-8").read()
    for titulo, cuerpo, _ in trozos(texto, RE_REQ):
        for nombre, bloque, desplazamiento in trozos(cuerpo, RE_ESC):
            if "CURRENT" not in [e.strip() for e in RE_EST.findall(bloque)]:
                continue  # only a CURRENT asserts something a test is claimed to prove
            donde = "%s :: %s" % (cap, nombre)
            ace = RE_ACE.search(bloque)
            if not ace:
                filas.append(("NODECLARADA", donde, rel, "0", "", ""))
                continue
            ptr = RE_PTR.search(ace.group(1))
            if not ptr:
                filas.append(("SINACEPTAR", donde, rel, "0", "", ""))
                continue
            # Line of the **Proof:** bullet — the claim being accepted — so `git blame` points at
            # the commit that introduced it rather than at the acceptance bullet itself.
            prueba = RE_PRU.search(bloque)
            base_off = texto.find(bloque)
            linea = texto.count("\n", 0, base_off + (prueba.start() if prueba else 0)) + 1
            filas.append(("APUNTA", donde, rel, str(linea), ptr.group(1), ptr.group(2)))

print("OK")
for fila in filas:
    print("\t".join(fila))
PY
)"

[ "$(printf '%s' "$CENSO" | sed -n 1p)" = "OK" ] || rojo "there is no corpus to certify" \
  "Same trap as the other guardians: nothing is not a green."

# ── Resolvers. Injectable so the falsifier can exercise the comparison without the network ─────
resolver_evento() {  # owner/repo  numero -> state \n closer \n closed_at
  if [ -n "${ACEPTACION_RESOLUTOR:-}" ]; then "$ACEPTACION_RESOLUTOR" "$1" "$2"; return; fi
  command -v gh >/dev/null 2>&1 || return 3
  gh api "repos/$1/issues/$2" \
    --jq '(.state // "?"), (.closed_by.login // "?"), (.closed_at // "?")' 2>/dev/null || return 3
}
resolver_autor() {  # sha -> login
  if [ -n "${ACEPTACION_AUTOR:-}" ]; then "$ACEPTACION_AUTOR" "$1"; return; fi
  command -v gh >/dev/null 2>&1 || return 3
  gh api "repos/$2/commits/$1" --jq '.author.login // "?"' 2>/dev/null || return 3
}

aceptadas=0; sinaceptar=0; nodeclaradas=0; fallos=()
# The breakdown behind the total, for the same reason the trace guardian carries one: a number has
# nowhere to put a footnote. «unaccepted 87» read alone cannot distinguish a consequence that was
# retired from one that was accepted, and both move it the same way.
declare -A CAP_ACE CAP_SIN CAP_NOD

while IFS=$'\t' read -r clase donde fichero linea repo numero; do
  [ -n "$clase" ] || continue
  cap="${donde%% ::*}"
  case "$clase" in
    NODECLARADA) nodeclaradas=$((nodeclaradas + 1)); CAP_NOD[$cap]=$(( ${CAP_NOD[$cap]:-0} + 1 )); continue ;;
    SINACEPTAR)  sinaceptar=$((sinaceptar + 1));  CAP_SIN[$cap]=$(( ${CAP_SIN[$cap]:-0} + 1 )); continue ;;
  esac

  # 1. the pointer resolves
  if ! datos="$(resolver_evento "$repo" "$numero")"; then
    fallos+=("$donde → the pointer \`$repo#$numero\` could not be resolved.
      This guardian FAILS rather than certifying an unverified acceptance: a green that cannot
      tell «accepted» from «could not ask» is the defect it exists to answer.")
    continue
  fi
  estado="$(printf '%s' "$datos" | sed -n 1p)"
  cerrador="$(printf '%s' "$datos" | sed -n 2p)"
  cierre="$(printf '%s' "$datos" | sed -n 3p)"

  # 2. the event is closed
  if [ "$estado" != "closed" ]; then
    fallos+=("$donde → \`$repo#$numero\` is \`$estado\`, not closed. An open event is a request, not an acceptance.")
    continue
  fi

  # the commit that introduced the claim
  # blame's stderr is kept and reported. Collapsing every blame failure into «not committed yet»
  # would be a misleading red of exactly the kind these guardians exist to avoid: the reason read
  # would not be the reason that happened.
  blame_err="$(mktemp)"
  sha="$(git -C "$RAIZ" blame -L "$linea,$linea" --porcelain -- "$fichero" 2>"$blame_err" | head -1 | cut -d' ' -f1)"
  motivo_blame="$(cat "$blame_err")"; rm -f "$blame_err"
  if [ -z "$sha" ]; then
    # «no such ref: HEAD» and «no such path» both mean the claim is not in any commit, which is a
    # real answer. Anything else is a failure of the tool and is reported verbatim rather than
    # dressed up as that answer.
    case "$motivo_blame" in
      *"no such ref"*|*"no such path"*|*"has only"*)
        fallos+=("$donde → the claim's line is not committed yet, so there is no author to compare
      the closer against. An acceptance cannot be verified against an uncommitted claim.") ;;
      *)
        fallos+=("$donde → could not attribute the claim's line ($fichero:$linea).
      git blame said: ${motivo_blame:-nothing}") ;;
    esac
    continue
  fi
  # The all-zeros SHA is blame's marker for a line that is not in any commit. Testing only the
  # FIRST character for '0' was a real defect here: roughly one commit in sixteen has a hash
  # starting with zero, and those were reported as uncommitted. It made the falsifier fail about
  # six runs in twenty-five, always with a reason that read plausible and was wrong — the exact
  # failure mode these guardians are built to refuse. A sha is the marker only if it is ALL zeros.
  if ! printf '%s' "$sha" | grep -q '[^0]'; then
    fallos+=("$donde → the claim's line is not committed yet, so there is no author to compare the
      closer against. An acceptance cannot be verified against an uncommitted claim.")
    continue
  fi
  if ! autor="$(resolver_autor "$sha" "$repo")"; then
    fallos+=("$donde → could not resolve the author of \`$sha\`.")
    continue
  fi

  # 3. the one with teeth
  if [ "$autor" = "$cerrador" ]; then
    fallos+=("$donde → \`$cerrador\` both authored the claim and closed \`$repo#$numero\`.
      This is self-certification with a pointer, which reads as closed and certifies nothing.
      The issue is not closed by whoever implements it, but by whoever asked for it.")
    continue
  fi

  # 4. the acceptance came after what it accepts
  fecha_commit="$(git -C "$RAIZ" show -s --format=%cI "$sha" 2>/dev/null)"
  if [ -n "$fecha_commit" ] && [ -n "$cierre" ] && [ "$cierre" != "?" ] \
     && [ "$(printf '%s\n%s\n' "$cierre" "$fecha_commit" | sort | head -1)" = "$cierre" ] \
     && [ "$cierre" != "$fecha_commit" ]; then
    fallos+=("$donde → \`$repo#$numero\` was closed at $cierre, BEFORE the claim it accepts was
      committed at $fecha_commit. An acceptance that predates its claim accepted something else.")
    continue
  fi
  aceptadas=$((aceptadas + 1)); CAP_ACE[$cap]=$(( ${CAP_ACE[$cap]:-0} + 1 ))
done <<< "$(printf '%s' "$CENSO" | sed -n '2,$p')"

if [ "${#fallos[@]}" -gt 0 ]; then
  rojo "${#fallos[@]} declared acceptance(s) do not hold" "${fallos[@]}"
fi

total=$((aceptadas + sinaceptar + nodeclaradas))
MSG="GREEN — and only for what it covers: every DECLARED acceptance resolves to a closed event
closed by someone other than the claim's author, after the claim was committed.
  accepted ${aceptadas} · unaccepted ${sinaceptar} · not declared ${nodeclaradas} · current ${total}
                     accepted · unaccepted · not declared
$(for c in $(printf '%s\n' "${!CAP_ACE[@]}" "${!CAP_SIN[@]}" "${!CAP_NOD[@]}" | sort -u); do
    printf '  %-18s %3d · %3d · %3d\n' "$c" "${CAP_ACE[$c]:-0}" "${CAP_SIN[$c]:-0}" "${CAP_NOD[$c]:-0}"
  done)
The last two are counted apart on purpose: «nobody said anything» is not «somebody said no».
This gate does NOT require an acceptance to exist — that threshold belongs to the management
system, not to this repository — and it says NOTHING about whether the check the accepter made was
any good. It gives the semantic half a floor, never a ceiling."
echo "$MSG"
{ echo "**aceptacion — $MSG**"; } >> "$SUMMARY"
exit 0
