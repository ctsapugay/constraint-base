# Blockers

A running ledger of what is currently stuck. Working state, not governed — edit it freely.

This is how a long run avoids stalling: when a front is blocked, log it here and move to
another unblocked front instead of stopping. Surface open blockers to Clara **together**
once every front is blocked (see `CLAUDE.md`, "Staying on task across a long run").

An outcome-changing ambiguity is a blocker like any other — it is logged here and raised
with Clara, **never resolved by assumption** (constraint C-SURFACE-AMBIGUITY). Batching
only changes when you ask, not whether.

`python3 tools/brief.py` prints the open blockers (status not `resolved`) in its WORKING
STATE section on every re-grounding call.

**Entry format:**

```
## B1 — Short title
- **status:** open | resolved
- **front:** the area of the work this blocks
- **what:** what is stuck, and why
- **needs:** what would clear it — a decision from Clara, an external thing, ...
- **since:** YYYY-MM-DD
- **resolved:** only when resolved — YYYY-MM-DD and how it cleared
```

Ids are `B` plus a number. Keep a resolved entry in place (mark `status: resolved`) so the
history of what blocked the work survives.

<!-- Add blockers below this line. -->

_No blockers yet._
