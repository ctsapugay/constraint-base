# Default constraints

These are inherited by every project cloned from this base. They are deliberately few
and deliberately rule-shaped: each one says what must remain true, never how to build.

**Editing rules for this file**

- Do not delete a default. To opt out, set `status: waived` and add a `waived:` field
  explaining why. That keeps the opt-out visible in diffs and in review.
- Do not add project-specific constraints here. They belong in `project.md`.
- Every entry must keep the field set below. `tools/validate.py` enforces it.

**Entry format** (same in every constraint file):

```
## ID — Short title
- **source:** default | project
- **status:** active | waived
- **rule:** One sentence. What must remain true. Outcome-shaped.
- **check:** How anyone can tell, from the outside, whether the rule held.
- **why:** Optional. Required when the rule names a specific technology.
- **waived:** Required only when status is waived.
```

---

## C-LOCAL — Development stays local

- **source:** default
- **status:** active
- **rule:** Nothing leaves this machine. No deploying, publishing, releasing, provisioning of hosted infrastructure, DNS or domain changes, package-registry publishing, or pushing to any production or shared environment happens unless Clara says so explicitly in the current session.
- **check:** Every command and API call that would create, alter, or expose a resource outside this machine appears in `progress/log.md` next to the session message in which Clara approved it. Absent such an entry, no such action was taken.
- **why:** The default posture is a working local project. Going live is a decision Clara makes deliberately, not a side effect of an agent making progress.

## C-BLAST-RADIUS — Changes stay inside the project

- **source:** default
- **status:** active
- **rule:** Files outside the project directory are not created, modified, or deleted, and machine-wide or account-wide settings are not changed, without Clara's explicit approval in the current session.
- **check:** A diff of the project directory accounts for every change made. Nothing outside it was touched, or the exception is recorded in `progress/log.md` with the approval.

## C-NO-SILENT-DESTRUCTION — Existing work is not destroyed silently

- **source:** default
- **status:** active
- **rule:** Data or history the agent did not create in this session — Clara's files, existing commits, branches, databases — is not deleted, overwritten, or rewritten without explicit approval. Reversible edits are fine; irreversible ones are not.
- **check:** Every irreversible operation performed is listed in `progress/log.md` with the approval that preceded it, and anything overwritten was recoverable from version control at the time.

## C-SECRETS — No secrets in the repository

- **source:** default
- **status:** active
- **rule:** Credentials, tokens, keys, and personal data are never written into tracked files, and never printed into logs or transcripts that get committed.
- **check:** A scan of tracked files finds no credential-shaped values, and secrets in use are read from the environment or from files excluded by `.gitignore`.

## C-EVIDENCE — Completion claims carry evidence

- **source:** default
- **status:** active
- **rule:** Nothing is reported as done, working, or passing on the strength of reasoning alone. A claim is made only after the corresponding check has actually been run and observed.
- **check:** Each completion claim in `progress/log.md` and in session summaries names the check that was run and what it output.

## C-RESUMABLE — A fresh session can pick up the work

- **source:** default
- **status:** active
- **rule:** At any stopping point, someone starting a brand-new session with no memory of prior sessions can determine the current state of the project, what remains, and what was tried and rejected, from the repository alone.
- **check:** `progress/log.md` has an entry for the most recent working session, and `python3 tools/brief.py` prints constraints, goal condition, and recent progress with no placeholders left unfilled.

## C-SURFACE-AMBIGUITY — Outcome-changing ambiguity goes to Clara

- **source:** default
- **status:** active
- **rule:** When a decision would change what Clara ends up with — scope, behaviour she will notice, the meaning of the goal condition — it is raised with her rather than resolved by assumption. Decisions that only affect how the work is done are the agent's to make.
- **check:** Assumptions made without asking are listed in `progress/log.md`, and each is one Clara could reverse later without discarding completed work.
