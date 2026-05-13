# Lane: tpc-occupancy-followup

## Goal

Operational follow-up on the DONE `beam-background-tpc-occupancy` MASTER_PLAN
row: from the ten `OPEN:` blockers enumerated in
`docs/reports/beam_background_tpc_occupancy.md` §"Reproducibility blockers",
pick the SMALLEST single open blocker and close it in one compact unit. No
new heavy simulation runs without planner sign-off. The compact unit
delivers a focused fix (code OR fail-closed validator OR registry manifest
OR documentation patch) plus a verifier transcript.

## Files

- Read first: `docs/reports/beam_background_tpc_occupancy.md` (the ten
  `OPEN:` blockers; the §"Next smallest implementation task" already names
  `scripts/verify_beam_background_occupancy.py` as the smallest fail-closed
  validator — strongly prefer that unless a verified-smaller scope appears).
- Read-only context: `NNBAR_Detector/src/detector/beampipe_geometry.cc`,
  `NNBAR_Detector/src/core/PhysicsList.cc`,
  `NNBAR_Detector/slurm/run_cosmic_array.slurm`,
  `nnbar_reconstruction/config/nnbar_geometry.yaml`,
  `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/12_Appendix_1.tex`.
- Modify/create: ONLY the files required by the chosen blocker. Examples
  (pick at most ONE blocker, one set of files):
  - `scripts/verify_beam_background_occupancy.py` (NEW; fail-closed
    validator per §"Next smallest implementation task")
  - OR a doc patch under `docs/reports/beam_background_tpc_occupancy.md`
    only if a blocker-scoped clarification is the right smallest fix
  - OR a single registry stub under `data/registry/beam_neutron_hibeam_v1/`
    if `dataset-registry-entry` is chosen
- Update: `docs/parallel-sessions/MASTER_PLAN.md` status/notes only.

Do NOT submit SLURM unless the chosen blocker is `HP-physics-build` AND
running an existing CPU build job is the only way to verify the constructor
registration. Any SLURM submission MUST be recorded in the MASTER_PLAN notes
with job id.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec,
   `docs/reports/beam_background_tpc_occupancy.md`, and `CODING_STANDARDS.md`.
2. Score the ten `OPEN:` blockers (source staging, dataset-registry entry,
   HP-physics build, absorber selector, scorer definitions, normalization,
   random-seed policy, occupancy arithmetic, Appendix A artifacts,
   systematics throws) by smallest single-iteration scope. Default to
   `scripts/verify_beam_background_occupancy.py` per the report's §"Next
   smallest implementation task" unless a clearly smaller alternative is
   justified in the commit message.
3. Add a `## Chosen blocker` note at the top of the MASTER_PLAN row update
   naming the blocker, scope rationale (one sentence), and expected output
   artifact path.
4. Implement the chosen blocker fix. Constraints: touch only the files in
   §Files for the chosen blocker; produce a fail-closed result (validator
   returns nonzero on missing prerequisites; doc patch is fact-checked
   against thesis Appendix A); keep every touched file ≤500 lines.
5. Write/extend a focused test under `tests/` only if the blocker introduces
   new Python code; otherwise add a verifier transcript snippet to the
   commit message.
6. If (and only if) the chosen blocker is `HP-physics-build` AND requires
   running an existing sim, perform the SSH check, submit one CPU SLURM job
   on `lu48` to verify `G4HadronPhysicsFTFP_BERT_HP` registers, and record
   the job id in MASTER_PLAN notes. NO new heavy simulation runs (no
   absorber-variant sweeps, no 500k-neutron campaigns).
7. Update `docs/parallel-sessions/MASTER_PLAN.md`: keep the original
   `beam-background-tpc-occupancy` row DONE; add a sibling notes row or a
   tracker entry `tpc-occupancy-followup` recording the closed blocker and
   the remaining open count (was 10 → now 9).

## Verification

```bash
rtk python -m pytest tests/ -x -q 2>&1 | tail -20
rtk wc -l docs/reports/beam_background_tpc_occupancy.md docs/parallel-sessions/MASTER_PLAN.md $(git diff --name-only --cached 2>/dev/null | grep -v '\.md$' || echo)
rtk proxy bash -lc 'test -f scripts/verify_beam_background_occupancy.py && python scripts/verify_beam_background_occupancy.py; echo "validator_exit=$?"'
rtk proxy bash -lc 'grep -c "^[0-9]*\. \`OPEN:" docs/reports/beam_background_tpc_occupancy.md'
```

Expected: full pytest exits 0; touched files ≤500 lines; if the validator
was the chosen fix, `validator_exit` is nonzero (fail-closed against
unstaged inputs); the report's `OPEN:` count drops by exactly 1 (if a
blocker was closed by fact, not just by validator) OR remains 10 (if the
validator was created without closing a blocker — that is still acceptable
for this compact unit because it gates future closure).

## Stop condition

Stop after exactly ONE blocker fix (or the fail-closed validator scaffold)
plus the MASTER_PLAN status update is committed. Do NOT close a second
blocker, do NOT broaden into a new beam-background simulation campaign, and
do NOT submit SLURM beyond the single HP-physics verification job (if
applicable).
