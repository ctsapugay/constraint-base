# Intake

Intake is a conversation, not a form. The agent runs it with Clara, and its output is
written into `constraints/project.md`, `goals/outcomes.md`, and `goals/goal-condition.md`.

The point is to end with a finish line Clara agrees with and an agent that knows the
boundaries. It should take ten to twenty minutes, not an hour.

## How to run it

Ask questions in small batches — two or three at a time, not a wall. Reflect answers back
in your own words. Push on vagueness: "fast", "clean", "easy to use", and "robust" are not
outcomes until they are attached to something observable.

Do not ask about implementation. Not what stack, not what structure, not what libraries.
If Clara volunteers a technology, note it as **direction for this session** unless it is
imposed from outside — in which case it becomes a constraint with a `why:` field. See
`docs/outcome-vs-implementation.md`.

Do not write anything to disk until the end. Draft in conversation, get agreement, then
write all files in one pass.

## What to find out

**1. The problem.** What is painful, missing, or manual right now? What does she do today
instead? → `goals/outcomes.md` § Problem

**2. Who it is for.** Her alone, her team, users she will never meet? This changes what
done means more than anything else in intake. → § Who it is for

**3. The outcomes.** "When this exists, what is true that isn't true now?" Keep pulling
until each one is something you could observe. Three to six is usually right.
→ § Outcomes

**4. The non-goals.** "What are you explicitly not trying to do?" and "if I finished
early, what should I *not* start on?" These stop an agent in goal mode from wandering.
→ § Non-goals

**5. The boundaries.** "What would make you say this went wrong, even if it worked?"
That question finds real constraints faster than asking for constraints directly. Probe
for: data that must not be touched, things that must not become slow, environments it has
to run in, anything with a deadline or an external dependency.
→ `constraints/project.md`

**6. The defaults.** Show her the seven defaults in `constraints/defaults.md` in one
short list. Ask if any should be waived for this project. Most of the time none should
be — do not talk her into waiving any. If she waives one, set `status: waived` and record
her reason in `waived:`.

**7. Open questions.** Anything she has not decided. For each, propose an assumption the
agent will work under, and check she is fine with it.
→ `goals/outcomes.md` § Open questions

## Then draft the goal condition

Distil the outcomes into a goal condition and present it for approval or edit. This is
the part that matters most — read `docs/goal-conditions.md` before drafting.

Present it as: the one-paragraph statement, then the criteria with their checks, then
"anything missing, anything you would cut?" Expect to revise it once or twice.

When she approves, set `state: approved` in `goals/goal-condition.md` and record the date.

## Finish

1. Write the three files.
2. Run `python3 tools/validate.py`. Fix anything it reports. If it warns about a line
   that is genuinely fine, leave it and say why in the log — do not edit the validator to
   silence it.
3. Append an entry to `progress/log.md` recording that intake happened, what was agreed,
   and any assumptions.
4. Tell Clara what to run next, and that she can edit any of these files by hand at any
   time.

## What good output looks like

A stranger should be able to read `constraints/` and `goals/` and correctly predict which
work Clara would accept and which she would reject — without having been in the
conversation, and without being told how to build any of it.
