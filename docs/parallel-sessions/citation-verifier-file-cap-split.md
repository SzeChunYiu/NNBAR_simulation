# Lane: citation-verifier-file-cap-split

## Goal
Split `scripts/verify_citations.py` before further growth. The AppleDouble
sidecar fix left the script at 488 lines, above the 450-line split threshold in
`CODING_STANDARDS.md` / `docs/parallel-sessions.md`.

## Scope
- Editable: `scripts/verify_citations.py`, a new helper module under `scripts/`
  if needed, and `tests/test_verify_citations.py` only.
- Forbidden: reconstruction/simulation physics code, queue validator behavior,
  SLURM, remote LUNARC jobs, generated reports.

## Required steps
1. Preserve current CLI behavior and public test imports.
2. Move cohesive helper groups into a small importable module (for example
   citation parsing/report writing), keeping all touched files below 450 lines
   where practical and definitely below 500.
3. Add or adjust tests only for import/CLI parity if the split changes module
   boundaries.
4. Do not change verifier semantics except for refactor-equivalent imports.

## Verification
Run:

```bash
rtk proxy python -m pytest tests/test_verify_citations.py -q
rtk proxy python scripts/verify_citations.py docs/parallel-sessions --report-json /tmp/nnbar-citation-report.json --report-md /tmp/nnbar-citation-report.md
rtk proxy python -m pytest tests/ -x -q 2>&1 | tail -20
rtk proxy bash scripts/validate-csup-queues.sh
rtk proxy wc -l scripts/verify_citations.py tests/test_verify_citations.py
```

## Stop condition
Stop after the refactor is committed or, if the split is unsafe, write a blocker
note with the exact import/API conflict and no production-code changes.
