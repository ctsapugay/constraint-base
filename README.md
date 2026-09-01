# constraint-base

A base repository for running an agent in goal mode on long-horizon projects without it
drifting.

Clone it, run intake, get a goal condition, then let an agent work.

## The idea

Give an agent a big task and enough time and it drifts: it optimizes something nobody
asked about, deploys something it shouldn't, declares victory on reasoning rather than
evidence, or quietly redefines what "done" meant. Not because it is careless — because
nothing in its context says where the edges are or where the finish line is.

This repo is that context, as a handful of plain Markdown files:

- **Constraints** — what must remain true throughout. A few inherited defaults every
  project gets, plus whatever this project needs.
- **Outcomes** — what becomes true when the project exists, and what is deliberately out
  of scope.
- **A goal condition** — the finish line, written precisely enough that an agent can
  check it itself and be right.
- **A progress log** — append-only, so a session with no memory of the last one can pick
  up where it left off.

## The one rule

**Constraints and goals describe outcomes and rules. They never describe how to build
anything.**

No prescribed architectures, file layouts, libraries, or patterns. The agent has full
freedom of judgment over implementation; the constraint system only defines the boundaries
and the finish line.

The difference in one line:

> "Use PostgreSQL." → *implementation*
> "Data survives the process being killed and is readable by the next run." → *outcome*

The first goes stale and blocks a better route. The second survives any rewrite and can
be checked from outside. `docs/outcome-vs-implementation.md` has the tests, a table of
ten examples, and the one legitimate exception (a technology imposed from outside, which
must carry a `why:` explaining who imposed it).

## Workflow

**1. Clone it.**

```
git clone git@github.com:ctsapugay/constraint-base.git my-project
cd my-project
rm -rf .git && git init
```

**2. Point an agent at it.** In a session with the repo open, say something like *"read
CLAUDE.md and run intake with me."* `CLAUDE.md` is the entry point — an agent that reads
it knows how the system works and what to do next, with no other setup.

**3. Intake.** The agent interviews you: the problem, who it's for, what becomes true,
what's out of scope, what would count as going wrong. It writes the answers to
`constraints/project.md` and `goals/outcomes.md`. It asks about implementation only to
note technologies that are genuinely imposed on you.

**4. Goal condition.** Intake ends with the agent drafting a finish line — a paragraph
plus three to seven criteria, each with a check you could run yourself. You approve or
edit it.

**5. Goal mode.** The agent works toward the goal condition inside the constraints,
re-grounding itself with `tools/brief.py` as it goes, marking criteria met only with
real evidence, and logging progress. It stops when the criteria are met.

## The defaults

Every project inherits seven rules, in `constraints/defaults.md`. They are deliberately
few and deliberately rule-shaped:

| | |
|---|---|
| `C-LOCAL` | Development stays local. No deploying, publishing, provisioning hosted infrastructure, or pushing to production unless you say so explicitly in that session. |
| `C-BLAST-RADIUS` | Changes stay inside the project directory. |
| `C-NO-SILENT-DESTRUCTION` | No irreversible destruction of work the agent didn't create. |
| `C-SECRETS` | No credentials in tracked files. |
| `C-EVIDENCE` | No completion claim without a check that was actually run. |
| `C-RESUMABLE` | A fresh session can resume from the repo alone. |
| `C-SURFACE-AMBIGUITY` | Ambiguity that changes the outcome goes to you; the rest is the agent's call. |

Any of them can be waived per project: set `status: waived` and give a reason. They are
never deleted, so the opt-out shows up in the diff.

## Tools

Two small stdlib-only Python scripts. No dependencies, no install.

```
python3 tools/brief.py       # constraints + goal condition + recent progress
python3 tools/validate.py    # are the files well-formed and outcome-shaped?
```

`brief.py` is the re-grounding call — an agent runs it at the start of a session and
periodically during a long run. `--goal` prints just the goal condition and criteria
status.

`validate.py` checks structure (required fields, unique IDs, no leftover placeholders,
no criterion marked met without evidence) and flags likely implementation detail:
library names, file paths, pattern names, "use X", step sequences. Those are warnings, not
errors — they are heuristics, and the point is to make you look at the line. `--strict`
turns warnings into a nonzero exit.

## Layout

```
CLAUDE.md                 entry point — an agent reads this and knows what to do
README.md                 this file
constraints/
  defaults.md             inherited rules, waivable
  project.md              project-specific rules
goals/
  outcomes.md             problem, audience, outcomes, non-goals, open questions
  goal-condition.md       the finish line
progress/
  log.md                  append-only session record
docs/
  outcome-vs-implementation.md
  intake.md
  goal-conditions.md
tools/
  brief.py
  validate.py
  constraint_files.py     shared parser
commands/                 optional slash commands: intake, reground, goal-check
```

The slash commands are inert until copied into place:

```
mkdir -p .claude/commands && cp commands/*.md .claude/commands/
```

They only wrap what `CLAUDE.md` already describes — skip them if you prefer to just talk
to the agent.

## Design notes

**Markdown, not YAML or JSON.** These files are read by humans and agents in roughly equal
measure and edited by hand constantly. The format is a strict heading-plus-fields
convention that a 200-line regex parser handles reliably, and that reads as prose.

**Nothing is generated.** There is no build step, no state outside the files, no
lockfile. Edit anything by hand at any time; the tools read whatever is there.

**The tools have no authority.** `validate.py` reports; it does not block. Nothing in the
repo can stop an agent doing something — the constraints work by being read, which is why
`CLAUDE.md` puts them in front of the agent before anything else.
