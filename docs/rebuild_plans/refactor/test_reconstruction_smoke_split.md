# `tests/test_reconstruction_smoke.py` split status

> **For Codex:** This is a status note, not an implementation plan.
> Do not split this file unless it grows past the 500-line cap again.

**Status:** superseded.

**Current state:** In
`/Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3`,
`tests/test_reconstruction_smoke.py` is 395 lines by fresh `wc -l`.
It is now below the `CODING_STANDARDS.md` section 1 limit. The earlier
split inventory is obsolete and was removed because it cited ranges that
no longer exist in the current test file.

**Related state:** The production
`nnbar_reconstruction/reconstruction.py` facade is 100 lines in the L3
branch, so the Wave 2.5 reconstruction split is not blocking on this
test file.

---

## Standing guardrails

- Keep `tests/test_reconstruction_smoke.py` below 500 lines.
- If it approaches 450 lines again, make a fresh split plan from the
  current file state before adding new coverage.
- Before any future split-plan commit, verify every file and symbol
  reference with the A+ examiner gate in `docs/parallel-sessions.md`.
- Run full `pytest tests/ -x --tb=short` after any mechanical test
  extraction.

---

## Evidence captured on 2026-05-10

```text
wc -l /Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3/tests/test_reconstruction_smoke.py
     395 /Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3/tests/test_reconstruction_smoke.py

wc -l /Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3/nnbar_reconstruction/reconstruction.py
     100 /Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3/nnbar_reconstruction/reconstruction.py
```
