# Reconstruction cutflow baseline for `pi0_mono_150mev`

## Scope

Pane 2 / worker-2 picked up the `reco-cutflow-baseline` item from
`codex-tasks/recon/worker-4.txt` as an in-scope Python/analysis lane swap. This
iteration is read-only with respect to reconstruction code: no Python module,
C++, macro, SLURM script, production sample, or LUNARC job was changed or run.

The queued baseline was written before the cluster seed-threshold fix landed.
The current default reconstruction is already fixed, so this report preserves
the requested pre-fix baseline by explicitly calling `cluster_neutral_hits` with
`seed_min_energy=10.0` and `cluster_min_energy=10.0`. A post-fix default check is
reported separately so the baseline is not confused with the current code path.

## Inputs

| Input | Rows | Event accounting |
|---|---:|---:|
| `build_lunarc/output/pi0_mono_150mev/Particle_output_0.parquet` | 200 | 200 unique `Event_ID` values |
| `build_lunarc/output/pi0_mono_150mev/LeadGlass_output_0.parquet` | 772,193 | 200 unique `Event_ID` values |
| `build_lunarc/output/pi0_mono_150mev/Scintillator_output_0.parquet` | 96,133 | Scintillator hits joined by `Event_ID` |

Fractions below use the 200 particle events as the denominator. The vertex was
`np.zeros(3)`, matching the mono-sample reconstruction driver default for this
origin sample.

## Required cutflow table

| Stage | Cut | n_pass | fraction |
|---:|---|---:|---:|
| 0 | Total events in `Particle_output_0.parquet` | 200 | 100.0% |
| 1 | Has LeadGlass hits | 200 | 100.0% |
| 2a | Per-event max LeadGlass `eDep > 10.0` MeV | 0 | 0.0% |
| 2b | Per-event max LeadGlass `eDep > 0.1` MeV | 198 | 99.0% |
| 3 | `>=1` neutral object with legacy seed threshold | 4 | 2.0% |
| 4 | `>=1` pi0 candidate with legacy seed threshold | 0 | 0.0% |

## Diagnostics

- The largest single LeadGlass step in the full sample is 9.988 MeV, so no event
  can start from a LeadGlass seed under the old 10 MeV seed-hit threshold.
- The median per-event maximum LeadGlass step is 4.069 MeV; the minimum is
  0.049 MeV.
- The two events failing the proposed 0.1 MeV LeadGlass seed threshold are
  `Event_ID` 194 and 196.
- Stage 3 is not exactly zero over all 200 events because four events
  (`Event_ID` 36, 41, 51, and 135) contain a Scintillator step above 10 MeV.
  Each creates one legacy neutral object, but none forms a pi0 candidate.
- The first 20 events reproduce the pre-fix verification symptom exactly:
  zero legacy neutral-object events and zero legacy pi0 candidates.

## Current default cross-check after the seed fix

The current default path (`reconstruct_neutral_objects` followed by
`find_pi0_candidates`) no longer corresponds to the broken baseline. On the same
200 events it gives:

| Current default metric | Count | Fraction / total |
|---|---:|---:|
| Events with `>=1` neutral object | 197 | 98.5% |
| Events with `>=1` pi0 candidate | 104 | 52.0% |
| Total neutral objects | 350 | 1.75 per event |
| Total pi0 candidates | 104 | 0.52 per event |

Event-level current neutral-object counts are `{0: 3, 1: 44, 2: 153}`. Current
pi0-candidate counts are `{0: 96, 1: 104}`.

## Interpretation

The requested baseline confirms the root-cause diagnosis: the old 10 MeV
seed-hit threshold is above every LeadGlass single-step deposit in this sample,
so LeadGlass-driven photon clustering cannot start. Rare Scintillator-only seeds
produce four neutral objects across the full 200-event sample, but they do not
recover any pi0 candidates. The already-merged seed fix changes the default
reconstruction behavior substantially, yielding nonzero neutral objects in
197/200 events and pi0 candidates in 104/200 events on this local sample.

## Verification

Commands run locally from `/Volumes/MyDrive/nnbar/nnbar/simulation`:

```bash
rtk proxy ls -lh build_lunarc/output/pi0_mono_150mev/Particle_output_0.parquet \
  build_lunarc/output/pi0_mono_150mev/LeadGlass_output_0.parquet \
  build_lunarc/output/pi0_mono_150mev/Scintillator_output_0.parquet
rtk proxy python - <<PY
# pandas/numpy aggregation over Event_ID; direct calls to cluster_neutral_hits,
# reconstruct_neutral_objects, and find_pi0_candidates generated this report.
PY
rtk proxy grep -nE "^(def|class) (cluster_neutral_hits|reconstruct_neutral_objects|find_pi0_candidates)" \
  nnbar_reconstruction/reconstruction/neutral_reconstruction.py
rtk proxy wc -l docs/reports/reco_cutflow_baseline.md
```

Observed verification on 2026-05-12: the report-number verifier printed
`RECO_CUTFLOW_BASELINE_OK n_events=200 legacy_neutral=4 legacy_pi0=0
current_neutral=197 current_pi0=104`; the queue validator scanned 27 files and
32 prompt lines with 0 failures; the worker pytest command reported 259 passed
and 2 skipped.
