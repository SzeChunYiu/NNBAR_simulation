---
id: 03_dataset_registry
title: Dataset registry — sample provenance schema
version: 0.1
status: draft
owner: Sim Production
depends_on: [00_README, 01_realism_contract, 02_digitization_seam]
inputs:
  - {path: NNBAR_Detector/output/, schema: simulation outputs}
  - {path: nnbar_reconstruction/digitization/configs/, schema: digitiser configs}
outputs:
  - {path: data/registry/datasets.yml, schema: registry index}
  - {path: data/registry/<dataset_id>/manifest.yml, schema: per-sample manifest}
  - {path: tests/test_registry_integrity.py, schema: hash + schema integrity test}
acceptance:
  - {test: every sample referenced in any plan resolves to a registry entry, method: cross-reference scan, pass_when: zero unresolved IDs}
  - {test: every frozen sample has matching hashes on disk, method: SHA-256 verification, pass_when: zero hash mismatches}
  - {test: registry is append-only for frozen samples, method: git history check, pass_when: no in-place edit of frozen entries}
risks:
  - {risk: hash drift on shared filesystems, mitigation: hash verification runs in CI weekly + on every plan reference}
  - {risk: storage cost balloons with sample variants, mitigation: plan 54 archival policy retires samples per retention table}
estimated_effort: M
last_updated: 2026-05-09
---

# Dataset registry — sample provenance schema

*Charter.* This plan defines the registry that maps every simulated
sample to its complete provenance: who produced it, with what command,
on what code version, with what physics list, against what geometry,
with what digitiser configuration, with what RNG seeds, what its
files hash to, what its expected schema is. Every plan that quotes a
number against a sample resolves the sample through the registry. No
sample is "the signal sample" or "the cosmic sample" without an ID.

## 1. Why the registry

Without the registry, "we ran the reconstruction on the signal sample"
is unprovable in three months. With the registry, "we ran reconstruction
v0.7 on dataset `sig_foil_500MeV_v3`" resolves to:

- the exact Geant4 command line
- the exact macro file
- the Geant4 version, physics list, and geometry hash
- the digitiser configuration ID (plan 02)
- the RNG seed
- the per-file SHA-256 manifest

This is the artifact that the HIBEAM reproducibility appendix already
gestures at (`DEC-2026-04-24-1` referencing dataset IDs). We make it
load-bearing.

## 2. Registry layout

```
data/
└── registry/
    ├── datasets.yml                 # top-level index: ID → manifest path
    ├── <dataset_id>/
    │   ├── manifest.yml             # the registry entry
    │   ├── command.sh               # exact reproducer (auto-generated)
    │   ├── geant4_environment.txt   # `geant4-config --version`, libs, macros
    │   └── hashes.txt               # SHA-256 per file, sorted
    └── ...
```

The actual sample parquet files live under `NNBAR_Detector/output/` or
`NNBAR_Detector/digitised/<dataset_id>/` — not inside `data/registry/`.
The registry is metadata only. This keeps the registry small and
git-friendly.

## 3. Manifest schema

Every `data/registry/<dataset_id>/manifest.yml`:

```yaml
id: sig_foil_500MeV_v3
human_label: "n̄ → multi-pi annihilation, foil origin, 500 MeV cap, signal v3"
status: draft | review | frozen | superseded | retired
supersedes: <prior id or null>

generator:
  type: signal | cosmic | beam_neutron | calibration_single_particle
  primary_macro: macro/studies/pi0_foil_500mev.mac
  command: ./nnbar-detector-simulation -m macro/studies/pi0_foil_500mev.mac
  primary_seed: 42
  events_requested: 10000
  events_produced: 9987     # filled after the run

simulation:
  geant4_version: "11.2.1"
  physics_list: FTFP_BERT_HP
  geometry_hash: <sha256 of compiled geometry>
  build_id: <build dir name + git rev>
  optical_photons: enabled | disabled
  gpu_paths: tpc_drift+optical | cpu_only

digitiser:
  config_id: default_identity_v1
  config_hash: <sha256 of the YAML>
  rng_seed: 1337

outputs:
  base_path: NNBAR_Detector/output/<run-id-pattern>
  files:
    - {name: TPC_output_0.parquet,             rows: 12345, sha256: <hex>}
    - {name: Scintillator_output_0.parquet,    rows: 9876,  sha256: <hex>}
    - ...
  total_size_bytes: <int>

schema_version: 09_io_schema_data_dictionary@v0.1
realism_class: A | A+C | A+B (B for diagnostic-only samples)

provenance:
  produced_by: <user, machine, slurm job id, date>
  produced_on: 2026-05-09T14:32:11Z

retention:
  policy: thesis_freeze | working_copy | retired
  retire_after: <ISO date>

decision_log_entries: [DEC-2026-05-09-1, ...]
```

## 4. Registry index

`data/registry/datasets.yml` is the top-level index. It contains one
line per registered dataset:

```yaml
datasets:
  - {id: sig_foil_500MeV_v1,                status: superseded, manifest: sig_foil_500MeV_v1/manifest.yml}
  - {id: sig_foil_500MeV_v2,                status: superseded, manifest: sig_foil_500MeV_v2/manifest.yml}
  - {id: sig_foil_500MeV_v3,                status: frozen,     manifest: sig_foil_500MeV_v3/manifest.yml}
  - {id: cosmic_cry_essLund_v1,             status: draft,      manifest: cosmic_cry_essLund_v1/manifest.yml}
  - {id: charged_pion_proton_foil_stress_v1,status: frozen,     manifest: charged_pion_proton_foil_stress_v1/manifest.yml}
  - ...
```

Codex-supervisor reads this file to resolve any plan or ledger reference.
Unresolvable IDs block sign-off.

## 5. ID conventions

Dataset IDs are short, unambiguous, machine-friendly:

```
<topic>_<key-feature>_<key-feature>_v<n>
```

Examples:

- `sig_foil_500MeV_v3`
- `cosmic_cry_essLund_5deg_overburdenA_v1`
- `beam_neutron_hibeam_thermalcap_v1`
- `cal_singlepion_50to600MeV_v2`
- `cal_singleproton_50to500MeV_v2`

`v<n>` increments on any change to: macro, generator seed, sample size,
geometry, physics list, digitiser config, or Geant4 version. A bump in
the simulator software *patch* version that does not affect physics
output is allowed without `v<n>` bump if a closure test (plan 19) shows
bit-equivalent or sub-resolution-equivalent outputs.

## 6. Status states and transitions

```
   draft ──→ review ──→ frozen ──→ retired
                  ▼
              superseded ──→ retired
```

- `draft` — produced but not yet reviewed; can be edited or deleted.
- `review` — proposed for freeze; Methodology Council reviews against
  acceptance criteria below.
- `frozen` — sealed. Manifest cannot be edited. Files are read-only on
  disk. Hash verification runs against frozen samples in CI.
- `superseded` — replaced by a newer version. Pointer to the successor
  is recorded.
- `retired` — files removed from disk per retention policy; manifest
  retained for citation traceability.

Freeze acceptance:

1. Sample size matches the declared target.
2. All declared output files exist and hash-match.
3. Geant4 environment file is present and self-consistent.
4. The producing macro and command are present and re-runnable.
5. Realism contract (plan 01) classification is up to date.
6. Decision-log entry exists for the freeze itself.

## 7. Hash protocol

- File hashing: `sha256sum` over each file, sorted lexicographically by
  filename. Stored in `hashes.txt` and embedded in `manifest.yml`.
- Manifest hashing: the manifest itself is hashed (excluding the
  `manifest_hash` self-reference) and the value stored in `datasets.yml`
  next to the entry.
- macOS AppleDouble files (`._*`) are excluded from hashing.

Hash verification is a CI job (plan 53) and a pre-flight check on any
plan that quotes a number against a frozen dataset.

## 8. Cross-references

Every reference to a sample in any plan, ledger row, or paper draft
uses the dataset ID. Ad-hoc references like "the signal sample we ran
last week" are forbidden. Codex-supervisor flags ad-hoc references in
plan reviews.

The reproduction ledger (plan 47) has a column `dataset_id` that joins
to the registry. Reviewer-defence packages (plan 50) include the
dataset ID as the first row of every result's provenance block.

## 9. Decision-log integration (plan 05)

A `frozen` transition logs `DEC-YYYY-MM-DD-N` with:

- the dataset ID being frozen,
- the rationale (which thesis claim or plan it serves),
- supersession links if it replaces a prior dataset,
- the freeze hash.

Subsequent ledger rows quoting the dataset cite the DEC entry.

## 10. Acceptance criteria

- The registry skeleton exists at `data/registry/` with the schema in
  §3 and §4.
- At least three datasets are registered as worked examples covering
  signal, cosmic, and calibration topics. (Concrete IDs proposed by
  plan 20, plan 21, plan 23.)
- The integrity test in `tests/test_registry_integrity.py` runs in CI
  and is green.
- Plan 47 reproduction ledger references only registry IDs, never
  free-form sample names.
- The realism contract audit (plan 01 §4) reads digitised parquet
  via the registry-resolved `outputs.base_path`, not direct paths.

## 11. Risks and mitigations

- *Risk:* registry becomes stale; samples on disk drift from
  manifests.
  *Mitigation:* hash verification in CI weekly and on every plan that
  quotes a frozen dataset. Hash mismatch is a hard fail.
- *Risk:* storage cost — full-statistics reproduction of every variant
  consumes terabytes.
  *Mitigation:* retention policy (plan 54) with `retired` state that
  removes files but preserves the manifest. Old superseded samples
  retire automatically after 90 days unless the Methodology Council
  pins them.
- *Risk:* registry becomes a bottleneck — every small-study sample
  needs a manifest.
  *Mitigation:* `draft` status is cheap; only `frozen` samples bear
  the full cost. Studies that never freeze (e.g. parameter scans)
  retain `draft` and self-retire after a month.

## 12. Dependencies

- **00_README** — defines plan ID space.
- **01_realism_contract** — sample manifests carry realism class.
- **02_digitization_seam** — sample manifests carry digitiser config ID.
- *Consumed by:* every plan that produces or quotes a sample
  (07–47 essentially, with high traffic on 20–23, 47, 50).

## 13. Out of scope

- Storage backend choice (local filesystem vs. EOS vs. S3). Plan 54
  picks the backend; this plan only specifies the metadata schema.
- Sample replication / mirroring across sites. Plan 54 again.
- Real-data samples. The registry is simulation-only; data samples
  belong to a separate registry on the data-side repository when one
  exists.

## 14. Open questions

- Should the registry index live in git or a database? *Default: YAML
  in git for now; revisit if the registry exceeds 100 entries.*
- Do we need a per-event manifest (event-id → input MCPL line)? *Default:
  no for v0.1; events resolve via run-id + event-id pair. Add only if a
  reviewer specifically asks.*
- Format for the per-file hash list — sorted text or content-addressed
  store? *Default: sorted text, simpler for git diffs.*

## 15. References

- HIBEAM `DEC-2026-04-24-1` referencing dataset IDs in the
  reproducibility appendix; this plan is the missing schema behind
  that reference.
- ATLAS Production System (Prodsys) dataset-naming convention as the
  structural inspiration.
- Rucio (CERN data management) as a future-scale option, currently
  out of scope.
