# Goal condition

The finish line. An agent running in goal mode works until every criterion here is met,
then stops. Drafted at the end of intake, approved or edited by Clara.

A goal condition is a **checkable statement about the world**, not a description of the
work. "The project is done when X" where X is something a skeptical person could verify
without reading the source. See `docs/goal-conditions.md` before writing one.

**Entry format for criteria:**

```
## G1 — Short title
- **criterion:** What must be observably true.
- **check:** The specific thing someone runs, opens, or looks at to confirm it.
- **state:** unmet | met
- **evidence:** Empty until met. Then: what was run and what it showed, with a date.
```

---

## Status

- **state:** draft
- **approved:** _not yet approved by Clara_

## Statement

<!-- INTAKE: one or two sentences. The whole finish line in plain language. -->

_Not yet drafted._

## Criteria

<!-- INTAKE: replace with the real criteria. Aim for three to seven. -->

## G1 — Placeholder

- **criterion:** _Not yet drafted. Intake replaces this with what must be observably true._
- **check:** _Not yet drafted. Every criterion needs something specific to run or look at._
- **state:** unmet
- **evidence:**

## Completion gate

The task is complete only when **every criterion above is met with real evidence** and
**`python3 tools/verify.py` is green** — every check in `checks/registry.md` passing, or
waived with Clara's countersignature (`approve.py --waive-check`) — on the current code.
The individual checks are not listed here; they live in the registry so the finish line
stays readable however many there are. A criterion's `state:` is a claim recorded once;
the checks are re-run, so this gate is what proves the project still works at the end, not
just that it worked when a criterion was first ticked.

This clause is standing: it is the same for every project and is not the agent's to
soften. `tools/validate.py` enforces it — marking the goal `met` while the suite is red,
stale, or unrun is an error.

## Out of scope for "done"

<!-- INTAKE: things that will still be imperfect when the goal condition is met, and
     that is fine. Prevents an agent from working past the finish line. -->

- _..._
