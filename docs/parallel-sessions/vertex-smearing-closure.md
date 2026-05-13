# Lane: vertex-smearing-closure

## Goal

Close the remaining thesis Chapter 7 "Effect of Resolution" follow-up from
`vertex-sigma-smearing`: add a compact seeded smearing-closure regression for
the explicit \(\sigma(\theta)\) projected-vertex uncertainty contract, without
inventing numeric values from thesis plots.

## Writable scope

- `tests/test_vertex_sigma_smearing.py`
- `nnbar_reconstruction/vertex/classical_vertex.py` only if the test exposes a
  small API defect needed for closure
- `docs/parallel-sessions/MASTER_PLAN.md` only for final status notes

Do not edit queues, C++ simulation, SLURM files, or unrelated reconstruction
modules in this lane.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `docs/parallel-sessions/vertex-sigma-smearing.md`
4. `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/7_Reconstruction.tex`
   - Vertex Reconstruction
   - Effect of Resolution

## One compact-safe iteration

Implement one seeded toy closure test:

1. Build synthetic `Track` objects whose true projected vertex is known.
2. Use a small explicit synthetic \(\sigma(\theta)\) table in centimeters.
3. Smear projected vertices with a fixed RNG seed and the corresponding table
   value for each track's theta bin.
4. Reconstruct with `weighted_vertex_reconstruction(..., weight_by_r_head=False,
   theta_sigma_table_cm=...)`.
5. Assert the estimator is approximately unbiased and that the normalized pull
   or RMS residual is consistent with the injected projected-position sigma
   within a documented toy tolerance.
6. Keep the test deterministic and small; do not require thesis sample files.

If the existing API cannot expose the quantities needed for a clean closure,
make the minimal production-code change in `classical_vertex.py` and document it
in the test.

## Verification command

```bash
python -m pytest tests/test_vertex_sigma_smearing.py -q
python -m pytest tests/ -x -q
wc -l nnbar_reconstruction/vertex/classical_vertex.py tests/test_vertex_sigma_smearing.py
```

## Stop condition

Stop after the seeded closure test passes, full tests pass, touched files remain
under 500 lines, and `MASTER_PLAN.md` says whether this closes the smearing
follow-up or leaves a named blocker.
