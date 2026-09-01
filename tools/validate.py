#!/usr/bin/env python3
"""Check that constraints and goals are well-formed and outcome-shaped.

    python3 tools/validate.py            # report; exit 1 only on errors
    python3 tools/validate.py --strict   # exit 1 on warnings too
    python3 tools/validate.py --quiet    # only print problems

ERRORS are structural: missing fields, duplicate ids, a criterion marked met with no
evidence. They mean a tool or an agent will misread the file.

WARNINGS are heuristics for implementation detail leaking into a rule -- library names,
file paths, pattern names, "use X", step sequences. They are guesses. Read the flagged
line and decide. Do not edit this script to silence one; if a flagged line is genuinely
fine, leave it and say why in progress/log.md.

See docs/outcome-vs-implementation.md.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from constraint_files import (  # noqa: E402
    CONSTRAINT_FILES,
    GOAL_FILE,
    OUTCOMES_FILE,
    ROOT,
    has_placeholders,
    load_constraints,
    load_goal,
    parse_file,
)

CONSTRAINT_REQUIRED = ("source", "status", "rule", "check")
CRITERION_REQUIRED = ("criterion", "check", "state")
VALID_STATUS = ("active", "waived")
VALID_CRITERION_STATE = ("unmet", "met")
VALID_GOAL_STATE = ("draft", "approved", "met")

# --- outcome-shape heuristics -------------------------------------------------

TECHNOLOGIES = (
    "postgres postgresql mysql sqlite mongodb redis memcached elasticsearch kafka "
    "rabbitmq celery docker kubernetes terraform ansible nginx apache aws azure gcp "
    "s3 lambda dynamodb firebase supabase vercel netlify heroku "
    "react vue angular svelte next.js nextjs nuxt tailwind bootstrap jquery "
    "django flask fastapi rails express nestjs spring laravel "
    "pytest unittest jest mocha vitest cypress playwright selenium "
    "numpy pandas sqlalchemy pydantic requests axios lodash webpack vite babel "
    "graphql grpc rest-api openapi swagger "
    "typescript javascript python java golang rust ruby php kotlin swift "
    "node npm yarn pnpm pip poetry cargo maven gradle"
).split()

PATTERNS = (
    "singleton factory observer decorator adapter facade repository-pattern "
    "microservice monolith mvc mvvm hexagonal event-driven pub-sub cqrs "
    "dependency-injection middleware orm dao dto"
).split()

# imperative build verbs, only when they open a sentence
IMPERATIVE_RE = re.compile(
    r"(?:^|\.\s+|;\s+)(use|add|create|build|implement|refactor|restructure|structure"
    r"|install|import|extend|inherit|wrap|split|merge|rename|move)\b",
    re.IGNORECASE,
)
MODAL_IMPERATIVE_RE = re.compile(
    r"\b(?:must|should|shall|will|needs? to|has to|have to)\s+"
    r"(use|add|create|build|implement|refactor|install|import|extend|wrap)\b",
    re.IGNORECASE,
)
PATH_RE = re.compile(r"\b[\w.-]+/[\w./-]+|\b\w+\.(?:py|js|jsx|ts|tsx|go|rs|rb|java|json|ya?ml|toml|ini|cfg)\b")
SEQUENCE_RE = re.compile(
    r"\bstep\s*\d|\bfirst,|\bfirstly\b|;\s*then\b|\bthen\s+(?:the|it|we|you)\b"
    r"|\bafterwards\b|\bfinally,",
    re.IGNORECASE,
)
COVERAGE_RE = re.compile(r"\b\d{1,3}\s*%\s*(?:code\s*)?coverage\b|\bcoverage\s+(?:of|above|at least)\s*\d", re.IGNORECASE)

TECH_RE = re.compile(r"\b(" + "|".join(re.escape(t) for t in TECHNOLOGIES) + r")\b", re.IGNORECASE)
PATTERN_RE = re.compile(
    r"\b(" + "|".join(re.escape(p).replace(r"\-", "[- ]") for p in PATTERNS) + r")\b"
    r"|\b\w+\s+(?:pattern|architecture)\b",
    re.IGNORECASE,
)


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")

    def note(self, msg: str) -> None:
        self.notes.append(msg)


def shape_warnings(text: str, has_why: bool) -> list[str]:
    """Heuristic complaints about a rule or criterion that describes *how*."""
    out: list[str] = []
    if not text:
        return out

    tech = TECH_RE.findall(text)
    if tech and not has_why:
        out.append(
            f"names a technology ({', '.join(sorted(set(t.lower() for t in tech)))}) "
            "without a 'why:' field. If it is imposed from outside, add why: saying who "
            "imposes it. Otherwise rewrite as an outcome."
        )

    pat = [m.group(0).strip() for m in PATTERN_RE.finditer(text)]
    if pat:
        out.append(
            f"names a design pattern ({', '.join(sorted(set(p.lower() for p in pat)))}). "
            "Describe the behaviour it is meant to produce instead."
        )

    paths = PATH_RE.findall(text)
    if paths:
        out.append("mentions a file or directory path. Rules should not prescribe layout.")

    imp = IMPERATIVE_RE.search(text) or MODAL_IMPERATIVE_RE.search(text)
    if imp:
        out.append(
            f"reads as an instruction ('{imp.group(1).lower()}...'). "
            "State what must be true, not what to do."
        )

    if SEQUENCE_RE.search(text):
        out.append("describes a sequence of steps. A rule holds at all times; it has no order.")

    if COVERAGE_RE.search(text):
        out.append("sets a coverage target. Tie the requirement to observable behaviour instead.")

    return out


def check_constraints(report: Report) -> list:
    constraints = load_constraints()
    seen: dict[str, str] = {}

    for path in CONSTRAINT_FILES:
        if not path.exists():
            report.error(path.name, "file is missing")

    for c in constraints:
        where = c.where()
        expected_source = "default" if "defaults.md" in str(c.source_file) else "project"

        for key in CONSTRAINT_REQUIRED:
            if not c.get(key):
                report.error(f"{where} [{c.id}]", f"missing required field '{key}:'")

        if c.id in seen:
            report.error(f"{where} [{c.id}]", f"duplicate id, already used at {seen[c.id]}")
        seen[c.id] = where

        source = c.get("source").lower()
        if source and source != expected_source:
            report.error(
                f"{where} [{c.id}]",
                f"source is '{source}' but it lives in {c.source_file.name} "
                f"(expected '{expected_source}')",
            )

        status = c.get("status").lower()
        if status and status not in VALID_STATUS:
            report.error(
                f"{where} [{c.id}]",
                f"status '{status}' is not one of {', '.join(VALID_STATUS)}",
            )
        if status == "waived" and not c.get("waived"):
            report.error(
                f"{where} [{c.id}]",
                "waived constraints need a 'waived:' field giving the reason",
            )
        if status == "active" and c.get("waived"):
            report.warn(f"{where} [{c.id}]", "has a 'waived:' reason but status is active")

        rule = c.get("rule")
        if rule and len(rule) < 25:
            report.warn(f"{where} [{c.id}]", "rule is very short; is it specific enough to check?")
        if c.get("check") and len(c.get("check")) < 25:
            report.warn(f"{where} [{c.id}]", "check is very short; could someone else run it?")

        for msg in shape_warnings(rule, has_why=bool(c.get("why"))):
            report.warn(f"{where} [{c.id}] rule", msg)

    active = [c for c in constraints if c.get("status").lower() == "active"]
    waived = [c for c in constraints if c.get("status").lower() == "waived"]
    report.note(f"{len(active)} active constraints, {len(waived)} waived.")
    return constraints


def check_goal(report: Report) -> None:
    if not GOAL_FILE.exists():
        report.error(GOAL_FILE.name, "file is missing")
        return

    status, criteria, statement = load_goal()

    if status is None:
        report.error(GOAL_FILE.name, "no '## Status' section")
    else:
        state = status.get("state").lower()
        if state not in VALID_GOAL_STATE:
            report.error(
                status.where("state"),
                f"goal state '{state}' is not one of {', '.join(VALID_GOAL_STATE)}",
            )
        if state == "draft":
            report.note(
                "Goal condition is still a draft. Intake is not finished until Clara "
                "approves it (set state: approved)."
            )

    if not statement or statement.lower().startswith("_not yet"):
        report.note("Goal condition has no statement yet.")

    if not criteria:
        report.error(GOAL_FILE.name, "no criteria (expected sections like '## G1 — ...')")

    seen: dict[str, str] = {}
    for g in criteria:
        where = g.where()
        for key in CRITERION_REQUIRED:
            if not g.get(key):
                report.error(f"{where} [{g.id}]", f"missing required field '{key}:'")

        if g.id in seen:
            report.error(f"{where} [{g.id}]", f"duplicate id, already used at {seen[g.id]}")
        seen[g.id] = where

        state = g.get("state").lower()
        if state and state not in VALID_CRITERION_STATE:
            report.error(
                f"{where} [{g.id}]",
                f"state '{state}' is not one of {', '.join(VALID_CRITERION_STATE)}",
            )
        if state == "met" and not g.get("evidence"):
            report.error(
                f"{where} [{g.id}]",
                "marked met with no 'evidence:'. A criterion is met only after its "
                "check has been run and observed (constraint C-EVIDENCE).",
            )

        check = g.get("check")
        if check and len(check) < 25:
            report.warn(
                f"{where} [{g.id}]",
                "check is very short. Could a skeptic run it without asking questions?",
            )

        for msg in shape_warnings(g.get("criterion"), has_why=bool(g.get("why"))):
            report.warn(f"{where} [{g.id}] criterion", msg)

    if criteria:
        met = sum(1 for g in criteria if g.get("state").lower() == "met")
        report.note(f"{met}/{len(criteria)} goal criteria met.")
        if len(criteria) > 8:
            report.warn(
                GOAL_FILE.name,
                f"{len(criteria)} criteria. More than about seven tends to mean a task "
                "list rather than a finish line.",
            )


def check_placeholders(report: Report) -> None:
    remaining = []
    for path in (ROOT / "constraints" / "project.md", OUTCOMES_FILE, GOAL_FILE):
        hits = has_placeholders(path)
        if hits:
            remaining.append((path, hits))
    if remaining:
        total = sum(len(h) for _, h in remaining)
        report.note(
            f"{total} intake placeholder(s) still present in "
            + ", ".join(p.name for p, _ in remaining)
            + " -- intake has not been completed."
        )


def main(argv: list[str]) -> int:
    strict = "--strict" in argv
    quiet = "--quiet" in argv

    report = Report()
    check_constraints(report)
    check_goal(report)
    check_placeholders(report)

    if report.errors:
        print(f"\nERRORS ({len(report.errors)})")
        for line in report.errors:
            print(f"  x {line}")

    if report.warnings:
        print(f"\nWARNINGS ({len(report.warnings)}) -- heuristics, read and judge")
        for line in report.warnings:
            print(f"  ! {line}")

    if report.notes and not quiet:
        print("\nNOTES")
        for line in report.notes:
            print(f"  - {line}")

    if not report.errors and not report.warnings:
        print("\nOK -- constraints and goal condition are well-formed.")
    print()

    if report.errors:
        return 1
    if strict and report.warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
