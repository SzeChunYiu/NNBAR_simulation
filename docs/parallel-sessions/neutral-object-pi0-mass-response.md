# Lane: neutral-object-pi0-mass-response

## Goal

Fail-closed audit of neutral-object truth-vs-reco distributions (Ch. 7 photon
energy + opening-angle) and π⁰ invariant-mass response (Ch. 8 single-π⁰) at
**50, 150, 250 MeV** mono-energetic π⁰ samples. If a sample is missing, emit a
structured blocker — do NOT regenerate. See MASTER_PLAN.md rows for
"neutral object response" and "single-π⁰ response".

## Files

- Create: `nnbar_reconstruction/analysis/neutral_pi0_response_audit.py` (<= 500 lines)
- Create: `tests/test_neutral_pi0_response_audit.py` (<= 300 lines)
- Update: `docs/parallel-sessions/MASTER_PLAN.md` (row status only)
- Read-only: `nnbar_reconstruction/reconstruction/pi0_cuts.py`,
  `nnbar_reconstruction/reconstruction/neutral_reconstruction.py`,
  existing pi0 samples on LUNARC under `build_lunarc/output/pi0_*`,
  `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/{7,8}_*.tex`

Do not edit C++. Do not submit SLURM. Do not retune any pi0 constants — this
lane only AUDITS; cut tuning is owned by `pi0-verification`.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, `pi0-verification.md`,
   `CODING_STANDARDS.md`.
2. Define `PI0_SAMPLE_ENERGIES_MEV = (50, 150, 250)` and reference Ch. 7/8
   expected response numbers (mass peak ~ 135 MeV, expected sigma scaling).
3. Implement `discover_pi0_sample(energy_mev, search_root) -> Optional[Path]`
   that locates an existing mono-energetic Parquet; never trigger a sim.
4. Implement `audit_pi0_response(parquet_path, energy_mev) -> AuditResult`
   producing: reco mass peak position, sigma, opening-angle distribution
   summary, photon energy truth-vs-reco bias. Emit structured blockers:
   `pi0_50mev_sample_missing`, `pi0_150mev_sample_missing`,
   `pi0_250mev_sample_missing`, `mass_peak_off_thesis`,
   `opening_angle_distribution_unverified`.
5. Top-level `run_audit(search_root) -> list[AuditResult]` iterates the three
   energies, returns one result per energy with blockers attached. Never raises
   on missing files.
6. Tests: (a) all three `*_sample_missing` blockers fire when search_root is
   empty, (b) synthetic Parquet with peak at 135 +- 10 MeV passes for one
   energy, (c) shifted peak triggers `mass_peak_off_thesis` with the offset
   reported in the reason.
7. Update MASTER_PLAN row with audit outcome (DONE or BLOCKED + reasons).

## Verification

```bash
rtk python -m pytest tests/test_neutral_pi0_response_audit.py -q
rtk zsh -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'
rtk wc -l nnbar_reconstruction/analysis/neutral_pi0_response_audit.py tests/test_neutral_pi0_response_audit.py docs/parallel-sessions/MASTER_PLAN.md
```

Expected: focused tests pass; full suite stays green; module + test each
remain <= 500 lines; no edits to `pi0_cuts.py` or C++.

## Stop condition

One compact-safe iteration: implement audit + tests, run, update MASTER_PLAN
row, commit, stop. If `*_sample_missing` blockers fire, leave row BLOCKED with
the missing-energy reasons; do NOT submit any new π⁰ simulation in this lane.
