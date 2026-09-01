#!/usr/bin/env python3
"""A glanceable progress readout. Text for chat, HTML for a phone.

    python3 tools/status.py             # one-screen text status
    python3 tools/status.py --json      # the same numbers, machine-readable
    python3 tools/status.py --html      # a self-contained dashboard (stdout)
    python3 tools/status.py --html --out board.html   # ...written to a file

brief.py is the agent's full re-grounding call. status.py is the opposite end: the
smallest honest answer to "how far along is it, and is it the right direction?" -- short
enough to read on a phone over Remote Control.

Its job is not to cheer. It is to SHOW PROOF: every criterion carries the check that
defines its "done" and, once met, the evidence that was actually recorded; the governance
panel states plainly whether the finish line still matches what Clara approved, and
whether approvals are signed or merely attributed. A number you cannot audit is not
confidence. The number here is criteria met over criteria total -- binary, equally
weighted, progress by *count* not effort -- and it is shown next to the evidence so it
can be checked, not just trusted.

The --html view is built to be published as an Artifact and opened on a phone. It is
self-contained (its only external requests are Google Fonts, which the Artifact sandbox
allows) and needs no server.

Standard library only.
"""

from __future__ import annotations

import html
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

    real = [g for g in criteria if not g.get("criterion", "").startswith("_Not yet")]
    total = len(real)
    met = sum(1 for g in real if g.get("state").lower() == "met")

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
                "criterion": g.get("criterion"),
                "check": g.get("check"),
                "evidence": g.get("evidence"),
                "has_evidence": bool(g.get("evidence")),
            }
            for g in real
        ],
        "constraints_in_force": len(binding),
        "constraint_ids": [c.id for c in binding],
        "constraints_waived": len(waived),
        "waivers_pending": len(pending),
        "waivers_pending_list": [{"id": c.id, "title": c.title} for c in pending],
        "governance_engaged": baseline.exists,
        "baseline_updated": baseline.updated,
        "signing": signing_configured(),
        "drift": sorted(changed.keys()),
        "proposals_pending": len(pending_props),
        "log_entries": len(entries),
        "last_log_title": last_title,
    }


# ------------------------------------------------------------------- text ----


def _bar(percent: int) -> str:
    filled = round(BAR_CELLS * percent / 100)
    return "[" + "■" * filled + "□" * (BAR_CELLS - filled) + "]"


def render_text(s: dict) -> str:
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
        mode = "signed" if s["signing"] else "attribution-only (unsigned)"
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


# ------------------------------------------------------------------- html ----

_STYLE = """
:root{
  --ground:#f4f6f5; --surface:#ffffff; --surface-2:#eef2f1;
  --ink:#1b2422; --muted:#5c6b68; --faint:#8a9794; --line:#e0e6e4;
  --accent:#0e6b62; --accent-soft:#d7e7e4;
  --ok:#1f9d57; --ok-soft:#dff3e6;
  --warn:#c8811a; --warn-soft:#f7ebd6;
  --bad:#c0392b; --bad-soft:#f6dfdb;
  --shadow:0 1px 2px rgba(20,40,36,.05),0 6px 20px rgba(20,40,36,.06);
}
:root:not([data-theme="light"]){}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ground:#0e1513; --surface:#161e1b; --surface-2:#1d2724;
    --ink:#e8edeb; --muted:#a2b0ac; --faint:#75827e; --line:#28322f;
    --accent:#43b3a6; --accent-soft:#123531;
    --ok:#46c884; --ok-soft:#13301f;
    --warn:#e0a944; --warn-soft:#332612;
    --bad:#e5715f; --bad-soft:#331d19;
    --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 22px rgba(0,0,0,.35);
  }
}
:root[data-theme="dark"]{
  --ground:#0e1513; --surface:#161e1b; --surface-2:#1d2724;
  --ink:#e8edeb; --muted:#a2b0ac; --faint:#75827e; --line:#28322f;
  --accent:#43b3a6; --accent-soft:#123531;
  --ok:#46c884; --ok-soft:#13301f;
  --warn:#e0a944; --warn-soft:#332612;
  --bad:#e5715f; --bad-soft:#331d19;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 22px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,-apple-system,sans-serif;
  line-height:1.5;-webkit-font-smoothing:antialiased;
  padding:22px 16px 60px}
.board{max-width:680px;margin:0 auto;display:flex;flex-direction:column;gap:20px}
.eyebrow{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;
  letter-spacing:.14em;text-transform:uppercase;color:var(--faint)}
.mono{font-family:"IBM Plex Mono",ui-monospace,monospace;
  font-variant-numeric:tabular-nums}

/* --- summary head --- */
.head{background:var(--surface);border:1px solid var(--line);border-radius:16px;
  box-shadow:var(--shadow);padding:20px;display:flex;gap:20px;align-items:center}
.ring{flex:0 0 auto}
.ring__num{font-family:"IBM Plex Mono",monospace;font-weight:600;
  font-variant-numeric:tabular-nums;fill:var(--ink)}
.ring__pct{font-family:"IBM Plex Mono",monospace;fill:var(--faint)}
.head__main{min-width:0}
.head__title{margin:2px 0 6px;font-size:22px;font-weight:600;letter-spacing:-.01em;
  text-wrap:balance}
.head__sub{color:var(--muted);font-size:14px;margin:0}
.badge{display:inline-flex;align-items:center;gap:7px;margin-top:12px;
  padding:6px 11px;border-radius:999px;font-size:12.5px;font-weight:500;
  border:1px solid transparent}
.badge .dot{width:8px;height:8px;border-radius:50%}
.badge--ok{background:var(--ok-soft);color:var(--ok);border-color:color-mix(in srgb,var(--ok) 25%,transparent)}
.badge--warn{background:var(--warn-soft);color:var(--warn);border-color:color-mix(in srgb,var(--warn) 25%,transparent)}
.badge--bad{background:var(--bad-soft);color:var(--bad);border-color:color-mix(in srgb,var(--bad) 30%,transparent)}
.badge--ok .dot{background:var(--ok)} .badge--warn .dot{background:var(--warn)} .badge--bad .dot{background:var(--bad)}

/* --- section scaffolding --- */
.sec__label{display:flex;align-items:baseline;justify-content:space-between;
  gap:10px;margin:4px 2px 10px}
.sec__label h2{margin:0;font-size:12px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--muted);font-weight:600}
.sec__count{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--faint)}

/* --- thesis --- */
.thesis{background:var(--accent-soft);border:1px solid color-mix(in srgb,var(--accent) 22%,transparent);
  border-radius:14px;padding:18px 20px}
.thesis .eyebrow{color:var(--accent)}
.thesis p{font-family:"IBM Plex Serif",Georgia,serif;font-size:19px;line-height:1.45;
  margin:8px 0 0;color:var(--ink);text-wrap:pretty}

/* --- criteria proof cards --- */
.crit{background:var(--surface);border:1px solid var(--line);border-left-width:4px;
  border-radius:12px;box-shadow:var(--shadow);padding:15px 16px;margin-bottom:11px;
  display:flex;gap:13px}
.crit--met{border-left-color:var(--ok)}
.crit--pending{border-left-color:var(--faint)}
.crit--flag{border-left-color:var(--bad)}
.crit__mark{flex:0 0 26px;height:26px;border-radius:50%;display:grid;place-items:center;
  font-size:15px;font-weight:700;margin-top:1px}
.crit--met .crit__mark{background:var(--ok-soft);color:var(--ok)}
.crit--pending .crit__mark{background:var(--surface-2);color:var(--faint)}
.crit--flag .crit__mark{background:var(--bad-soft);color:var(--bad)}
.crit__body{min-width:0;flex:1}
.crit__id{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--accent);
  font-weight:600;letter-spacing:.01em}
.crit__text{margin:3px 0 0;font-size:15px;color:var(--ink)}
.proof{margin-top:11px;border-top:1px dashed var(--line);padding-top:10px;
  display:flex;flex-direction:column;gap:8px}
.proof__row{display:grid;grid-template-columns:70px 1fr;gap:10px;align-items:start}
.proof__k{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.08em;
  text-transform:uppercase;color:var(--faint);padding-top:2px}
.proof__v{font-family:"IBM Plex Mono",monospace;font-size:12.5px;color:var(--muted);
  line-height:1.5;word-break:break-word}
.proof__v--evidence{color:var(--ink);background:var(--ok-soft);border-radius:7px;
  padding:8px 10px}
.proof__missing{color:var(--bad);font-weight:600}

/* --- guardrails --- */
.rails{background:var(--surface);border:1px solid var(--line);border-radius:14px;
  box-shadow:var(--shadow);padding:16px 18px;display:flex;flex-direction:column;gap:13px}
.rail{display:flex;gap:12px;align-items:flex-start}
.rail__k{flex:0 0 96px;font-size:12px;color:var(--muted);padding-top:2px}
.rail__v{flex:1;min-width:0;font-size:13.5px}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-family:"IBM Plex Mono",monospace;font-size:11px;padding:3px 8px;border-radius:6px;
  background:var(--surface-2);color:var(--muted);border:1px solid var(--line)}
.note{display:flex;gap:8px;font-size:12.5px;color:var(--warn);
  background:var(--warn-soft);border-radius:8px;padding:9px 11px;margin-top:2px}
.note--bad{color:var(--bad);background:var(--bad-soft)}
.foot{color:var(--faint);font-size:12px;text-align:center;line-height:1.6;
  padding-top:4px}
.foot .mono{color:var(--muted)}
@media (max-width:460px){
  .head{flex-direction:column;text-align:center;align-items:center}
  .badge{align-self:center}
  .rail{flex-direction:column;gap:4px}
  .rail__k{flex-basis:auto}
}
@media (prefers-reduced-motion:no-preference){
  .ring__arc{transition:stroke-dashoffset 1s cubic-bezier(.2,.7,.2,1)}
}
"""


def _esc(text) -> str:
    return html.escape(str(text or ""))


def _ring_svg(percent: int) -> str:
    r = 34
    import math
    circ = 2 * math.pi * r
    off = circ * (1 - percent / 100)
    return f"""<svg width="92" height="92" viewBox="0 0 92 92" class="ring" aria-hidden="true">
  <circle cx="46" cy="46" r="{r}" fill="none" stroke="var(--surface-2)" stroke-width="8"/>
  <circle class="ring__arc" cx="46" cy="46" r="{r}" fill="none" stroke="var(--ok)"
    stroke-width="8" stroke-linecap="round" transform="rotate(-90 46 46)"
    stroke-dasharray="{circ:.1f}" stroke-dashoffset="{off:.1f}"/>
  <text x="46" y="44" text-anchor="middle" class="ring__num" font-size="21">{percent}</text>
  <text x="46" y="60" text-anchor="middle" class="ring__pct" font-size="9" letter-spacing="1">% MET</text>
</svg>"""


def _trust_badge(s: dict) -> str:
    if not s["governance_engaged"]:
        return ('<span class="badge badge--warn"><span class="dot"></span>'
                'Finish line not yet locked (intake)</span>')
    if s["drift"]:
        return (f'<span class="badge badge--bad"><span class="dot"></span>'
                f'Drift from approved baseline: {_esc(", ".join(s["drift"]))}</span>')
    mode = "signed" if s["signing"] else "attribution-only"
    return (f'<span class="badge badge--ok"><span class="dot"></span>'
            f'Matches the baseline you approved · {mode}</span>')


def _criteria_html(s: dict) -> str:
    if not s["criteria"]:
        return ('<div class="crit crit--pending"><div class="crit__mark">○</div>'
                '<div class="crit__body"><p class="crit__text">No criteria yet. Intake '
                'has not produced a finish line, so there is nothing to prove against. '
                'Run intake to define what "done" means.</p></div></div>')
    rows = []
    for c in s["criteria"]:
        if c["met"] and not c["has_evidence"]:
            cls, mark = "crit--flag", "!"
        elif c["met"]:
            cls, mark = "crit--met", "✓"
        else:
            cls, mark = "crit--pending", "○"
        proof = [
            '<div class="proof__row"><div class="proof__k">Check</div>'
            f'<div class="proof__v">{_esc(c["check"])}</div></div>'
        ]
        if c["met"] and c["has_evidence"]:
            proof.append(
                '<div class="proof__row"><div class="proof__k">Evidence</div>'
                f'<div class="proof__v proof__v--evidence">{_esc(c["evidence"])}</div></div>'
            )
        elif c["met"]:
            proof.append(
                '<div class="proof__row"><div class="proof__k">Evidence</div>'
                '<div class="proof__v proof__missing">Marked met with no evidence — '
                'not proven. validate.py rejects this.</div></div>'
            )
        rows.append(
            f'<article class="crit {cls}"><div class="crit__mark">{mark}</div>'
            f'<div class="crit__body"><div class="crit__id">{_esc(c["id"])}'
            f' · {_esc(c["title"])}</div>'
            f'<p class="crit__text">{_esc(c["criterion"])}</p>'
            f'<div class="proof">{"".join(proof)}</div></div></article>'
        )
    return "".join(rows)


def _rails_html(s: dict) -> str:
    chips = "".join(f'<span class="chip">{_esc(cid)}</span>' for cid in s["constraint_ids"])
    parts = [
        '<div class="rail"><div class="rail__k">In force</div>'
        f'<div class="rail__v"><div class="chips">{chips or "—"}</div></div></div>'
    ]
    if s["governance_engaged"]:
        gov = ("<span class=\"mono\">no drift</span> · matches the baseline approved "
               f'<span class="mono">{_esc(s["baseline_updated"][:10])}</span>')
        if s["drift"]:
            gov = f'<span class="mono">DRIFT in {_esc(", ".join(s["drift"]))}</span>'
    else:
        gov = "not engaged — constraints and the finish line are still being written"
    parts.append(
        '<div class="rail"><div class="rail__k">Governance</div>'
        f'<div class="rail__v">{gov}</div></div>'
    )
    if s["governance_engaged"] and not s["signing"]:
        parts.append(
            '<div class="note">Approvals are <b>attribution-only (unsigned)</b>. '
            'An approval commit could be forged by anything with repo access. '
            'Enable signing to make approvals un-forgeable.</div>'
        )
    if s["waivers_pending"]:
        wl = ", ".join(_esc(w["id"]) for w in s["waivers_pending_list"])
        parts.append(
            f'<div class="note note--bad">{s["waivers_pending"]} waiver(s) '
            f'not approved ({wl}) — those constraints are <b>still binding</b>.</div>'
        )
    if s["proposals_pending"]:
        parts.append(
            '<div class="rail"><div class="rail__k">Proposals</div>'
            f'<div class="rail__v">{s["proposals_pending"]} awaiting your sign-off</div></div>'
        )
    return "".join(parts)


def render_html(s: dict) -> str:
    """Self-contained dashboard body. Publish as an Artifact; no server needed."""
    if s["criteria_total"]:
        title_line = f'{s["criteria_met"]} of {s["criteria_total"]} criteria proven'
        sub = "Each is a checkable fact with the evidence beside it."
    else:
        title_line = "Finish line not yet defined"
        sub = "Run intake to turn outcomes into checkable criteria."
    activity = (
        f'{s["log_entries"]} log entries · last: <span class="mono">'
        f'&ldquo;{_esc(s["last_log_title"])}&rdquo;</span>'
        if s["log_entries"] else "no progress logged yet"
    )
    return f"""<title>Constraint Board</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Serif:ital@0;1&display=swap">
<style>{_STYLE}</style>
<main class="board">
  <header class="head">
    {_ring_svg(s["percent"])}
    <div class="head__main">
      <div class="eyebrow">Constraint-base · goal {_esc(s["goal_state"])}</div>
      <h1 class="head__title">{_esc(title_line)}</h1>
      <p class="head__sub">{_esc(sub)}</p>
      {_trust_badge(s)}
    </div>
  </header>

  <section class="thesis">
    <div class="eyebrow">The finish line</div>
    <p>{_esc(s["statement"]) or "Not yet drafted."}</p>
  </section>

  <section>
    <div class="sec__label"><h2>Proof of progress</h2>
      <span class="sec__count">{s["criteria_met"]}/{s["criteria_total"]} met</span></div>
    {_criteria_html(s)}
  </section>

  <section>
    <div class="sec__label"><h2>Guardrails</h2>
      <span class="sec__count">{s["constraints_in_force"]} in force</span></div>
    <div class="rails">{_rails_html(s)}</div>
  </section>

  <footer class="foot">
    {activity}<br>
    Progress is by criteria count — each binary and equally weighted, not a measure of effort.
  </footer>
</main>"""


def main(argv: list[str]) -> int:
    s = collect()
    if "--json" in argv:
        print(json.dumps(s, indent=2))
        return 0
    if "--html" in argv:
        page = render_html(s)
        if "--out" in argv:
            out = argv[argv.index("--out") + 1]
            Path(out).write_text(page, encoding="utf-8")
            print(f"wrote {out}")
        else:
            print(page)
        return 0
    print(render_text(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
