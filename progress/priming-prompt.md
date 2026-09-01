# Priming prompt

A paste-in block to boot a cold session fast. Editable — keep it current, and carry it to
each new session. It points the session at what it needs; it does not replace reading
`CLAUDE.md`. Everything below the divider is the block to paste; edit the project line.

---

You are resuming work on this project. Do this first, in order:

1. Read `CLAUDE.md` fully — it is the entry point and explains the constraint system.
2. Run `python3 tools/brief.py` and read it: the constraints, the goal condition, the
   working state (current checkpoint and open blockers), and recent progress.
3. Read `progress/checkpoint.md` (where the work is right now), then `progress/blockers.md`
   (what is stuck), then the tail of `progress/log.md` (how it got here).
4. You are in goal mode. Work toward the goal condition inside the constraints. Keep going
   across fronts; stop only when genuinely blocked on every front, or when an action would
   be dangerous or irreversible. Log at every natural break and keep the checkpoint fresh.

Project: <one line on what this project is — edit me>
