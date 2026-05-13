# NNBAR / G4GPU Acceleration Paper — Methodology Specification

**Purpose:** This document defines the academic standard every result in this
project must meet before it is cited in a paper or thesis. It covers the
Geant4 acceleration study (G4GPU), the NNBAR simulation validation, and the
reconstruction chain closure. Every codex lane must read this before claiming
a result "done".

---

## Target journals

| Priority | Journal | Scope |
|---|---|---|
| 1 | *Computer Physics Communications* (Elsevier) | HEP software, simulation frameworks |
| 2 | *Journal of Computational Physics* (Elsevier) | Algorithms, numerical methods, GPU computing |
| 3 | *Nuclear Instruments and Methods A* (Elsevier) | Detector simulation and instrumentation |
| 4 | *SoftwareX* (Elsevier) | Reproducible software artifacts |

Primary target is **Comput. Phys. Commun.** — it is the canonical venue for
Geant4-related algorithmic papers (Agostinelli 2003, Allison 2006/2016) and
carries the highest community impact for this work.

---

## Claim taxonomy

Every result must be tagged with one of these claim levels before publication.

| Level | Label | Required evidence |
|---|---|---|
| L0 | **Scaffold** | Code compiles, unit tests pass; no physics or performance claim |
| L1 | **Predicted** | Literature-backed estimate; no measured data; labelled `OPEN:` in reports |
| L2 | **Measured-local** | Measured on one hardware configuration; reproducible with pinned seeds |
| L3 | **Measured-matrix** | Measured on ≥2 CPU microarchitectures AND ≥1 GPU; parity gate passed |
| L4 | **Verified-published** | Independent reproduction by a second person or CI job on different hardware |

No result below **L3** may appear in a paper's results table. L1 predictions
may appear in a "motivation" section only if clearly labelled as estimates.

---

## Benchmark workload matrix

All performance measurements must be taken on this fixed workload set.
Adding workloads requires a MASTER_PLAN entry and a new harness row schema
extension — do not add ad-hoc workloads.

| ID | Workload | Geant4 example | Events | Physics list(s) | Primary observable |
|---|---|---|---|---|---|
| W1 | EM calorimeter (minimal) | TestEm0 | 10 000 | FTFP_BERT, QGSP_BIC | Steps/event, dE/dx mean |
| W2 | EM calorimeter (full scoring) | TestEm3 | 10 000 | FTFP_BERT, QGSP_BIC | Edep profile, step count |
| W3 | Hadronic shower | Hadr01 | 5 000 | FTFP_BERT, QGSP_BIC, Shielding | Secondary multiplicity, Edep |
| W4 | Hadronic + neutron HP | Hadr04 | 2 000 | FTFP_BERT_HP, Shielding_HP | Neutron capture rate, time |
| W5 | NNBAR full event (signal) | NNBAR macro | 1 000 | FTFP_BERT | All detector Parquet outputs |
| W6 | NNBAR full event (cosmic µ) | NNBAR macro | 500 | FTFP_BERT | TPC hits, scintillator Edep |

---

## Physics-list matrix

All optimizations must be tested against at least W1+W2 with both lists in
the table below. An optimization that degrades one physics list is **not
publishable** as a win.

| ID | List | Notes |
|---|---|---|
| PL1 | FTFP_BERT | Primary NNBAR production list |
| PL2 | QGSP_BIC | Standard hadronic alternative |
| PL3 | Shielding | Neutron transport / medical physics |
| PL4 | FTFP_BERT_HP | High-precision neutron (required for beam background) |

---

## Hardware matrix

Minimum required before a result is L3:

| ID | Machine | CPU | GPU | CUDA | Notes |
|---|---|---|---|---|---|
| H1 | LUNARC Aurora (gpua40) | AMD EPYC Milan | NVIDIA A40 | 12.8 | Primary GPU node |
| H2 | LUNARC Aurora (gpua100) | AMD EPYC Milan | NVIDIA A100 80 GB | 12.8 | High-memory GPU |
| H3 | LUNARC Aurora (lu48) | AMD EPYC Milan (48c) | — | — | CPU baseline |
| H4 | Local (Intel) | Intel Core (any ≥4c) | — | — | Second CPU microarch |

CPU-only optimizations require H3 + H4 for L3. GPU offload optimizations
require H1 + H2.

---

## Parity gate (physics correctness)

**Every optimization that changes a physics computation must pass the parity
gate before its speedup is reported.** The gate is a hard blocker — not a
warning.

### Gate procedure

For each (optimization, workload W1--W6, physics list PL1--PL4):

1. Run vanilla Geant4 (unmodified v11.2.2) with N=20 seeds, record per-event
   observables: `Edep_total`, `step_count`, `secondary_multiplicity`,
   `first_step_length`, `neutron_capture_rate` (W4 only).
2. Run optimized build with the same N=20 seeds.
3. Apply two-sample Kolmogorov-Smirnov test to each observable distribution.
4. **Pass criterion:** KS p-value > 0.05 for all observables in all workloads.
5. If any observable fails: the optimization is tagged `PARITY_FAIL` in the
   harness output row and must not be promoted to L3.

### Reference dataset pinning

- Vanilla reference runs are stored as Parquet in
  `benchmarks/reference/<workload>/<physics_list>/seed_<N>.parquet`.
- Reference dataset is version-pinned with a SHA-256 manifest at
  `benchmarks/reference/MANIFEST.sha256`.
- Any re-generation of the reference requires a MASTER_PLAN entry and a
  planner sign-off comment in that entry.

---

## Statistical power

- N=20 runs per configuration for KS test and speedup mean ± σ.
- Report 95% confidence interval on speedup: `mean ± 1.96σ/√N`.
- A speedup is only reported if the lower bound of the CI exceeds 1.00
  (i.e., improvement is statistically significant at 95% CL).
- Negative results (optimization slows things down) must be reported with the
  same CI and tagged `REGRESSION` in the harness row — they are not discarded.

---

## Negative-results policy

Negative results are first-class outputs. An optimization that:
- passes parity but shows speedup CI lower bound < 1.0: reported as `NEUTRAL`
- passes parity but shows CI upper bound < 1.0: reported as `REGRESSION` and
  included in the paper as a cautionary data point
- fails parity: reported as `PARITY_FAIL` with the failing observable named

All three categories appear in Supplementary Table S1. This is non-negotiable
for Comput. Phys. Commun. reproducibility standards.

---

## Reproducibility requirements

Every result table row must have:

1. **Pinned Geant4 version:** `v11.2.2`, git tag `geant4-11.2.2`.
2. **Pinned seed set:** the 20 seeds used, stored in the harness Parquet row.
3. **Pinned hardware spec:** SLURM job ID + `scontrol show job` output saved
   to `benchmarks/hardware_evidence/<jobid>.txt`.
4. **Singularity/container image hash** for the build environment (or a
   verbatim `module load` + cmake configure log committed to
   `benchmarks/build_logs/<opt_id>_<hardware_id>.txt`).
5. **Git commit hash** of the G4GPU branch used, stored in the harness row.

---

## Paper structure (target outline)

1. Introduction — motivation, related work (Celeritas, AdePT, Opticks, VecGeom)
2. Geant4 hot-path analysis — the 50-entry bottleneck database methodology
3. G4GPU framework design — architecture, isolation policy, backend abstraction
4. Optimization catalogue — one subsection per BD cluster:
   - 4.1 PostStep GPIL dispatch (BD-032/034/035)
   - 4.2 Lambda table caching (BD-036/037/038/039/040)
   - 4.3 Geometry navigation: voxel SIMD (BD-042–049)
   - 4.4 RTX geometry backend (Phase 3)
   - 4.5 GPU particle offload (Phase 1/2 + EM gamma kernel)
5. Benchmark results — harness output tables, hardware matrix, CI plots
6. Physics parity — KS-test results for all workload × physics-list combinations
7. Comparison with Celeritas / AdePT / Opticks
8. Application to NNBAR detector simulation — wall-clock improvement on W5/W6
9. Conclusion and future work (Phase 6 SoA, Phase 7 tri-compute, differentiable)

---

## Gap-finding protocol for validator/planner

The validator/planner meta lane must check these questions every iteration:

1. Is every RUNNING lane producing L2+ evidence, or is it stuck on L1 predictions?
2. Are there observables in the benchmark workload matrix not yet covered by
   harness rows? → file a NEXT task.
3. Are there physics-list / hardware combinations in the matrix with no
   reference dataset? → queue reference generation sbatch.
4. Does the latest git log introduce a new result not yet in the harness? → queue
   a harness run for that result.
5. Are there thesis claims (reproduction ledger rows) with no corresponding
   simulation sample? → queue sample generation.
6. Are there open `OPEN:` markers in any report that have been unresolved for
   > 2 iterations? → escalate to planner queue with a bounded resolution task.
7. Is the paper outline (§ above) missing a section that the current evidence
   would support? → write the section spec.

This loop runs until every BD entry has an L3 harness row, every thesis claim
has a verified sample, and every paper section has supporting evidence.

---

## Milestone gates before submission

- [ ] All 50 BD entries have harness rows (L2 minimum, L3 for paper table)
- [ ] KS parity gate passed for all L3 rows
- [ ] Hardware matrix complete: H1+H3+H4 for CPU wins; H1+H2 for GPU
- [ ] Celeritas and AdePT baselines measured (or blocker explicitly documented
      with evidence in Supplementary)
- [ ] Thesis reproduction ledger: ≥90% of rows unblocked (verified samples)
- [ ] NNBAR W5/W6 end-to-end speedup measured with full cosmic + signal samples
- [ ] All `OPEN:` markers in `docs/reports/` resolved or explicitly deferred with
      a reference to a follow-up paper
- [ ] Figure and table captions written (no placeholder text)
- [ ] All references have DOI and year

No submission until all boxes are checked.
