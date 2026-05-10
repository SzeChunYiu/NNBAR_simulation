---
id: 46_significance_protocol
title: Significance protocol — Z₀, expected/observed limits
version: 0.1
status: draft
owner: Analysis WG
depends_on: [00_README, 04_statistical_uncertainty, 43_signal_efficiency, 44_background_taxonomy, 45_systematics_taxonomy]
outputs:
  - {path: docs/rebuild_plans/46_significance_protocol.md, schema: this file}
acceptance:
  - {test: Z₀ definition signed in DEC, method: §1 review, pass_when: signed}
  - {test: expected and observed limit conventions named (CLs vs F-C), method: §2 review, pass_when: signed}
  - {test: finite-sample regime (zero or near-zero observed) handled by F-C explicitly, method: §3, pass_when: implemented}
risks:
  - {risk: asymptotic significance overstates Z₀ in low-stats regime, mitigation: §3 F-C handover}
estimated_effort: S
last_updated: 2026-05-09
---

# Significance protocol

*Charter.* The single-source convention for every "discovery
significance" or "limit" the rebuild quotes.

## 1. Discovery significance

Definition: asymptotic Asimov discovery formula

```
Z_0 = sqrt( 2 ((s + b) ln(1 + s/b) - s) )
```

valid for `s, b > 0` and reasonably large counts. Inputs `s` and `b`
come from plan 43 (signal efficiency) and plan 44 (background tree),
weighted by their nuisances per plan 45.

`s` is the expected selected signal count for the exposure being
quoted; `b` is the summed expected selected background count after
applying plan-44 channel rates and plan-45 nuisance weights. The
function is not evaluated for `b = 0`; those rows use §3.

Worked examples for implementation tests:

| Case | s | b | Expected `Z_0` | Use |
|---|---:|---:|---:|---|
| high-background sanity | 50 | 20 | 8.68 | asymptotic path should run |
| modest-count boundary | 10 | 6 | 3.37 | asymptotic path still allowed |
| zero-background row | 10 | 0 | n/a | must dispatch to §3 F-C |

DEC stub: `DEC-46-Z0-ASYMPTOTIC` — choose the Cowan Asimov discovery
formula above for `s > 5` and `b > 5`; require §3 F-C handover for
zero/near-zero rows. Status: draft, pending Methodology Council sign-off.

## 2. Limit conventions

Plan 46 chooses a convention; codex-supervisor implements the chosen
path. Candidates:

- **CLs** (LHC standard) via `pyhf`.
- **Feldman-Cousins** (PDG standard).

For NNBAR's near-zero-background regime, F-C is more honest in low
stats and is the recommended default. CLs is the alternative for
cross-check.

90% C.L. is the default reporting level; 95% C.L. is reported in
parallel for cross-comparison with literature.

Decision table:

| Quantity | Primary convention | Cross-check | Worked example / expected output |
|---|---|---|---|
| zero-survivor background upper limit | Feldman-Cousins 90% C.L. | none required | `n_obs=0`, `b=0`, `N=244000` gives `ε90 = 2.44 / 244000 = 1.0e-5` per plan 04 §5 |
| nonzero low-count observed limit | Feldman-Cousins unified interval | CLs only if a pyhf model exists | `n_obs=3`, `b=1.2` dispatches to F-C table/toy construction, not asymptotic Z |
| high-count expected/observed limit | CLs via `pyhf` | Feldman-Cousins spot-check | `b>5` and binned nuisance model present: report CLs 90% and 95% in the appendix |

DEC stub: `DEC-46-LIMIT-CONVENTION` — choose Feldman-Cousins as the
primary low-count and zero-survivor limit convention; use CLs as the
high-count cross-check when a pyhf model is available. Status: draft,
pending Methodology Council sign-off.

## 3. Finite-sample handover

When observed `n_obs ≤ 5` or expected `b ≤ 5`, the asymptotic Z_0
is replaced by F-C. The handover threshold is signed in DEC.

## 4. Acceptance criteria

- §1 Z_0 implemented as a function in
  `nnbar_reconstruction.statistics`.
- §2 limit convention chosen and signed.
- §3 handover implemented and tested.

## 5. Dependencies

- **04, 43, 44, 45** — inputs.
- *Consumed by:* plan 47 (ledger), plan 50 (defence package).

## 6. References

- Cowan et al., *Eur. Phys. J. C* 71 (2011) 1554 (asymptotic
  formulas).
- Feldman & Cousins (cited in plan 04).
- pyhf documentation.
