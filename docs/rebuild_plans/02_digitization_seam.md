---
id: 02_digitization_seam
title: Digitisation seam — interface for future detector realism
version: 0.1
status: draft
owner: Software Quality
depends_on: [00_README, 01_realism_contract]
inputs:
  - {path: NNBAR_Detector/output/*.parquet, schema: simulation outputs (Class A perfect today), produced_by: 07_simulation_atomic_walkthrough}
outputs:
  - {path: nnbar_reconstruction/digitization/, schema: digitisation layer interface (no-op default)}
  - {path: docs/rebuild_plans/02_digitization_seam.md, schema: this file}
acceptance:
  - {test: identity-transform layer is a no-op verified bit-for-bit, method: round-trip through digitiser with default config, pass_when: output parquet hashes match input}
  - {test: digitiser is a single-entry interface, method: only one public API, pass_when: reconstruction code never imports anything from digitisation/internal}
  - {test: every limitation in plan 01 §6 maps to a future plug-in slot, method: review against registry, pass_when: every L1–L12 has a named slot or is documented as out of scope}
risks:
  - {risk: seam drifts from contract over time as ad-hoc smearing is added inside reco, mitigation: realism audit (plan 01) treats reco-side smearing as a Class A→A transformation that must live in digitisation/}
  - {risk: digitisation parameters become un-versioned, mitigation: parameter file is required input; default lives in plan 03 dataset registry as a frozen artifact}
estimated_effort: M
last_updated: 2026-05-09
---

# Digitisation seam — interface for future detector realism

*Charter.* The current rebuild assumes a perfect detector: hit positions,
timings, and energies are exact MC truth (limitations L1–L4 in plan 01).
This is intentional — we want a clean baseline before adding realism.
But the design must reserve the slot where realism is *eventually*
inserted, so adding realism later requires only changing one layer, not
touching the reconstruction code. This plan specifies that slot.

## 1. Why a seam now, not a digitiser now

Three reasons to design the seam now even though the implementation is
identity-transform:

1. **Reconstruction code stability.** Without the seam, reco code reads
   simulation parquet directly. Adding realism later requires editing
   every reco function that references a position, time, or energy.
   With the seam, reco reads digitised parquet; the digitiser changes,
   reco does not.
2. **Audit cleanliness.** The realism audit (plan 01 §4) defines Class A
   as "what a real DAQ would produce." If the simulation writes exact
   truth into Class A columns, the contract is technically violated by
   the simulation itself. The seam reframes the simulation as the source
   and the digitiser as the producer of Class A; the simulation now
   writes a strictly larger, named *truth-bearing* schema and the
   digitiser projects it down.
3. **Parameter versioning.** A digitiser configured by an external
   parameter file forces the rebuild to register the parameter set
   under plan 03. Without the seam, "the detector is perfect" is
   never an explicit configuration choice.

## 2. The seam interface

A single Python entry-point, with a corresponding C++ entry-point
reserved for future high-throughput configurations.

```python
# nnbar_reconstruction/digitization/__init__.py
def digitise(
    input_dir: Path,           # parquet files from NNBAR_Detector/output/
    output_dir: Path,          # parquet files consumed by reconstruction
    config: DigitiserConfig,   # plug-in selection + parameters
    rng: np.random.Generator,  # seed bound by plan 03 dataset registry
) -> DigitiserReport:
    ...
```

The interface contract:

- *Input* is a directory of simulation-side parquet files (the schema
  produced by the Geant4 sensitive detectors and run-action writer).
- *Output* is a directory of parquet files with the *same column
  names* as the input but with values transformed by the configured
  plug-ins. Column dtypes are preserved.
- *Truth columns* (Class B in plan 01) pass through untouched. The
  digitiser is forbidden to modify them.
- *Calibration constants* (Class C) are *applied* in the digitiser when
  appropriate (e.g. a future smearing plug-in might use the W-value to
  scale an electron-count fluctuation).
- The digitiser is *deterministic* given a fixed RNG seed. Plan 03
  records the seed.
- The digitiser writes a side-car JSON `_digitiser_report.json` per
  output directory recording the plug-in chain, parameter set, RNG
  seed, input file hashes, output file hashes, and runtime.

## 3. The default configuration: identity transform

Until any plug-in is enabled, the digitiser is a bit-for-bit no-op:

```yaml
# default_digitiser.yml
position_smearing: identity
timing_jitter: identity
energy_noise: identity
threshold: identity
dead_channels: identity
```

The default configuration is itself an artifact registered in plan 03.
A non-default configuration creates a new dataset ID (plan 03), so
"realistic-detector samples" and "perfect-detector samples" never share
provenance.

## 4. Plug-in slots

Each slot maps onto one or more limitations from plan 01 §6. The slot
list is the authoritative seam; new slots require a plan revision.

| Slot | Closes limitation | Default | Future plug-ins |
|---|---|---|---|
| `position_smearing` | L1 | identity | Gaussian per-axis smearing with σ from detector resolution; covariance for non-isotropic resolution; per-volume σ table |
| `timing_jitter` | L2 | identity | Gaussian jitter; per-detector σ; detector-specific bias terms |
| `energy_noise` | L3 (noise component) | identity | Gaussian electronic noise; Poisson photon-statistics correction |
| `energy_threshold` | L3 (threshold) | identity | Per-channel threshold cut; threshold-shape function |
| `energy_nonlinearity` | L3 (linearity / saturation) | identity | Lead-glass saturation curve; scintillator quenching (Birks); TPC gain saturation |
| `dead_channels` | L4 | identity | Channel mask read from external CSV; hot-channel removal |
| `gain_dispersion` | L10 | identity | Per-channel gain factor sampled from a calibration table |
| `optical_photon_qe` | L12 | passes through | PMT QE curve, geometric acceptance |

Slots that close future limitations (trigger, beam structure, ageing,
B-field) are *not* in the seam; they live in plan 16 or later because
they affect the simulation, not just the readout.

## 5. Configuration discipline

The digitiser configuration is a YAML file with strict schema:

```yaml
position_smearing:
  plugin: gaussian_per_axis
  params:
    sigma_x_mm: 0.5
    sigma_y_mm: 0.5
    sigma_z_mm: 1.0
  source: <citation: detector technical note, version, date>
timing_jitter:
  plugin: gaussian
  params:
    sigma_ns: 1.0
  source: <citation>
...
```

Every plug-in entry has:

- `plugin` — a registered name resolvable by the digitiser.
- `params` — plug-in-specific parameters.
- `source` — citation to the calibration source (plan 18 intercalibration,
  test-beam note, vendor data sheet). Cannot be empty.

Codex-supervisor blocks runs whose configuration does not pass schema
validation.

## 6. Realism upgrade gate (concrete)

A plug-in moves from `identity` to a real implementation only when:

1. Plan 18 (intercalibration) or a comparable source provides the
   calibration value with a propagated uncertainty (plan 04).
2. A decision-log entry (plan 05) records the upgrade, citing the source
   and the supersession of the identity default.
3. A side-by-side study compares `default_digitiser` vs. the new
   plug-in on a frozen sample (plan 03), measuring the impact on
   every observable in plan 38 truth-substitution ladder.
4. The reviewer-defence package (plan 50) for any result quoted under
   the new digitiser includes a digitisation-sensitivity bracket
   computed against the identity default.

The upgrade is not all-or-nothing: position smearing can land while
timing remains identity, etc. Each slot upgrades independently with
its own gate.

## 7. Where the seam sits in the pipeline

```
NNBAR_Detector/output/*.parquet           ← simulation, perfect detector
                │
                ▼
        digitise(..., config=default_digitiser)
                │
                ▼
NNBAR_Detector/digitised/<dataset_id>/*.parquet     ← consumed by reco
                │
                ▼
          reconstruction
```

In identity mode, `NNBAR_Detector/output/` and
`NNBAR_Detector/digitised/<default-id>/` are content-equivalent; the
hash side-car proves it.

When a realistic configuration is chosen, the digitised directory has a
different dataset ID and different hashes. Plan 03 enforces ID
uniqueness.

## 8. Acceptance criteria

- A skeleton digitisation layer exists at
  `nnbar_reconstruction/digitization/` with the entry-point in §2.
- The default identity configuration produces parquet outputs whose
  per-file SHA-256 matches the input, for every sample in plan 20.
- Every slot in §4 has either a real plug-in registered or a
  named identity stub; no slot is missing.
- The digitiser configuration is a registered artifact in plan 03.
- A worked example in `tests/test_digitiser_identity.py` confirms the
  bit-for-bit guarantee on a small representative sample.
- The realism audit (plan 01 §4) reads digitised parquet, not raw
  simulation parquet, by default. Reading raw parquet outside the
  digitiser is treated as an audit warning.

## 9. Risks and mitigations

- *Risk:* the seam adds disk-and-runtime cost for no scientific benefit
  while it remains identity.
  *Mitigation:* the identity plug-in writes via filesystem hardlink
  when the input/output filesystem supports it, falling back to copy
  only when hardlink fails. Runtime is O(linking the directory).
- *Risk:* developers add ad-hoc smearing inside reconstruction
  ("just for this study") to bypass the seam.
  *Mitigation:* plan 53 CI fails the realism audit when reco code
  contains randomness modules (`numpy.random.*`, `random.*`) outside
  marked decorators.
- *Risk:* configuration sprawl — every study lays down its own digitiser
  configuration, fracturing reproducibility.
  *Mitigation:* plan 03 limits the canonical configuration set; ad-hoc
  configurations live in `output/studies/<id>/digitiser_config.yml` and
  are not promoted to thesis numbers without plan-03 registration.

## 10. Dependencies

- **01_realism_contract** — defines Class A/B/C; the seam is the
  technical mechanism that makes Class A meaningful.
- **03_dataset_registry** — registers the digitiser configuration as
  a versioned artifact.
- *Consumed by:* every reco-side plan that reads parquet inputs;
  plan 50 reviewer defence package; plan 53 CI.

## 11. Out of scope

- Implementing any non-identity plug-in. Plug-in implementations are
  separate plan revisions made when the upgrade gate (§6) opens for
  that slot.
- Modelling the trigger, DAQ, beam structure, ageing, or B-field. These
  are simulation-side, not digitiser-side.

## 12. Open questions

- Does the user want the seam to operate on a streaming Arrow record
  batch (lower memory) or in pandas dataframes (simpler code)? *Default:
  pyarrow record batch; reco code already uses pyarrow.*
- Should the digitiser also produce a paired truth-table side-car
  (e.g. `*_truth.parquet`) so validation code reads truth from a
  separate file rather than the same file? *Default: yes, eventually,
  because it makes the realism audit trivial. For v0.1, share the
  parquet to avoid duplicating disk.*

## 13. References

- ALICE TPC ZeroSuppression / digitisation pipeline as a structural
  reference (cited in plan 48 prior-art survey).
- ATLAS/CMS digitisation modularisation (`G4Sim → Digi → Reco` chain)
  as the design precedent.
