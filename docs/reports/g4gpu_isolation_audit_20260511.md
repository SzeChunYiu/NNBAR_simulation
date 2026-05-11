# G4GPU isolation audit — 2026-05-11

- **Audited baseline commit:** `7f6c9a2` (`docs(planner): queue calibration and protocol follow-ups`)
- **Branch observed:** `lane/g4-source-review-hotpath1-pil`
- **Policy:** `docs/policies/g4gpu-isolation.md`
- **Spec:** `docs/parallel-sessions/g4gpu-isolation-audit.md`
- **Verdict:** PASS — no evidence that the NNBAR simulation links against, calls, imports, or uses G4GPU in code, builds, SLURM/scripts, or available result provenance.

Note: the broad sample greps in the spec would traverse generated build trees,
SLURM stdout logs, Parquet/test artifacts, and other non-source directories.
For the code-reference checks below I used extension-filtered `find | grep`
commands over source/config/script/documentation files, while the dedicated
script and binary checks separately cover production script and build-linkage
surfaces. Empty output means no matching contamination string was found.

## Check 1 — NNBAR_Detector code references

### LUNARC tree

Command:

```bash
rtk proxy ssh lunarc 'cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim && find CMakeLists.txt Makefile config.h.in cmake config docs external include macro macros scripts slurm src tests -type f \( -name "*.cc" -o -name "*.hh" -o -name "*.cu" -o -name "*.cuh" -o -name "*.cpp" -o -name "*.hpp" -o -name "*.h" -o -name "CMakeLists.txt" -o -name "*.cmake" -o -name "*.sh" -o -name "*.slurm" -o -name "*.mac" -o -name "*.md" -o -name "Makefile" -o -name "*.in" \) -print0 2>/dev/null | xargs -0 grep -nI "G4GPU\|geant4-gpu\|G4GPUGeometry\|libG4GPU" 2>/dev/null | head -30'
```

Output:

```text
(no output; command exit 0)
```

Result: PASS.

### Local mirror

Command:

```bash
rtk proxy bash -lc 'find NNBAR_Detector/CMakeLists.txt NNBAR_Detector/Makefile NNBAR_Detector/config.h.in NNBAR_Detector/cmake NNBAR_Detector/config NNBAR_Detector/docs NNBAR_Detector/external NNBAR_Detector/include NNBAR_Detector/macro NNBAR_Detector/macros NNBAR_Detector/scripts NNBAR_Detector/slurm NNBAR_Detector/src NNBAR_Detector/tests -type f \( -name "*.cc" -o -name "*.hh" -o -name "*.cu" -o -name "*.cuh" -o -name "*.cpp" -o -name "*.hpp" -o -name "*.h" -o -name "CMakeLists.txt" -o -name "*.cmake" -o -name "*.sh" -o -name "*.slurm" -o -name "*.mac" -o -name "*.md" -o -name "Makefile" -o -name "*.in" \) -print0 2>/dev/null | xargs -0 grep -nI "G4GPU\|geant4-gpu\|G4GPUGeometry\|libG4GPU" 2>/dev/null | head -30'
```

Output:

```text
(no output; command exit 0)
```

Result: PASS.

## Check 2 — CMake / build configuration

### Local CMake files

Command:

```bash
rtk proxy bash -lc 'grep -ni "G4GPU\|find_package.*G4GPU" NNBAR_Detector/CMakeLists.txt; printf "root_exit=%s\n" "$?"; find NNBAR_Detector -mindepth 2 -maxdepth 2 -name CMakeLists.txt -print -exec grep -ni "G4GPU\|find_package.*G4GPU" {} \;; printf "nested_find_exit=%s\n" "$?"'
```

Output:

```text
root_exit=1
nested_find_exit=0
```

Result: PASS — `grep` exit 1 is the expected no-match result for the root CMake file; nested search found no G4GPU lines.

### LUNARC CMake files

Command:

```bash
rtk proxy ssh lunarc 'grep -ni "G4GPU\|find_package.*G4GPU" /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/CMakeLists.txt; printf "root_exit=%s\n" "$?"; find /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim -mindepth 2 -maxdepth 2 -name CMakeLists.txt -print -exec grep -ni "G4GPU\|find_package.*G4GPU" {} \;; printf "nested_find_exit=%s\n" "$?"'
```

Output:

```text
root_exit=1
nested_find_exit=0
```

Result: PASS.

## Check 3 — Python imports

Command:

```bash
rtk proxy bash -lc 'set +e; grep -rni "import g4gpu\|from g4gpu\|geant4_gpu" nnbar_reconstruction/ 2>/dev/null; printf "exit=%s\n" "$?"'
```

Output:

```text
exit=1
```

Result: PASS — no Python import of G4GPU was found.

## Check 4 — SLURM and shell scripts

### Local scripts

Command:

```bash
rtk proxy bash -lc 'printf "script_file_count="; find scripts lunarc slurm macro -type f \( -name "*.sh" -o -name "*.slurm" -o -name "*.py" -o -name "*.bash" -o -name "*.zsh" -o -name "*.md" \) 2>/dev/null | wc -l; find scripts lunarc slurm macro -type f \( -name "*.sh" -o -name "*.slurm" -o -name "*.py" -o -name "*.bash" -o -name "*.zsh" -o -name "*.md" \) -print0 2>/dev/null | xargs -0 grep -nI "geant4-gpu\|G4GPU\|libG4GPU" 2>/dev/null || true'
```

Output:

```text
script_file_count=      11
```

Result: PASS.

### LUNARC scripts

Command:

```bash
rtk proxy ssh lunarc 'cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim && printf "script_file_count=" && find slurm scripts -type f \( -name "*.sh" -o -name "*.slurm" -o -name "*.py" -o -name "*.bash" -o -name "*.zsh" -o -name "*.md" \) 2>/dev/null | wc -l && find slurm scripts -type f \( -name "*.sh" -o -name "*.slurm" -o -name "*.py" -o -name "*.bash" -o -name "*.zsh" -o -name "*.md" \) -print0 2>/dev/null | xargs -0r grep -nI "geant4-gpu\|G4GPU\|libG4GPU" 2>/dev/null || true'
```

Output:

```text
script_file_count=26
```

Result: PASS.

## Check 5 — Result Parquet provenance

Command:

```bash
rtk proxy python3 - <<'PY'
import pyarrow.parquet as pq
import glob, os
files = sorted(glob.glob('nnbar_reconstruction/results/**/*.parquet', recursive=True))
print(f'files={len(files)}')
for f in files:
    try:
        pf = pq.ParquetFile(f)
        meta = pf.schema_arrow.metadata or {}
        sim = meta.get(b'simulator', b'<missing>').decode()
        print(f'{os.path.basename(f)}: simulator={sim}')
    except Exception as e:
        print(f'{f}: ERROR {e}')
PY
```

Output:

```text
files=0
```

Result: PASS — no local Parquet result files were present in the audited path, so no G4GPU provenance or missing-provenance finding was observed.

## Check 6 — Binary inventory on LUNARC

### Spec build directory

Command:

```bash
rtk proxy ssh lunarc 'ls -la /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build/*.so 2>/dev/null; printf "ls_exit=%s\n" "$?"; find /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build/ -name "*.so" -exec ldd {} \; 2>/dev/null | grep -i "g4gpu\|geant4-gpu"; printf "ldd_grep_exit=%s\n" "$?"'
```

Output:

```text
ls_exit=2
ldd_grep_exit=1
```

Result: PASS — no shared objects were present in the spec build directory, and linker-output grep found no G4GPU dependency.

### Additional current LUNARC build directories

Command:

```bash
rtk proxy ssh lunarc 'find /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build_lunarc -name "*.so" -print 2>/dev/null | head -40; find /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build_lunarc -name "*.so" -exec ldd {} \; 2>/dev/null | grep -i "g4gpu\|geant4-gpu"; printf "ldd_grep_exit=%s\n" "$?"'
```

Output:

```text
ldd_grep_exit=1
```

Result: PASS.

## Check 7 — CI / config

Command:

```bash
rtk proxy bash -lc 'for p in .github Makefile pyproject.toml setup.py; do [ -e "$p" ] && printf "%s\n" "$p"; done | xargs grep -rni "G4GPU\|geant4-gpu" 2>/dev/null || true'
```

Output:

```text
(no output; command exit 0)
```

Result: PASS.

## Check 8 — Documentation cross-check

Command:

```bash
rtk proxy bash -lc 'ls docs/policies/g4gpu-isolation.md; grep -ni "g4gpu-isolation" docs/parallel-sessions/MASTER_PLAN.md'
```

Output:

```text
docs/policies/g4gpu-isolation.md
87:| **G4GPU↔NNBAR isolation policy** | DONE | g4gpu-isolation-policy | See `docs/policies/g4gpu-isolation.md`; NNBAR uses vanilla Geant4 only until per-process physics-parity gate passes |
88:| **G4GPU isolation audit** | RUNNING | g4gpu-isolation-audit | See `docs/parallel-sessions/g4gpu-isolation-audit.md`; verify no current cross-contamination and lock in clean baseline |
```

Result: PASS.

## Overall verdict

PASS. All eight audit checks were executed and no G4GPU contamination was found in the NNBAR production code, build configuration, Python imports, SLURM/script surfaces, binary linkage surface, CI/config surface, or available result provenance.

No `VIOLATION:` remediation blocks are queued from this audit.

Audit verifies NNBAR simulation is isolated from G4GPU as of 7f6c9a2.
