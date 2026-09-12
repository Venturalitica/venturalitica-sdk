# History rewrite, 2026-09-12

On 2026-09-12 the published history of this repository was rewritten and force-pushed, to remove
third-party identifiers that should never have been committed. This file exists because the
rewrite otherwise leaves no trace in the tree it was applied to, which is the defect
[`CLAUDE.md`](../../CLAUDE.md) opens by describing: a process whose record lives somewhere else
cannot answer *which process produced this record?* at any commit.

**The identifiers themselves are not reproduced here.** Naming them in the record of their removal
would defeat the removal. They were customer identities, which belong in a restricted register and
never in this repository.

**This rewrite did not close the exposure.** It reduced the surface from the day it was pushed.
The residue below is declared, not incidental, and the exposure is closed when GitHub Support
confirms the purge described at the end — not before.

## What was rewritten

`git filter-repo`, over every branch and tag, replacing the identifiers in commit messages and in
file contents. The current tree had already been redacted by hand in `#17`, so the rewrite changed
**no file at `HEAD`**: 328 files, byte for byte identical before and after. It touched history
only.

| ref | before | after |
|---|---|---|
| `main` | `b231d42` | `29978ce` |
| `staging` | `43b4183` | `b672f79` |
| `v0.6.1` | `e623d84` | `f613a10` |
| `v0.6.2` | `4addb9a` | `cca3d0a` |
| `v0.6.10` | `2983e21` | `3e7ce32` |
| `v0.3.0` | unchanged | its history predates the affected commits |
| `gh-pages` | moved afterwards by a docs deploy, **not** by the rewrite | |

Verified after the push, against a fresh mirror of the remote: zero occurrences in the content of
any branch or tag, zero in any reachable commit message, `git fsck` clean, and the same commit
count as before. The four release tags have **identical trees** — only their commit identifiers
changed — so a published artefact still corresponds to what its tag contains.

## What it did not close

**`refs/pull/*`.** GitHub keeps the head of every pull request in refs that reject writes. Those
refs still resolve to pre-rewrite commits, so the old objects remain reachable by identifier to
anyone who has or guesses one. A repository owner cannot fix this; only GitHub Support can. The
count was **17 at the time of writing, and it moves**: each open pull request adds two and each
merge removes its own, so the number is only meaningful with its date.

**PyPI.** Four published versions — 0.6.13, 0.8.0, 0.8.1 and 0.8.2 — carry an identifier inside
two files of the source distribution. Verified by downloading them. A PyPI release can be yanked
but never edited, and anything already fetched cannot be recalled.

**The edit history of issues.** Five issues and pull requests were edited to remove the identifier.
GitHub keeps the previous version visible in the edit history to anyone who can see the item.

**Existing clones and forks.** Out of reach by construction.

## The second-order effect nobody predicted

The force-push to `staging` fired a `push` event, and **`staging` was three months stale**, so the
workflow definition it carries is the retired one that published *by branch* rather than on manual
dispatch. That old definition ran: `build` succeeded, `publish-testpypi` failed, and
`publish-pypi` was skipped.

The real index was never reached, and it is worth being precise about why: `publish-pypi` is gated
on `github.ref == 'refs/heads/main'`, and `main` carries the current workflow, which only runs on
manual dispatch. So the protection held because of which file governs which branch, **not because
anything checked that a force-push should not publish**.

Two things follow, and the second is the one that matters:

- Pushing to a stale branch runs the workflows *that branch* carries, not the ones the default
  branch carries. A rewrite that touches every ref therefore re-runs retired automation.
- **`staging` still carries that definition.** Any future push to it attempts a publish again.
  Bringing the branch up to date, or retiring it, closes that; leaving it is a live defect.

## What remains to be done

A ticket to GitHub Support asking whether `refs/pull/*` can be removed or re-pointed, whether the
unreachable objects can be garbage-collected, and — the question we cannot answer ourselves — in
what order they recommend it. It deliberately does not contain the identifiers, and deliberately
does not bundle the PyPI and edit-history questions, so that the part they can act on is not
delayed by the parts they cannot.

The order was decided the other way round: rewrite first, ticket second. The trade was recorded
at the time. Reducing the surface from today rather than from whenever Support replies is a
legitimate reason, and the cost if Support declines is that the rewrite bought a partial result.
