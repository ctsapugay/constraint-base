#!/usr/bin/env python3
"""Print the constraints, the goal condition, and recent progress.

    python3 tools/brief.py          # everything
    python3 tools/brief.py --goal   # just the goal condition and criteria
    python3 tools/brief.py --rules  # just the active constraints

Run this at the start of a session, and again periodically during a long run: after
finishing a chunk of work, before a decision that would be expensive to reverse, or
whenever you notice you have been going a while without checking. It is the re-grounding
call -- read the output, then ask whether what you are about to do stays inside the rules
and moves toward the finish line.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from constraint_files import (  # noqa: E402
    load_constraints,
    load_goal,
    recent_log_entries,
)

WIDTH = 88


def rule(char: str = "=") -> None:
    print(char * WIDTH)


def wrap(text: str, indent: str = "    ") -> str:
    return textwrap.fill(
        text, width=WIDTH, initial_indent=indent, subsequent_indent=indent
    )


def show_constraints() -> None:
    constraints = load_constraints()
    active = [c for c in constraints if c.get("status").lower() != "waived"]
    waived = [c for c in constraints if c.get("status").lower() == "waived"]

    rule()
    print(f"CONSTRAINTS -- {len(active)} active")
    rule()
    print(
        wrap(
            "These bound the work. They say what must remain true; they never say how "
            "to build anything. Implementation is your judgment.",
            indent="",
        )
    )
    print()

    for c in active:
        origin = "default" if c.get("source").lower() == "default" else "project"
        print(f"  [{c.id}] {c.title}  ({origin})")
        print(wrap(c.get("rule"), indent="      "))
        if c.get("check"):
            print(wrap(f"check: {c.get('check')}", indent="      "))
        print()

    if waived:
        print(f"  Waived for this project ({len(waived)}):")
        for c in waived:
            print(f"    [{c.id}] {c.title} -- {c.get('waived') or 'no reason given'}")
        print()


def show_goal() -> None:
    status, criteria, statement = load_goal()
    state = status.get("state") if status else "unknown"

    rule()
    print(f"GOAL CONDITION -- {state}")
    rule()

    if statement:
        print(wrap(statement, indent=""))
    else:
        print("  (no statement yet)")
    print()

    if state.lower() == "draft":
        print(wrap(
            "! Still a draft. Clara has not approved it. Finish intake before starting "
            "work -- see docs/intake.md.",
            indent="  ",
        ))
        print()

    met = 0
    for g in criteria:
        gstate = g.get("state").lower()
        mark = "x" if gstate == "met" else " "
        met += gstate == "met"
        print(f"  [{mark}] {g.id} -- {g.title}")
        print(wrap(g.get("criterion"), indent="      "))
        print(wrap(f"check: {g.get('check')}", indent="      "))
        if gstate == "met":
            print(wrap(f"evidence: {g.get('evidence') or '(NONE -- this is a problem)'}", indent="      "))
        print()

    if criteria:
        print(f"  {met}/{len(criteria)} criteria met.")
        if met == len(criteria):
            print(wrap(
                "All criteria are met. The work is finished -- stop here rather than "
                "looking for more to improve.",
                indent="  ",
            ))
        print()


def show_progress(limit: int = 3) -> None:
    entries = recent_log_entries(limit)
    rule()
    print(f"RECENT PROGRESS -- last {len(entries)} log entr{'y' if len(entries) == 1 else 'ies'}")
    rule()
    if not entries:
        print("  (progress/log.md is empty)")
        print()
        return
    for entry in entries:
        for line in entry.splitlines():
            print(f"  {line}" if line.strip() else "")
        print()


def main(argv: list[str]) -> int:
    only_goal = "--goal" in argv
    only_rules = "--rules" in argv

    if only_goal:
        show_goal()
        return 0
    if only_rules:
        show_constraints()
        return 0

    show_constraints()
    show_goal()
    show_progress()
    rule("-")
    print("Full detail: constraints/, goals/, progress/log.md. "
          "Well-formedness: python3 tools/validate.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
