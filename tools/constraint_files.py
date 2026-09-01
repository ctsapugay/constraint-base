"""Parser for the constraint-base file format.

The format is Markdown with a convention:

    ## ID — Short title
    - **field:** value
    - **other:** value that may
      continue on indented lines

Every ``## `` heading starts a section. If the heading looks like ``ID — title`` (an
uppercase-ish id, a dash, a title) the section gets an id. Bullets of the form
``- **key:** value`` become fields. Everything else is prose and is ignored.

Standard library only, by design. No install step.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONSTRAINT_FILES = [
    ROOT / "constraints" / "defaults.md",
    ROOT / "constraints" / "project.md",
]
GOAL_FILE = ROOT / "goals" / "goal-condition.md"
OUTCOMES_FILE = ROOT / "goals" / "outcomes.md"
LOG_FILE = ROOT / "progress" / "log.md"

# "## C-LOCAL — Development stays local"  /  "## G1 - Something"
HEADING_RE = re.compile(r"^##\s+(?P<rest>.+?)\s*$")
ID_TITLE_RE = re.compile(
    r"^(?P<id>[A-Z][A-Za-z0-9-]{0,39})\s+[—–-]\s+(?P<title>.+)$"
)
FIELD_RE = re.compile(r"^-\s+\*\*(?P<key>[a-zA-Z][a-zA-Z0-9 _-]*):\*\*\s*(?P<value>.*)$")
CONTINUATION_RE = re.compile(r"^\s{2,}(?P<value>\S.*)$")
FENCE_RE = re.compile(r"^\s*```")

PLACEHOLDER_MARKERS = (
    "<!-- INTAKE:",
    "_Not yet",
    "_not yet",
    "_..._",
    "_No project constraints defined yet",
)


@dataclass
class Section:
    """One ``## `` heading and the fields under it."""

    heading: str
    id: str | None
    title: str
    fields: dict[str, str] = field(default_factory=dict)
    field_lines: dict[str, int] = field(default_factory=dict)
    line: int = 0
    source_file: Path | None = None

    @property
    def label(self) -> str:
        return self.id or self.title

    def get(self, key: str, default: str = "") -> str:
        return self.fields.get(key, default).strip()

    def where(self, key: str | None = None) -> str:
        name = self.source_file.name if self.source_file else "?"
        lineno = self.field_lines.get(key, self.line) if key else self.line
        return f"{name}:{lineno}"


def parse_file(path: Path) -> list[Section]:
    """Return every ``## `` section in ``path``. Missing file -> empty list."""
    if not path.exists():
        return []

    sections: list[Section] = []
    current: Section | None = None
    last_key: str | None = None
    in_fence = False

    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if FENCE_RE.match(raw):
            in_fence = not in_fence
            last_key = None
            continue
        if in_fence:
            continue

        heading = HEADING_RE.match(raw)
        if heading:
            rest = heading.group("rest").strip()
            match = ID_TITLE_RE.match(rest)
            if match:
                current = Section(
                    heading=rest,
                    id=match.group("id"),
                    title=match.group("title").strip(),
                    line=lineno,
                    source_file=path,
                )
            else:
                current = Section(
                    heading=rest, id=None, title=rest, line=lineno, source_file=path
                )
            sections.append(current)
            last_key = None
            continue

        if current is None:
            continue

        fieldmatch = FIELD_RE.match(raw)
        if fieldmatch:
            key = fieldmatch.group("key").strip().lower()
            current.fields[key] = fieldmatch.group("value").strip()
            current.field_lines[key] = lineno
            last_key = key
            continue

        cont = CONTINUATION_RE.match(raw)
        if cont and last_key:
            current.fields[last_key] = (
                current.fields[last_key] + " " + cont.group("value").strip()
            ).strip()
            continue

        if not raw.strip():
            last_key = None


    return sections


def load_constraints() -> list[Section]:
    """Constraints from both files, in file order. Only id-bearing sections count."""
    out: list[Section] = []
    for path in CONSTRAINT_FILES:
        for section in parse_file(path):
            if section.id and section.id.startswith("C-"):
                out.append(section)
    return out


def load_goal() -> tuple[Section | None, list[Section], str]:
    """Return (status section, criteria, statement text)."""
    sections = parse_file(GOAL_FILE)
    status = next((s for s in sections if s.id is None and s.title.lower() == "status"), None)
    criteria = [s for s in sections if s.id and s.id.upper().startswith("G")]
    return status, criteria, _statement_text()


def _statement_text() -> str:
    if not GOAL_FILE.exists():
        return ""
    lines = GOAL_FILE.read_text(encoding="utf-8").splitlines()
    collecting = False
    out: list[str] = []
    for raw in lines:
        if raw.strip().lower().startswith("## statement"):
            collecting = True
            continue
        if collecting and raw.startswith("## "):
            break
        if collecting:
            stripped = raw.strip()
            if stripped and not stripped.startswith("<!--"):
                out.append(stripped)
    return " ".join(out).strip()


def has_placeholders(path: Path) -> list[tuple[int, str]]:
    """Lines in ``path`` that still carry intake placeholder markers."""
    if not path.exists():
        return []
    found = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for marker in PLACEHOLDER_MARKERS:
            if marker in raw:
                found.append((lineno, raw.strip()))
                break
    return found


def recent_log_entries(limit: int = 3) -> list[str]:
    """The last ``limit`` ``## `` entries of the progress log, newest last."""
    if not LOG_FILE.exists():
        return []
    text = LOG_FILE.read_text(encoding="utf-8")
    if "\n---\n" in text:
        text = text.split("\n---\n", 1)[1]
    chunks: list[str] = []
    current: list[str] = []
    for raw in text.splitlines():
        if raw.startswith("## "):
            if current:
                chunks.append("\n".join(current).strip())
            current = [raw]
        elif current:
            current.append(raw)
    if current:
        chunks.append("\n".join(current).strip())
    return [c for c in chunks if c][-limit:]
