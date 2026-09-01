#!/usr/bin/env python3
"""A compact, glanceable progress readout. Built to be read on a phone.

    python3 tools/status.py          # one-screen status
    python3 tools/status.py --json   # the same numbers, machine-readable

brief.py is the agent's full re-grounding call. status.py is the opposite end: the
smallest honest answer to "how far along is it, and is anything wrong?", short enough to
paste into a chat and read on a phone over Remote Control.

The headline number is criteria met over criteria total. Read it honestly: criteria are
binary and equally weighted here, so this is progress by *count*, not by effort or by
lines of code. Four small criteria and one enormous one still read as 4/5. That is a
deliberate limitation -- the finish line is a set of checkable facts, not a burndown.

Standard library only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from constraint_files import (  # noqa: E402
    approved_ids,
    drift,
    load_baseline,
    load_constraints,
    load_goal,
    load_proposals,
    recent_log_entries,
    signing_configured,
)

BAR_CELLS = 10


def _partition_constraints(approved: set[str]):
    """(in force, effectively waived, waiver-pending-so-still-binding)."""
    binding, waived, pending = [], [], []
    for c in load_constraints():
        if c.get("status").lower() != "waived":
            binding.append(c)
        elif c.get("waived-by").upper() in approved:
            waived.append(c)
        else:
            binding.append(c)
            pending.append(c)
    return binding, waived, pending


def collect() -> dict:
    approved = approved_ids()
    status, criteria, statement = load_goal()
    goal_state = (status.get("state") if status else "unknown") or "unknown"

    real_criteria = [g for g in criteria if not g.get("criterion", "").startswith("_Not yet")]
    total = len(real_criteria)
    met = sum(1 for g in real_criteria if g.get("state").lower() == "met")

    binding, waived, pending = _partition_constraints(approved)
    baseline = load_baseline()
    proposals = load_proposals()
    pending_props = [p for p in proposals if p.get("status").lower() == "proposed"]
    changed = drift()

    entries = recent_log_entries(9999)
    last_title = ""
    if entries:
        head = entries[-1].splitlines()[0]
        last_title = head[3:].strip() if head.startswith("## ") else head.strip()

    return {
        "goal_state": goal_state,
        "statement": statement,
        "criteria_total": total,
        "criteria_met": met,
        "percent": round(100 * met / total) if total else 0,
        "criteria": [
            {
                "id": g.id,
                "title": g.title,
                "met": g.get("state").lower() == "met",
                "has_evidence": bool(g.get("evidence")),
            }
            for g in real_criteria
        ],
        "constraints_in_force": len(binding),
        "constraints_waived": len(waived),
        "waivers_pending": len(pending),
        "governance_engaged": baseline.exists,
        "signing": signing_configured(),
        "drift": sorted(changed.keys()),
        "proposals_pending": len(pending_props),
        "log_entries": len(entries),
        "last_log_title": last_title,
    }


def _bar(percent: int) -> str:
    filled = round(BAR_CELLS * percent / 100)
    return "[" + "■" * filled + "□" * (BAR_CELLS - filled) + "]"


def render(s: dict) -> str:
    out: list[str] = []
    out.append(f"CONSTRAINT-BASE STATUS  ·  goal: {s['goal_state']}")
    if s["criteria_total"]:
        out.append(
            f"{s['criteria_met']}/{s['criteria_total']} criteria met  "
            f"{_bar(s['percent'])} {s['percent']}%"
        )
    else:
        out.append("No criteria yet (intake has not produced a finish line).")
    out.append("")

    if s["criteria"]:
        out.append("Criteria")
        for c in s["criteria"]:
            mark = "x" if c["met"] else " "
            tail = "" if not c["met"] else ("  (evidence ✓)" if c["has_evidence"] else "  (NO EVIDENCE!)")
            out.append(f"  [{mark}] {c['id']} — {c['title']}{tail}")
        out.append("")

    out.append("Guardrails")
    gline = f"  {s['constraints_in_force']} constraints in force"
    if s["constraints_waived"]:
        gline += f" · {s['constraints_waived']} waived"
    if s["waivers_pending"]:
        gline += f" · ⚠ {s['waivers_pending']} waiver(s) pending (still binding)"
    out.append(gline)

    if not s["governance_engaged"]:
        out.append("  Governance: not engaged (intake phase — finish line not yet locked)")
    elif s["drift"]:
        out.append(f"  Governance: ⚠ DRIFT from approved baseline in {', '.join(s['drift'])}")
    else:
        mode = "signed" if s["signing"] else "attribution-only"
        out.append(f"  Governance: engaged, no drift ({mode})")
    if s["proposals_pending"]:
        out.append(f"  Proposals: {s['proposals_pending']} awaiting your sign-off")
    out.append("")

    out.append("Activity")
    if s["log_entries"]:
        out.append(f"  {s['log_entries']} log entries · last: \"{s['last_log_title']}\"")
    else:
        out.append("  no progress logged yet")
    out.append("")
    out.append("Note: progress is by criteria count — each binary and equally weighted,")
    out.append("not a measure of effort. See the log for what actually happened.")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    s = collect()
    if "--json" in argv:
        print(json.dumps(s, indent=2))
    else:
        print(render(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
