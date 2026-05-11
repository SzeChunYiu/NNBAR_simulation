# Lane: g4gpu-isolation-audit

## Goal

Verify the NNBAR simulation is not currently linking against, calling, or
depending on the G4GPU R&D project anywhere — in code, builds, SLURM scripts,
or data provenance. Report findings to
`docs/reports/g4gpu_isolation_audit_<date>.md`.

This is a defensive audit. It should pass cleanly today (G4GPU is fresh).
We run it now to lock in the clean baseline and re-run on a recurring basis
to catch any future drift.

Read first: `docs/policies/g4gpu-isolation.md`

## Audit checks

For each check, record PASS or FAIL with the exact command output. If any
check FAILs, the audit report flags it as a `VIOLATION:` block and queues
a remediation task.

### 1. NNBAR_Detector code references

```bash
rtk proxy ssh lunarc 'grep -rni "G4GPU\|geant4-gpu\|G4GPUGeometry\|libG4GPU" \
  /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/ 2>/dev/null \
  | grep -v "\.git/" | head -30'

# Local mirror:
grep -rni "G4GPU\|geant4-gpu\|G4GPUGeometry\|libG4GPU" \
  NNBAR_Detector/ 2>/dev/null | grep -v "\.git/" | head -30
```

Expected: no matches.

### 2. CMake / build configuration

```bash
grep -ni "G4GPU\|find_package.*G4GPU" NNBAR_Detector/CMakeLists.txt
grep -ni "G4GPU\|find_package.*G4GPU" NNBAR_Detector/*/CMakeLists.txt 2>/dev/null
rtk proxy ssh lunarc 'grep -ni "G4GPU\|find_package.*G4GPU" \
  /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/CMakeLists.txt \
  /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/*/CMakeLists.txt 2>/dev/null'
```

Expected: no matches.

### 3. Python imports

```bash
grep -rni "import g4gpu\|from g4gpu\|geant4_gpu" nnbar_reconstruction/ 2>/dev/null
```

Expected: no matches.

### 4. SLURM and shell scripts

```bash
grep -rni "geant4-gpu\|G4GPU\|libG4GPU" \
  scripts/ lunarc/ slurm/ macro/ 2>/dev/null | grep -v "\.git/"
rtk proxy ssh lunarc 'grep -rni "geant4-gpu\|G4GPU\|libG4GPU" \
  /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/ \
  /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/scripts/ 2>/dev/null'
```

Expected: no matches.

### 5. Result Parquet provenance

```bash
python3 -c "
import pyarrow.parquet as pq
import glob, os
for f in glob.glob('nnbar_reconstruction/results/**/*.parquet', recursive=True):
    try:
        pf = pq.ParquetFile(f)
        meta = pf.schema_arrow.metadata or {}
        sim = meta.get(b'simulator', b'<missing>').decode()
        print(f'{os.path.basename(f)}: simulator={sim}')
    except Exception as e:
        print(f'{f}: ERROR {e}')
"
```

Expected: every file either reports `simulator=geant4-11.2.2-...` or is
flagged as missing-provenance (which is a separate problem, not a G4GPU
violation, but should be noted).

### 6. Binary inventory on LUNARC

```bash
rtk proxy ssh lunarc 'ls -la \
  /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build/*.so 2>/dev/null'
rtk proxy ssh lunarc 'find /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build/ \
  -name "*.so" -exec ldd {} \; 2>/dev/null | grep -i "g4gpu\|geant4-gpu"'
```

Expected: no `libG4GPU` in the linker output.

### 7. CI / config

```bash
grep -rni "G4GPU\|geant4-gpu" .github/ Makefile pyproject.toml setup.py 2>/dev/null
```

Expected: no matches except in documentation paths.

### 8. Documentation cross-check

The audit confirms that `docs/policies/g4gpu-isolation.md` exists and is
referenced from MASTER_PLAN.md. (Documentation about G4GPU is allowed; what
is forbidden is code dependency.)

## Output

`docs/reports/g4gpu_isolation_audit_YYYYMMDD.md` containing:
1. Date and commit hash
2. Each of the eight checks above with its exact command and output
3. Overall PASS / FAIL verdict
4. If any FAIL: a `VIOLATION:` block per finding with severity (`CRITICAL` if
   in production code; `WARNING` if only in development branches) and a
   proposed remediation
5. Sign-off line: "Audit verifies NNBAR simulation is isolated from G4GPU as
   of <commit>."

## Iteration cycle

1. Read this spec and `docs/policies/g4gpu-isolation.md`
2. Mark `g4gpu-isolation-audit` RUNNING in MASTER_PLAN.md
3. Run each check above on both local and LUNARC trees
4. Write the report
5. Commit on the current branch
6. Mark DONE

## Acceptance

- All eight checks executed with their commands and output recorded
- Verdict line is unambiguous
- Any FAIL produces a remediation entry queued for the appropriate worker
- The report file ends with the sign-off line

## Stop condition

After committing the report, stop. The planner should re-queue this audit on
a recurring basis (suggest weekly while G4GPU is under active development).
