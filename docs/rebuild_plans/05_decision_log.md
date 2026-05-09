---
id: 05_decision_log
title: Methodology decision log
version: 0.1
status: draft
owner: Methodology Council
depends_on: [00_README]
inputs: []
outputs:
  - {path: docs/governance/DECISION_LOG.md, schema: append-only DEC-YYYY-MM-DD-N entries}
  - {path: docs/governance/DECISION_LOG_INDEX.md, schema: topic index, auto-generated}
acceptance:
  - {test: every methodology choice in any plan or code change cites a DEC entry, method: cross-reference scan, pass_when: zero uncited choices}
  - {test: log is append-only for entries past their freeze, method: git history check, pass_when: no in-place edit of frozen DEC entries}
  - {test: superseded entries link bidirectionally to their successor, method: link integrity check, pass_when: no dangling links}
risks:
  - {risk: log becomes a dumping ground; entries are too vague to act on, mitigation: §3 entry schema enforces alternatives + consequences}
  - {risk: parallel decision logs (HIBEAM repo + this rebuild) drift, mitigation: §6 cross-repo mirroring policy}
estimated_effort: S
last_updated: 2026-05-09
---

# Methodology decision log

*Charter.* This plan defines the format, location, and maintenance rules
for the methodology decision log. Every load-bearing methodological
choice is recorded here. Code, plans, ledger rows, and reviewer-defence
packages cite log entries by ID. The log is the single audit trail
showing why the rebuild looks the way it does.

The HIBEAM repository already maintains a `docs/governance/DECISION_LOG.md`
with entries like `DEC-2026-04-24-1` (truth vertex source = converted CSV)
and `DEC-2026-05-08-1` (TrackGNN feature schema). This plan adopts the
same identifier format and entry schema and adds rules for
cross-repository mirroring.

## 1. Identifier format

```
DEC-YYYY-MM-DD-N
```

- `YYYY-MM-DD` — date the decision was approved (not drafted).
- `N` — within-day sequence (1, 2, …) to disambiguate multiple
  decisions on the same date.

IDs are immutable. A reversed decision creates a new entry that
supersedes the old; the old entry is annotated but never edited.

## 2. Storage location

```
docs/governance/
├── DECISION_LOG.md           # append-only, chronological
├── DECISION_LOG_INDEX.md     # topic index, auto-regenerated
└── archive/
    └── superseded_2026/      # optional reading order, auto-grouped
```

A single Markdown file is the source of truth. Codex-supervisor parses
entries by their `## DEC-YYYY-MM-DD-N` headers; the auto-generated
index regenerates after every entry append.

## 3. Entry schema

```markdown
## DEC-2026-05-09-1
**Topic.** [Short topic, e.g. "Truth vertex source = CSV"]
**Status.** approved | superseded | reverted
**Owners.** [WG, individuals]
**Plans affected.** [list of plan IDs]
**Code touched.** [list of files / modules, optional]
**Samples affected.** [dataset IDs from plan 03, optional]

### Context
[1–3 paragraphs. What problem motivated the decision. What was the
previous state. What constraints apply.]

### Decision
[1 paragraph. The choice in present tense, imperative voice.]

### Rationale
[Why this choice and not the alternatives.]

### Alternatives considered
1. [Alt 1] — rejected because …
2. [Alt 2] — rejected because …
3. [Alt 3] — kept for future revisit; conditions named.

### Consequences
- [What changes in code / data / plans.]
- [What new uncertainty or limitation is introduced.]
- [What downstream sign-offs are now required.]

### Supersedes / Superseded by
- Supersedes: DEC-YYYY-MM-DD-N (link)
- Superseded by: DEC-YYYY-MM-DD-N (filled when this entry is reversed)

### References
[Citations: papers, prior plans, code commits, meeting notes.]
```

A draft entry has `Status: draft`. Approval moves it to
`Status: approved` and locks the body.

## 4. Approval workflow

1. *Draft.* Anyone (codex-supervisor, user, supervisor) opens a draft
   entry. Status = `draft`.
2. *Review.* The Methodology Council reviews the entry against the
   schema. Reviewer asks: is the alternatives list complete? Is the
   consequence list honest about new limitations?
3. *Approval.* On approval, status flips to `approved`, the body is
   locked, and the entry is appended to `DECISION_LOG.md` with the
   final ID.
4. *Supersession.* A later entry that reverses or replaces an earlier
   one fills in the `Superseded by` link on the old entry (the only
   write allowed on an approved entry's body) and includes the new
   rationale.

## 5. Cross-references

Every plan opens with a `decision_log_entries` field in its YAML
header (currently optional; mandatory from v0.2 of the plan set).
Subsystem plans 25–37 cite the DEC entries that pinned the algorithm
they describe.

Every reproduction-ledger row (plan 47) cites the DEC entry that
controls the methodology for that row. Drift between the ledger row's
result and the DEC entry's claim is detected by plan 53 CI.

Every reviewer-defence package (plan 50) attaches the DEC entries
relevant to the result, so a reviewer asking "why did you do X?" gets
a single-link answer.

## 6. Cross-repository mirroring

The HIBEAM TPC vertex-reconstruction repository has its own decision
log. The two logs do not merge. Instead:

- HIBEAM-side decisions that materially affect this rebuild
  (truth-vertex source, unit conventions, feature schemas) are
  *mirrored* into our log as new DEC entries that cite the HIBEAM
  entry as the original source. The mirror entry is short and points
  to the original; it does not duplicate the body.
- Our decisions that materially affect the HIBEAM analysis are mirrored
  into the HIBEAM log via the same convention.
- The Methodology Council reviews mirror candidates monthly to ensure
  drift is bounded.

Example mirror entry:

```markdown
## DEC-2026-05-10-1
**Topic.** Mirror: HIBEAM vertex truth source = CSV
**Status.** approved
**Owners.** Methodology Council
**Plans affected.** [09, 13]

### Context
HIBEAM repository decision DEC-2026-04-24-1 establishes that the
authoritative truth vertex source is the converted CSV, not the
Particle_output table. Our rebuild's signal-model and validation paths
reference vertices and must adopt the same convention to keep cross-
repository numbers comparable.

### Decision
Adopt HIBEAM DEC-2026-04-24-1 verbatim for any reconstruction in this
rebuild that consumes vertex truth from sources HIBEAM also consumes.

### Consequences
- Plan 09 IO dictionary marks the relevant simulation columns with
  the HIBEAM convention.
- Plan 13 signal-model assessment uses the CSV-derived vertex when
  comparing against HIBEAM.

### References
- HIBEAM `docs/governance/DECISION_LOG.md` § DEC-2026-04-24-1
```

## 7. What goes in the log

In:
- Choice of algorithm where alternatives exist (vertex fit method,
  PID classifier, clustering algorithm, …).
- Choice of physics constant where calibration is ambiguous (TPC
  W-value, scintillator yield, …).
- Choice of sample for a quoted thesis number.
- Adoption of a method from prior art (cite the survey plan 48).
- Acceptance of a known limitation (link to plan 01 §6).
- Adoption of a third-party library or tool.

Out:
- Routine code refactors.
- Bug fixes that do not change a methodology.
- Stylistic / cosmetic choices.
- Choices documented entirely inside a plan that is itself approved
  (the plan approval is the decision).

## 8. Entry length discipline

A good DEC entry fits on one printed page (≈ 60 lines). Longer entries
indicate the decision is actually two decisions; split.

## 9. Acceptance criteria

- `docs/governance/DECISION_LOG.md` exists with at least three
  worked-example entries:
  1. The decision to adopt the perfect-detector-now / digitisation-seam
     architecture (plan 02).
  2. The decision to mirror HIBEAM `DEC-2026-04-24-1` (vertex truth).
  3. The decision to adopt CRY for cosmic regeneration (plan 21).
- `DECISION_LOG_INDEX.md` regenerates from the log without manual
  editing.
- The schema-citation audit (plan 53) is green: every plan that
  contains methodology choices has matching DEC references.

## 10. Risks and mitigations

- *Risk:* the log fills with low-information "we decided to use
  Python" entries.
  *Mitigation:* §7 explicitly excludes routine choices; reviewers
  reject low-content entries.
- *Risk:* the log lags behind reality — choices are made in code
  without DEC entries.
  *Mitigation:* plan 53 CI scans diffs for methodology-affecting
  changes (new algorithm files, edits to constants in `_realism.py`,
  changes to selection thresholds) and demands a paired DEC entry
  before merge.
- *Risk:* dual-repo drift.
  *Mitigation:* §6 mirroring policy plus monthly Methodology Council
  review.

## 11. Dependencies

- **00_README** — plan ID space and sign-off chain.
- *Consumed by:* every plan's `decision_log_entries` field; every
  ledger row in plan 47; every reviewer defence package in plan 50.

## 12. Out of scope

- Operational decisions about which run to schedule when; those live
  in plan 52 run orchestration.
- Personnel / authorship decisions; that belongs to the supervisor.

## 13. Open questions

- Should DEC entries be issued in pull-request form (review via PR)
  or via a dedicated review meeting? *Default: PR for entries proposed
  by codex-supervisor; meeting note for entries originating with the
  user or the supervisor.*
- Do we want a `Status: deprecated` for entries that are still
  technically valid but no longer relevant? *Default: no — supersession
  with a link is enough; deprecation is a duplicate state.*

## 14. References

- HIBEAM repository `docs/governance/DECISION_LOG.md` — structural
  template.
- ATLAS Computing CR (Change Request) workflow — comparable practice.
- Architecture Decision Records (ADR, Nygard 2011) — comparable
  practice.
