---
description: Test each goal criterion against reality and update its state and evidence
---

Run `python3 tools/brief.py --goal`.

For each criterion, actually run its `check:`. Not a mental simulation, not an inference
from the code — run the command, open the thing, trigger the behaviour, and observe the
result. This is constraint C-EVIDENCE and it is the one most easily fudged.

Then update `goals/goal-condition.md`:

- Criterion passed → `state: met`, and fill `evidence:` with what you ran and what it
  output, with today's date.
- Criterion failed → leave it `unmet` and say what specifically fell short.
- Check could not be run → say why. Do not mark it met.

Update `state:` and `evidence:` only. The criterion text and its check are governed —
if a criterion turns out to be unmeetable or wrongly worded, that is a proposal
(`commands/propose.md`), not an edit. Rewording a criterion so the work passes is the
exact failure this system exists to prevent.

Run `python3 tools/validate.py` afterwards. It will flag any drift in the governed part
of the goal condition.

Report: how many criteria are met, what is left, and what the next step is.

If every criterion is met with real evidence, say the goal condition is satisfied and
stop working. Do not start improving things that are out of scope for done.
