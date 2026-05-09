---
id: 21_sample_cosmic_CRY
title: Cosmic sample regeneration — CRY integration + thorough study rework
version: 0.1
status: draft
owner: Sim Production
depends_on: [00_README, 03_dataset_registry, 04_statistical_uncertainty, 12_physics_list_audit, 14_background_models, 16_geometry_and_alignment, 19_simulation_validation_suite]
inputs:
  - {path: NNBAR_Detector/macro/cosmic_macro/, schema: legacy per-species macros}
outputs:
  - {path: data/registry/cosmic_cry_essLund_*/manifest.yml, schema: registered sample}
  - {path: NNBAR_Detector/external/cry/, schema: vendored CRY library}
  - {path: NNBAR_Detector/src/generator/CRYGenerator.cc, schema: integration glue (new)}
acceptance:
  - {test: CRY library integrated and reproducible build green, method: §3 build verification, pass_when: smoke run produces non-empty cosmic primaries}
  - {test: cosmic flux at ESS Lund coordinates within 15% of CRY default at chosen date, method: §1 verification, pass_when: agreement}
  - {test: cosmic sample size derived from upper-limit target on cosmic survival, method: §4 derivation, pass_when: documented}
  - {test: every cosmic-related thesis claim (numbers + figures) is mapped to a reproducing study here, method: §5 inventory, pass_when: full coverage}
risks:
  - {risk: zero surviving cosmic events is misreported as zero rate instead of upper limit, mitigation: §4 Feldman-Cousins binding to plan 04}
  - {risk: overburden model under-shielding overestimates cosmic rate, mitigation: §2 explicit overburden treatment}
estimated_effort: L
last_updated: 2026-05-09
---

# Cosmic sample regeneration — CRY integration + thorough study rework

*Charter.* Replace the existing per-species cosmic macros (plan 10
§1.3) with a single CRY-driven cosmic generator that samples the
real atmospheric flux at ESS Lund coordinates, then rework every
cosmic-related study from the licentiate using the new sample.

The licentiate abstract claims "approximately 70% signal acceptance
with no surviving cosmic-ray background events" — this number must
be reproduced here as a Feldman-Cousins upper limit (plan 04 §5),
not as a point-estimate of zero rate.

## 1. CRY parameters

Per plan 14 §1.1:

| Parameter | Value | Source |
|---|---|---|
| Latitude | 55.7° N | ESS Lund |
| Altitude | 10 m a.s.l. | Lund site |
| Date | 2026-06-01 | provisional; user confirms |
| Solar modulation | CRY default for date | included in CRY model |
| Particles enabled | µ, e±, γ, n, p | atmospheric mixture |
| Sample box dimensions | full detector + 5 m overburden | §2 |
| Sample box top altitude | 10 m above ground | §1 latitude |

## 2. Overburden model

Real ESS detector hall has overburden (concrete ceiling, equipment).
The current simulation models *no overburden*. This is conservative
(higher cosmic rate). Plan 21 records two configurations:

- `cosmic_cry_essLund_overburdenA` (zero overburden, conservative).
- `cosmic_cry_essLund_overburdenB` (1 m concrete equivalent).

The systematic on cosmic rejection from overburden uncertainty is
the difference between A and B.

## 3. Integration

Two paths considered:

- *(a) Direct CRY → Geant4 primary generator.* New
  `src/generator/CRYGenerator.cc` reads CRY events and emits Geant4
  primaries directly.
- *(b) CRY → MCPL → Geant4 via existing G4MCPLGenerator.* Reuses
  existing MCPL infrastructure (plan 07 §10.3, §10.4); adds an
  external CRY → MCPL converter step.

**Decision.** Path (b) is preferred for the rebuild because it
preserves reproducibility (the MCPL file becomes the registered
sample input; re-runs are trivially deterministic) and reuses
proven code paths.

## 4. Sample-size derivation

The licentiate abstract reports zero surviving cosmics in a finite
sample. The PhD thesis must declare a *target* upper limit on the
cosmic survival rate, then back-compute the CRY sample size needed.

Per plan 04 §5:

```
ε_upper = 2.44 / N_generated   at 90% C.L. via Feldman-Cousins
```

For a target ε_upper = 1 × 10⁻⁵ (cosmic survival probability per
generated cosmic event), `N_generated ≥ 244 000`.

For a target ε_upper = 1 × 10⁻⁶, `N_generated ≥ 2 440 000`.

Codex-supervisor and user choose the target jointly; v0.1 documents
both options pending decision.

## 5. Cosmic-related thesis claim inventory

Codex-supervisor enumerates every cosmic claim in the licentiate
and PhD theses. v0.1 stub list:

- *Licentiate Ch 6.* Cosmic muon rate distribution; cosmic veto
  efficiency.
- *Licentiate Ch 9.* Event-shape variables for cosmics vs signal.
- *Licentiate Ch 10.* Cosmic-rejection cut-flow.
- *Licentiate abstract.* "Zero surviving cosmics in a finite sample."
- *PhD additions.* Any new cosmic claims.

Each row maps to a reproducing study under
`output/studies/cosmic_<topic>/` and a ledger row in plan 47.

## 6. Sample registry

| ID | Configuration | Statistics | Status |
|---|---|---|---|
| `cosmic_cry_essLund_overburdenA_v1` | §1 + zero overburden | 244 000 | draft |
| `cosmic_cry_essLund_overburdenB_v1` | §1 + 1 m concrete | 244 000 | draft |
| `cosmic_cry_essLund_smoke_v1` | §1 + 1 000 events | smoke | draft |

## 7. Acceptance criteria

- §1 CRY parameters frozen with DEC entry.
- §2 overburden choice documented; both A and B registered.
- §3 integration path implemented with paired DEC.
- §4 sample size derived from a target upper limit (user chooses
  target).
- §5 inventory complete; every claim has a reproducing study.

## 8. Risks

- *Risk:* CRY date choice fixes a ~10% solar-cycle uncertainty.
  *Mitigation:* plan 14 §1.4 systematic propagation.
- *Risk:* per-species legacy macros are still cited from licentiate
  text; ledger reproduction needs both old and new.
  *Mitigation:* plan 47 reproduces the old per-species rate using
  the legacy macros first (green), then adds the CRY-driven number
  as the PhD update.

## 9. Dependencies

- **04** — F-C upper limit machinery.
- **12** — `_HP` ON for cosmic-neutron physics.
- **14** — cosmic-flux background model definition.
- **16** — geometry (overburden additions).
- *Consumed by:* plans 32 (selection), 39 (background taxonomy),
  41 (significance), 47 (ledger).

## 10. References

- LLNL CRY library and documentation.
- PDG cosmic-ray review.
- ESS site geology / overburden documents (HIBEAM project).
