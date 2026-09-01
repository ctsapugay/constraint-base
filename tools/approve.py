#!/usr/bin/env python3
"""Clara's approval command. Records what she has signed off on.

    python3 tools/approve.py --status          # pending proposals and any drift
    python3 tools/approve.py --baseline        # engage governance (end of intake)
    python3 tools/approve.py P-0001 [P-0002]   # approve proposals, re-record baseline
    python3 tools/approve.py --decline P-0001  # decline a proposal

This script is FOR CLARA. It is not a lock -- anything with a shell can run it. What it
does is make approval a deliberate, recorded, committed act, so that an approval which
was not hers is visible in git history afterwards rather than invisible. If you want
approval that an agent cannot fabricate, turn on commit signing; see docs/governance.md.

Standard library only.
"""

from __future__ import annotations

import datetime as _dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from constraint_files import (  # noqa: E402
    BASELINE_FILE,
    GOVERNANCE_DIR,
    PROPOSALS_DIR,
    current_digests,
    drift,
    git,
    in_git_repo,
    load_baseline,
    load_goal,
    load_proposals,
    signing_configured,
)

TODAY = _dt.date.today().isoformat()


def _fail(msg: str) -> int:
    print(f"\n  x {msg}\n")
    return 1


def _confirm(prompt: str, assume_yes: bool) -> bool:
    if assume_yes:
        print(f"{prompt} -- assumed yes (--yes)")
        return True
    if not sys.stdin.isatty():
        print(f"{prompt}\n  x Refusing: no terminal. Run this yourself, or pass --yes.")
        return False
    try:
        answer = input(f"{prompt} Type 'approve' to continue: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer == "approve"


def _write_baseline(approved: list[str]) -> None:
    GOVERNANCE_DIR.mkdir(parents=True, exist_ok=True)
    digests = current_digests()
    lines = [
        "# Approved baseline. Written by tools/approve.py -- do not hand-edit.",
        "# Hand-editing this file is exactly the tampering validate.py looks for.",
        "version 1",
        f"updated {_dt.datetime.now().isoformat(timespec='seconds')}",
        f"constraints {digests['constraints']}",
        f"goal {digests['goal']}",
        f"tools {digests['tools']}",
    ]
    lines += [f"approved {pid}" for pid in approved]
    BASELINE_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _stamp_proposal(section, new_status: str) -> None:
    path = section.source_file
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"^-\s+\*\*status:\*\*.*$",
        f"- **status:** {new_status}",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if re.search(r"^-\s+\*\*approved:\*\*", text, flags=re.MULTILINE):
        text = re.sub(
            r"^-\s+\*\*approved:\*\*.*$",
            f"- **approved:** {TODAY}" if new_status == "approved" else "- **approved:**",
            text,
            count=1,
            flags=re.MULTILINE,
        )
    path.write_text(text, encoding="utf-8")


def _commit(message: str, assume_yes: bool) -> int:
    if not in_git_repo():
        print("  ! Not a git repository. Baseline written, but not committed.")
        print("    Governance leans on git history; commit this yourself.")
        return 0
    paths = ["constraints", "goals", "governance", "proposals"]
    code, out = git("add", *paths)
    if code != 0:
        return _fail(f"git add failed: {out}")
    args = ["commit", "-m", message]
    if signing_configured():
        args.insert(1, "-S")
    code, out = git(*args)
    if code != 0:
        return _fail(f"git commit failed: {out}")
    print(f"  Committed: {message.splitlines()[0]}")
    if signing_configured():
        print("  Signed. validate.py will verify it against governance/allowed_signers.")
    else:
        print("  Unsigned -- attribution only. See docs/governance.md to strengthen this.")
    return 0


def cmd_status() -> int:
    baseline = load_baseline()
    proposals = load_proposals()
    pending = [p for p in proposals if p.get("status").lower() == "proposed"]

    print()
    if not baseline.exists:
        print("Governance: NOT ENGAGED (no approved baseline yet).")
        print("  Constraints and the goal condition are still freely editable.")
        print("  Run 'python3 tools/approve.py --baseline' once you approve the goal condition.")
    else:
        print(f"Governance: ENGAGED (baseline recorded {baseline.updated}).")
        print(f"  Approved proposals: {', '.join(baseline.approved) or 'none beyond the baseline'}")
        changed = drift()
        if changed:
            print("\n  ! GOVERNED CONTENT HAS CHANGED SINCE THE LAST APPROVAL:")
            for area in sorted(changed):
                print(f"      {area}")
            print("    Review 'git diff' and either revert it or approve it deliberately.")
        else:
            print("  No drift. Governed content matches the approved baseline.")

    print(f"\nProposals: {len(proposals)} total, {len(pending)} pending your sign-off.")
    for p in pending:
        print(f"\n  [{p.id}] {p.title}   ({p.get('kind') or 'unspecified kind'})")
        print(f"      targets:  {p.get('targets') or '-'}")
        print(f"      because:  {p.get('because') or '(no explanation given -- reject it)'}")
        print(f"      change:   {p.get('change') or '-'}")
        if p.get("risk"):
            print(f"      risk:     {p.get('risk')}")
        print(f"      file:     {p.source_file.name}")
    print()
    return 0


def cmd_baseline(assume_yes: bool) -> int:
    status, _criteria, _statement = load_goal()
    state = (status.get("state").lower() if status else "")
    if state != "approved":
        return _fail(
            "The goal condition is not approved yet (state is "
            f"'{state or 'missing'}'). Finish intake first: governance protects an "
            "agreed finish line, so there has to be one."
        )
    if load_baseline().exists:
        print("\nA baseline already exists. This will replace it with the current state.")

    print("\nAbout to record the CURRENT contents of:")
    print("  constraints/defaults.md, constraints/project.md, goals/goal-condition.md")
    print("  and the tool sources, as the approved baseline.")
    print("\nReview 'git diff' and read the constraints before you do this.")
    if not _confirm("\nRecord this as approved?", assume_yes):
        return _fail("Cancelled. Nothing written.")

    _write_baseline(load_baseline().approved)
    print(f"  Baseline written to {BASELINE_FILE.relative_to(BASELINE_FILE.parents[1])}")
    return _commit(
        "APPROVED: BASELINE\n\n"
        "Engage governance. Standing constraints and the goal condition are now "
        "changeable only through an approved proposal.",
        assume_yes,
    )


def cmd_approve(ids: list[str], assume_yes: bool) -> int:
    baseline = load_baseline()
    if not baseline.exists:
        return _fail(
            "No baseline yet. Run 'python3 tools/approve.py --baseline' first, once "
            "the goal condition is approved."
        )

    proposals = {p.id.upper(): p for p in load_proposals() if p.id}
    wanted = [i.upper() for i in ids]

    missing = [i for i in wanted if i not in proposals]
    if missing:
        return _fail(f"No such proposal: {', '.join(missing)}")

    already = [i for i in wanted if i in baseline.approved]
    if already:
        return _fail(f"Already approved: {', '.join(already)}")

    print()
    for pid in wanted:
        p = proposals[pid]
        if not p.get("because"):
            return _fail(
                f"{pid} has no 'because:' field. A proposal without a written "
                "explanation is not reviewable; send it back."
            )
        print(f"[{pid}] {p.title}  ({p.get('kind') or 'unspecified kind'})")
        print(f"    targets: {p.get('targets') or '-'}")
        print(f"    because: {p.get('because')}")
        print(f"    change:  {p.get('change') or '-'}")
        if p.get("risk"):
            print(f"    risk:    {p.get('risk')}")
        print()

    changed = drift()
    if changed:
        print("Governed content currently differs from the approved baseline in:")
        for area in sorted(changed):
            print(f"    {area}")
        print("Approving will record the CURRENT state as approved. Read 'git diff' first.")
    else:
        print("Note: governed content is unchanged from the last baseline. If this")
        print("proposal was meant to change a constraint, the edit has not been made yet.")

    if not _confirm(f"\nApprove {', '.join(wanted)} and re-record the baseline?", assume_yes):
        return _fail("Cancelled. Nothing written.")

    for pid in wanted:
        _stamp_proposal(proposals[pid], "approved")
    _write_baseline(baseline.approved + wanted)

    return _commit(
        f"APPROVED: {', '.join(wanted)}\n\n"
        + "\n".join(f"{pid}: {proposals[pid].title}" for pid in wanted),
        assume_yes,
    )


def cmd_decline(ids: list[str], assume_yes: bool) -> int:
    proposals = {p.id.upper(): p for p in load_proposals() if p.id}
    wanted = [i.upper() for i in ids]
    missing = [i for i in wanted if i not in proposals]
    if missing:
        return _fail(f"No such proposal: {', '.join(missing)}")
    for pid in wanted:
        _stamp_proposal(proposals[pid], "declined")
        print(f"  Declined {pid}: {proposals[pid].title}")
    return _commit(f"Decline proposal(s): {', '.join(wanted)}", assume_yes)


def main(argv: list[str]) -> int:
    assume_yes = "--yes" in argv
    args = [a for a in argv if a != "--yes"]

    if not args or "--status" in args:
        return cmd_status()
    if "--baseline" in args:
        return cmd_baseline(assume_yes)
    if "--decline" in args:
        ids = [a for a in args if a != "--decline"]
        if not ids:
            return _fail("Which proposal? e.g. --decline P-0001")
        return cmd_decline(ids, assume_yes)

    ids = [a for a in args if not a.startswith("--")]
    if not ids:
        return _fail("Nothing to do. Try --status.")
    if not PROPOSALS_DIR.exists():
        return _fail("No proposals/ directory.")
    return cmd_approve(ids, assume_yes)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
