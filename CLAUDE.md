# CLAUDE.md

You are working in a repository cloned from **constraint-base**. This file is the entry
point. Read it fully before doing anything else.

This repo carries a constraint system: a small set of files defining the boundaries the
work must stay inside, and the finish line it is working toward. It exists so an agent can
run for a long time on a large task without drifting.

## The one rule that governs everything here

**Constraints and goals describe outcomes and rules. They never describe how to build
anything.**

Architecture, file layout, libraries, patterns, and sequencing are entirely your judgment.
The constraint system defines the boundaries and the finish line, and nothing else. If you
find yourself writing "use X" or "put Y in Z" into a constraint or a goal criterion, stop
and read `docs/outcome-vs-implementation.md`.

This cuts both ways: do not let a constraint tell you how to build, and do not write one
that does.

## Orient yourself first

Run this before anything else. It prints the active constraints, the goal condition, and
recent progress:

```
python3 tools/brief.py
```

Then pick the situation you are in.

### Situation 1 — intake has not run yet

You will see placeholders in the brief, and `goals/goal-condition.md` will say
`state: draft` with a placeholder criterion.

Run intake with Clara. Read `docs/intake.md` and follow it. It is a conversation: you ask,
she answers, you draft, she approves. Do not write files until the end. Do not start
building. Do not skip to the goal condition — the outcomes have to come first or the goal
condition will be guesswork.

Intake ends when the goal condition is approved and `python3 tools/validate.py` passes.

### Situation 2 — goal condition is approved, work is in progress

You are in goal mode. Work toward the goal condition, inside the constraints, using your
own judgment about everything else.

While working:

- **Re-ground periodically.** Every so often — after finishing a meaningful chunk, before
  a decision that would be expensive to reverse, whenever you notice you have been going
  a while — run `python3 tools/brief.py` again and read it. Check what you are about to
  do against the constraints, and check whether the goal condition is closer or whether
  you have wandered off it.
- **Check criteria honestly.** A criterion moves to `met` only after you have actually
  run its `check:` and seen the result. Record what you ran and what it showed in
  `evidence:`. Never mark something met because you believe it works.
- **Log at every natural break.** Append to `progress/log.md` in the format at the top of
  that file. Write for a session that has no memory of this one.
- **When you hit outcome-changing ambiguity, ask Clara** (constraint C-SURFACE-AMBIGUITY).
  Decisions that only affect how the work gets done are yours to make — make them and
  note them in the log.

Stop when every criterion is `met` with real evidence. Then say so and stop — do not keep
improving past the finish line. `goals/goal-condition.md` has an "out of scope for done"
section; respect it.

### Situation 3 — Clara wants to change the constraints or the goal

Edit the files, then run `python3 tools/validate.py`, then log the change in
`progress/log.md` with her reason. A goal condition that moves without a record is worse
than no goal condition. If the criteria changed materially, ask her to re-approve.

## The files

| File | What it holds |
|---|---|
| `constraints/defaults.md` | Rules inherited by every project. Waive, never delete. |
| `constraints/project.md` | Rules specific to this project. Written at intake. |
| `goals/outcomes.md` | The problem, who it is for, what becomes true, what is out of scope. |
| `goals/goal-condition.md` | The finish line: criteria, checks, evidence, approval state. |
| `progress/log.md` | Append-only session record so a fresh session can resume. |
| `docs/outcome-vs-implementation.md` | How to tell an outcome from a smuggled implementation detail. |
| `docs/intake.md` | How to run intake. |
| `docs/goal-conditions.md` | How to write a goal condition that can actually be checked. |
| `tools/brief.py` | Prints constraints + goal + recent progress. Your re-grounding call. |
| `tools/validate.py` | Checks the above are well-formed and outcome-shaped. |

Everything is plain Markdown. Clara edits it by hand whenever she likes. Nothing here
generates anything; there is no state outside these files.

## Defaults you inherit

Seven rules, active unless waived in `constraints/defaults.md`. Read them there — the
short version:

- **C-LOCAL** — development stays local: no deploying, publishing, provisioning hosted
  infrastructure, or pushing to production unless Clara says so explicitly this session
- **C-BLAST-RADIUS** — changes stay inside the project directory
- **C-NO-SILENT-DESTRUCTION** — no irreversible destruction of work you did not create
- **C-SECRETS** — no credentials in tracked files
- **C-EVIDENCE** — no completion claim without a check you actually ran
- **C-RESUMABLE** — a fresh session can resume from the repo alone
- **C-SURFACE-AMBIGUITY** — outcome-changing ambiguity goes to Clara

C-LOCAL is the one most likely to come up mid-run. "It would be useful to deploy this to
test it" is not an exception to it. Ask.

## Optional shortcuts

`commands/` holds three slash commands — `intake`, `reground`, `goal-check` — that wrap
the three things above. They are live only if they have been copied into `.claude/commands/`:

```
mkdir -p .claude/commands && cp commands/*.md .claude/commands/
```

They are conveniences. Everything works without them, from this file alone.

## Note on this file

Once the project is underway you may want project-specific notes for yourself here.
Add them below this line, and keep them separate from the constraint system: notes here
are guidance, and guidance is not binding. Only `constraints/` binds.
