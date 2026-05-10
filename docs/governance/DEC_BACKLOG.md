# DEC backlog — sign-off log

This file is the historical record of DEC-stub sign-off rounds.
Active stubs (when present) live above the divider; promoted entries
are summarised below.

Last refreshed: 2026-05-10.

---

## Active backlog: 0 stubs

All known DEC stubs have been promoted to `DECISION_LOG.md`. New
stubs added to plan bodies will queue here until the next sign-off
round.

---

## Round-1 sign-off (2026-05-10)

The user delegated DEC sign-off to the supervisor in the
2026-05-10 "do whatever is missing, you don't need to ask me"
directive. The following 5 stubs were promoted using their plan-body
draft recommendations:

| ID | Topic | Plan source | Notes |
|---|---|---|---|
| DEC-2026-05-10-2 | Beam-neutron source path | 14 §2.1, 22 | MCPL preferred when available; parameterised fallback with `model_only=true` tag. Re-promote when ESS team delivers MCPL file. |
| DEC-2026-05-10-4 | Alignment scenario sigma grid | 16 §2 | Placeholder-with-trigger: 3 named scenarios at engineering-prior σ. Re-promote when ESS detector survey lands. |
| DEC-2026-05-10-6 | Scintillator yield mode policy | 18 §3 | 11136 photons/MeV (fast mode) and 10000 photons/MeV (optical mode); explicit 1.1136× scale at comparison. |
| DEC-2026-05-10-7 | Cross-repo mirror policy | 05 §6 | Live-pointer to HIBEAM repository; monthly methodology-council drift review. |
| DEC-2026-05-10-8 | `reconstruction.py` 500-line refactor split | refactor plan | Per-subsystem module split landed; shim retained 2 weeks then removed. |

Plus 3 already-promoted (initial round):
- DEC-2026-05-10-1 (CRY freeze)
- DEC-2026-05-10-3 (FTFP_BERT `_HP` split)
- DEC-2026-05-10-5 (TPC W=23.6 eV)

All 8 entries carry `Status: approved` (the 5 from the second round
are flagged "provisional auto-approval" — reviewable; user may
supersede with a counter-DEC).

---

## Pre-thesis ratification gate

Before thesis submission, the user is expected to:
1. Read `DECISION_LOG.md` end-to-end.
2. For each `provisional` entry, either ratify (flip to plain
   `approved`) or open a counter-DEC.
3. Confirm the cross-repo mirror status against the HIBEAM repo.

This is a single pre-defense pass, not a per-DEC interaction.
