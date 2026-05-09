---
id: 06_governance_and_review
title: Governance and review — working groups, gates, cadence
version: 0.1
status: draft
owner: Methodology Council + Software Quality (joint)
depends_on: [00_README, 05_decision_log]
inputs: []
outputs:
  - {path: docs/governance/CHARTERS.md, schema: per-WG charter}
  - {path: docs/governance/REVIEW_GATES.md, schema: review matrix + escalation}
  - {path: docs/governance/MEETING_LOG.md, schema: meeting notes archive}
acceptance:
  - {test: every plan has an owning WG and a review WG named, method: YAML header check, pass_when: all 58 plans complete}
  - {test: every PR or plan revision passes the gate stated in §3, method: review log audit, pass_when: zero merges without paired review}
  - {test: meeting cadence sustained for 8 consecutive weeks, method: meeting log timestamps, pass_when: gaps ≤ 2 weeks}
risks:
  - {risk: small team treats role separation as bureaucracy and skips gates, mitigation: §6 escalation makes gate skipping visible}
  - {risk: plan reviews accumulate faster than the council can process, mitigation: §3 single-reviewer fast path for low-impact changes}
estimated_effort: S
last_updated: 2026-05-09
---

# Governance and review

*Charter.* This plan defines the working-group structure, review gates,
sign-off chain, escalation protocol, and meeting cadence that keep the
rebuild defensible. The user is the human in the loop; codex-supervisor
is the executing agent; supervisors are the formal sign-off authority.
The plan makes those roles explicit so the small team operating with
formal-collaboration discipline does not regress to "whoever has the
keyboard decides."

## 1. Working groups (recap from 00_README §3)

Working groups, charters, and plan ownership are defined in 00_README
§3 and §4. This plan repeats only the *structural* points and adds the
operational rules.

Each WG has:
- a *charter paragraph* (template in 00_README §3.2),
- an *owned plan list* (00_README §3.1),
- a *primary sign-off authority* (00_README §6),
- a *review queue* in `docs/governance/REVIEW_QUEUE.md` updated by
  codex-supervisor,
- a *meeting cadence* (§5).

Membership is the user, codex-supervisor agents, and (for sign-off)
the academic supervisors. A single human may rotate through several
WGs; the role separation is by *artifact authorship and review*, not
by personnel.

## 2. Drafting authority

Within a WG, drafting authority defaults to the WG owner. Codex-
supervisor drafts plan revisions when:

- a CI signal demands a revision (plan 53),
- a downstream plan reveals a missing input,
- the user requests a revision in conversation,

and proposes the revision via the §3 review path. Codex-supervisor does
not unilaterally approve its own drafts.

## 3. Review gates

There are three review classes. Every change selects exactly one.

### 3.1 Single-reviewer (low-impact)

Conditions:
- The change is to a plan whose `status` is `draft` or `review`.
- It does not alter the YAML header fields `id`, `depends_on`, `inputs`,
  `outputs`, `acceptance`, `risks`.
- It does not contradict an approved DEC entry (plan 05).
- It does not affect any frozen sample (plan 03).

Reviewers: any non-author member of the owning WG, plus the
Methodology Council if the WG owner is the Council itself.

### 3.2 Two-reviewer (standard)

Conditions:
- Default for any change that does not qualify for single-reviewer.
- Always required for changes to a `signed` plan (which immediately
  flips its status to `review`; see plan 00 §8).

Reviewers: one from the owning WG, one from the review WG named in
00_README §6.

### 3.3 Council-and-supervisor (load-bearing)

Conditions:
- Any change to a foundational plan (00–06).
- Any change that closes a plan-01 limitation.
- Any change to the dataset registry's freeze policy or the realism
  contract's audit rules.
- Any change that retires a frozen sample.

Reviewers: full Methodology Council convenes; supervisor sign-off
required.

## 4. Sign-off chain

```
draft  ──→  review  ──→  signed (codex-supervisor may execute)
                ▲
                │
   plan revision restarts review cycle
```

The transitions:

- `draft → review`: any author, by submitting the plan or revision for
  review.
- `review → draft`: any reviewer, by rejection with rationale logged
  in the review queue.
- `review → signed`: the appropriate authority per §3 and 00_README §6.
- `signed → review`: any reviewer, when starting a revision.
- `signed → superseded`: when a successor plan is signed; bidirectional
  link required.

Codex-supervisor reads `status` from each plan's YAML header. It
refuses to execute against `status: draft` or `status: review`.

## 5. Meeting cadence

Three regular meetings, plus ad-hoc:

| Meeting | Cadence | Attendees | Output |
|---|---|---|---|
| **Stand-up** | Weekly, 30 min | User + codex-supervisor (proxy in writing) | Status update, blocker triage, plan-status changes |
| **POG/CP review** | Bi-weekly, 60 min | One WG at a time, rotating | Plan-revision review, DEC drafting |
| **Methodology Council** | Monthly, 90 min | Council + user; supervisor invited | Sign-off on `review`-state plans, cross-WG conflict resolution |
| **Thesis prep** | Quarterly | User + supervisor | Reproduction-ledger review (plan 47), reviewer-question registry triage (plan 51) |
| **Ad-hoc** | As needed | Affected WGs | Time-sensitive decisions; logged in DEC if methodology |

Meeting notes live in `docs/governance/MEETING_LOG.md` and follow a
fixed format: date, attendees, agenda, decisions (with DEC IDs if
applicable), action items with owners.

For practical operation: when the user signals a strategic direction
in conversation (as has happened multiple times in this rebuild's
opening session), codex-supervisor logs the conversation as an ad-hoc
meeting note with the user's message verbatim under "decisions."

## 6. Escalation protocol

- *Disagreement between two WGs:* escalate to Methodology Council at
  the next monthly meeting; record the conflict as a draft DEC entry.
- *Disagreement between a WG and the Methodology Council:* escalate
  to the supervisor; document on the next quarterly thesis-prep agenda.
- *Disagreement between codex-supervisor and the user:* the user wins
  by default; codex-supervisor proposes the disagreement as a DEC
  draft with both options enumerated, the user chooses, the entry is
  approved.
- *Disagreement between this rebuild and the HIBEAM repository:* the
  Methodology Council coordinates with the HIBEAM lead; the resolution
  is mirrored into both decision logs (plan 05 §6).

A WG that wants to override an escalation must do so via a new DEC
entry; the override path is never silent.

## 7. Plan revision workflow

(Concrete operational form of 00_README §8.)

1. *Open a revision.* Author edits the plan file, bumps `version`,
   sets `status: review`, drafts a corresponding DEC entry if
   methodology changes (plan 05).
2. *Add to review queue.* Author appends an entry to
   `docs/governance/REVIEW_QUEUE.md`:
   `[<plan_id> v<old>→v<new>] <one-line summary>  ← <author>`
3. *Reviewer claims.* The reviewer assigns themselves in the queue
   and posts comments inline in the plan file (suggestion blocks) or
   in the meeting notes.
4. *Author addresses.* The author resolves comments in a new commit
   on the same revision branch.
5. *Sign-off.* Per §3 and §4. The reviewer flips `status` to
   `signed` (single-reviewer / two-reviewer) or escalates to Council
   (load-bearing).
6. *Close out.* The DEC entry, if any, is approved on the same step.
   Codex-supervisor regenerates the status board in 00_README §9.

## 8. Codex-supervisor instructions to itself

These are operational rules codex-supervisor follows without further
prompting:

- Before executing any plan, verify `status: signed`. Refuse otherwise.
- Before quoting any number in the ledger or a defence package, verify
  the underlying sample's registry status is `frozen`.
- Before opening a methodology change, draft both the plan revision
  and the DEC entry together, in one commit.
- Refuse to merge a PR that introduces a methodology change without a
  paired DEC entry.
- Refuse to merge a PR that breaks the realism audit (plan 01) or the
  registry integrity check (plan 03).
- Treat user direct instructions as the highest authority; if they
  conflict with a signed plan, propose the plan revision before
  executing.

## 9. Acceptance criteria

- `docs/governance/CHARTERS.md` exists, derived from 00_README §3.
- `docs/governance/REVIEW_GATES.md` codifies §3 of this plan.
- `docs/governance/REVIEW_QUEUE.md` and `MEETING_LOG.md` exist as
  living documents.
- The first three meeting notes are written.
- The first three DEC entries from plan 05 are present.
- Plan 53 CI checks the YAML headers of all 58 plans for owning WG /
  review WG completeness.

## 10. Risks and mitigations

- *Risk:* governance overhead chokes a small team.
  *Mitigation:* §3.1 single-reviewer fast path; ad-hoc meetings logged
  rather than scheduled.
- *Risk:* the user implicitly bypasses the council by giving
  codex-supervisor a direct order, which then becomes the de-facto
  decision without a DEC entry.
  *Mitigation:* §8 codex-supervisor logs every direct instruction as a
  DEC draft for council ratification at the next monthly meeting.
- *Risk:* meeting cadence collapses under thesis-writing crunch.
  *Mitigation:* §5 thesis-prep meeting takes priority over POG/CP at
  the cost of WG-level review depth. Stand-up is mandatory; everything
  else is suspendable up to two weeks before a thesis-prep meeting
  reset.

## 11. Dependencies

- **00_README** — defines plan ID space, working groups, sign-off
  matrix.
- **05_decision_log** — paired with this plan; sign-off events generate
  DEC entries.
- *Consumed by:* every plan (every plan's `status` and ownership flow
  through this plan's gates).

## 12. Out of scope

- Personnel decisions, authorship, contributorship.
- IT infrastructure choices (those flow through plan 52 run
  orchestration and plan 53 CI).
- Real-collaboration governance (HIBEAM/NNBAR collaboration MOUs etc.)
  beyond what plan 05 §6 mirroring covers.

## 13. Open questions

- Should weekly stand-up output be a written digest the user reads, or
  a live conversation? *Default: written digest from codex-supervisor;
  user reads asynchronously and replies as needed.*
- Should supervisor sign-off be required quarterly even when no
  load-bearing plan is open for review? *Default: yes — confirms
  supervisor visibility on the rebuild's overall status.*
- How to bootstrap the initial sign-off when the WGs are nascent and
  the Methodology Council is essentially the user? *Default: the user
  signs off the foundational plans (00–11) as Council; codex-supervisor
  proposes Council membership expansion at thesis-prep meetings.*

## 14. References

- ATLAS POG/CP/Analysis-WG operational structure (public ATLAS Computing
  Note ATL-COM-COMP-2014-XXX, structural reference).
- CMS PAGs/POGs documentation (structural reference).
- LHCb Working Group Convener handbook (cadence reference).
