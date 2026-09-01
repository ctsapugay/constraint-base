---
description: Render the Constraint Board dashboard and update the shared Artifact link
---

Produce the phone-friendly progress dashboard and publish it as an Artifact, keeping the
**same URL** each time so a bookmark always shows the latest.

Do this:

1. **Freshness.** If the argument is `fresh` ($ARGUMENTS) *and* no other session is
   actively running the worker in this directory, run `python3 tools/verify.py` first to
   re-run the check suite. Otherwise do **not** re-run checks — from an observer session
   while the worker is mid-task, re-running could collide with it. Skipping is safe: the
   board shows a STALE flag when the code has changed since the last verify, so a stale
   green can't masquerade as current.

2. **Render.** `python3 tools/status.py --html --out checks/board.html`

3. **Publish, keeping the link stable.**
   - If `checks/board-url.txt` exists, read the URL in it and update *that* artifact
     (pass it as the artifact `url`), so the phone link never changes.
   - Otherwise publish `checks/board.html` as a new artifact — title "Constraint Board",
     favicon 🧭 — then write its URL to `checks/board-url.txt`.

4. **Report.** Give Clara the URL. If the board shows the suite as STALE, tell her to run
   `/board fresh` (or have the worker run `tools/verify.py`) to re-prove the current code.

This command is read-only over the constraint system: it renders and publishes state, and
never edits constraints, goals, the registry, or runs `approve.py`.
