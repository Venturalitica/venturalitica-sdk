# How work is done in this repository

> **Normative, not a manual.** This file exists so the design-and-development method is documented
> **in the repository where it is applied** and reconstructible at any commit (ISO 9001 §7.5.3).
> Until now it was not: the method lived in an external plugin whose version left no trace in the
> history, so "which process produced this record?" had no checkable answer.

## Method

`brainstorming → design spec → plan → implementation → PR`

## Spec anatomy — six sections, all required

```
§0 Motivation          §3 Phases
§1 Dated decisions     §4 Boundary
§2 Design              §5 Acceptance criteria
```

**§5 is written as an INVARIANT**, because that is the nature of this component: *given these
inputs, the emitted measurement / OSCAL assessment is exactly X*. It is proved with a frozen corpus
or a known-answer test — never by walking a UI. A change without §5 is not ready to implement.

## A change enters through an issue with three fields

`component` · `origin` · **`closing criterion`**

And the rule that holds it up: **the issue is not closed by whoever implements it, but by whoever
asked for it**, against a check of their own. Otherwise the interface between repositories carries
promises instead of facts.

## Hard rules

| Rule | Why |
|---|---|
| **This repository is PUBLIC** | Apache-2.0, published to PyPI, with an external community. What is written here is a public statement — and what is promised here is a product requirement (ISO 9001 §8.2) |
| **Never name a customer** | not even indirectly. Customer identities live in a restricted register, never in this repository |
| **The OSCAL contract is normative** | it is cited from the public README as *the normative OSCAL contract*. A normative reference that does not resolve is a defect, not a typo — `docs/contracts/oscal-assessment-plan-v1.md` is currently **missing** |
| **Dependencies through `uv`** | the lockfile is part of the evidence, not a build artefact |
| **Version numbers are load-bearing** | this package is installed by third parties. A version that disagrees with its own release notes is a defect |

## What is not asserted without measuring it

> **Nothing measurable is asserted from memory.** A hand-written census stops being true; a cleanup
> is not a control; a guard nobody has seen fail is not proven.

`not measured` is not the same as `fine`. Say which one it is.
