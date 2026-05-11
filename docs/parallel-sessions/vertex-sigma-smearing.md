# Lane: vertex-sigma-smearing

## Goal

Bring the Python vertex weighting path closer to thesis Chapter 7 by adding a
compact, verifiable first iteration for the \(\sigma(\theta)=\bar d_0(\theta)\)
weighting contract and the associated smearing-closure expectations. Do not
invent thesis numbers from plots; only hard-code values that are explicitly
available from a checked source.

## Writable scope

- `nnbar_reconstruction/vertex/classical_vertex.py`
- New or focused tests under `tests/`, preferably `tests/test_vertex_sigma_smearing.py`
- `docs/parallel-sessions/MASTER_PLAN.md` only for final lane-status notes

Do not edit C++ simulation, SLURM files, queues, or unrelated reconstruction
modules in this lane.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/7_Reconstruction.tex`
   - Vertex Reconstruction
   - Effect of Resolution
4. Existing Python surfaces verified before this spec was written:
   - `nnbar_reconstruction/vertex/classical_vertex.py`
   - functions/classes: `VertexResult`, `estimate_angular_uncertainty`,
     `weighted_vertex_reconstruction`, `reconstruct_vertex`,
     `iterative_vertex_reconstruction`

Before committing any new file/function/path claim, re-run the verifier rule in
`docs/parallel-sessions.md` rather than trusting this handoff.

## One compact-safe iteration

Pick one small unit and finish it completely. Recommended first unit:

1. Add a thesis-style projected-vertex uncertainty helper for \(\theta\)-binned
   \(\bar d_0\) values.
   - Use 20-degree bins over 0--180 degrees.
   - Treat the table values as projected-position uncertainties, not angular
     uncertainties in radians.
   - If a thesis numeric table is not present in the source text, make the API
     require an explicit table/config for thesis-mode weighting and keep the
     current empirical fallback unchanged.
2. Wire the helper into `weighted_vertex_reconstruction` behind an explicit
   argument or documented config path so existing callers keep their current
   behavior unless thesis-mode data are supplied.
3. Add regression tests with a small synthetic table and synthetic tracks:
   - bin selection is correct at bin boundaries and near 0/180 degrees;
   - weights are proportional to \(1/\sigma(\theta)^2\);
   - the weighted vertex uses projected-position sigma values and does not mix
     radians with centimeters;
   - the empirical fallback still works when no table is supplied.
4. If time remains, add a seeded smearing-closure test with toy tracks; otherwise
   leave the smearing closure as a concrete TODO in this lane spec or
   `MASTER_PLAN.md` notes without claiming it is done.

## Verification command

Run focused tests first, then full tests if the focused set passes:

```bash
python -m pytest tests/test_vertex_sigma_smearing.py -q
python -m pytest tests/ -x -q
```

Also verify the 500-line cap:

```bash
wc -l nnbar_reconstruction/vertex/classical_vertex.py tests/test_vertex_sigma_smearing.py
```

## Stop condition

Stop after one compact, tested unit. Handoff must state exactly which behavior
was implemented, which tests passed, whether a real thesis \(\bar d_0\) numeric
table was found, and any remaining blocker for the smearing-closure part.
