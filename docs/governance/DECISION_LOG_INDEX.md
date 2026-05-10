# NNBAR rebuild — decision-log index

Auto-derived from `DECISION_LOG.md`. Append-only.

| ID | Topic | Status | Plans affected | Date |
|---|---|---|---|---|
| DEC-2026-05-10-1 | CRY cosmic-flux site/date freeze | approved | 14, 21, 45 | 2026-05-10 |
| DEC-2026-05-10-2 | Beam-neutron source path: MCPL preferred + parameterised fallback | approved (provisional) | 14, 22, 44, 45 | 2026-05-10 |
| DEC-2026-05-10-3 | FTFP_BERT physics-list `_HP` split policy | approved | 03, 12, 14, 21, 22, 45, 47 | 2026-05-10 |
| DEC-2026-05-10-4 | Alignment scenario sigma grid — placeholder-with-trigger | approved (provisional) | 16, 25, 30, 45 | 2026-05-10 |
| DEC-2026-05-10-5 | TPC W-value production constant | approved | 09, 17, 18, 27, 47 | 2026-05-10 |
| DEC-2026-05-10-6 | Scintillator yield mode policy | approved (provisional) | 09, 18, 33, 47 | 2026-05-10 |
| DEC-2026-05-10-7 | Cross-repo mirror policy = live pointer | approved (provisional) | 05, 09, 13, 38, 57 | 2026-05-10 |
| DEC-2026-05-10-8 | `reconstruction.py` 500-line refactor split | approved (provisional) | 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37 | 2026-05-10 |

**Provisional approvals** were promoted to the log on 2026-05-10
without explicit per-decision user sign-off — the user delegated
DEC sign-off to the supervisor on that date. Each provisional entry
is reviewable; the user can supersede with a counter-DEC at any time.
The "(provisional)" status flips to plain "approved" upon user
ratification.

Mirror entries to HIBEAM repository (handled by DEC-2026-05-10-7):
- `DEC-2026-04-24-1` — HIBEAM, vertex truth source = converted CSV.
  Live-pointer; cited by plans 09, 13, 38.
- `DEC-2026-05-08-1` — HIBEAM, MVA inference-vs-training feature
  schema audit. Live-pointer; cited by plan 57.
