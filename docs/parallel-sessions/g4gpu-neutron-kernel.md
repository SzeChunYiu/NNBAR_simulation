# Lane: g4gpu-neutron-kernel

## Goal

Scaffold the G4GPU neutron elastic-scattering kernel described by the
geant4-gpu SPEC without touching NNBAR production code. This compact unit
adds a clearly bounded CUDA/header interface, a deterministic CPU/GPU-safe
unit test for two-body elastic-scattering kinematics, CMake wiring under the
existing neutron build option, and fail-closed notes for physics parity work
that remains beyond the first scaffold.

## Files

Work in the geant4-gpu repo ONLY:

- Repo: `/Volumes/MyDrive/nnbar/geant4-gpu/`
- Branch: `lane/g4gpu-neutron-kernel`
- Create: `include/g4gpu/NeutronStepKernel.hh`
- Create: `src/physics/NeutronStepKernel.cu`
- Create: `tests/test_neutron_elastic_scatter.cu`
- Modify: `CMakeLists.txt` to add the neutron source and test target under
  `G4GPU_WITH_NEUTRON`
- Update: `/Volumes/MyDrive/nnbar/nnbar/simulation/docs/parallel-sessions/MASTER_PLAN.md`
  row status/notes only.

Read-only references:

- `/Volumes/MyDrive/nnbar/geant4-gpu/docs/SPEC.md`
- `/Volumes/MyDrive/nnbar/geant4-gpu/docs/VALIDATION.md`
- `/Volumes/MyDrive/nnbar/geant4-gpu/include/g4gpu/G4GPUTrackBuffer.hh`
- `/Volumes/MyDrive/nnbar/geant4-gpu/include/g4gpu/MaterialData.hh`
- `/Volumes/MyDrive/nnbar/geant4-gpu/src/physics/MuonStepKernel.cu`
- `/Volumes/MyDrive/nnbar/geant4-gpu/CMakeLists.txt`

**G4GPU isolation:** do not include, link, import, or inspect NNBAR_Detector
production code for this implementation. The kernel must live entirely in the
geant4-gpu repo and use only the geant4-gpu public structs already present
there. No simulations or SLURM submissions are part of this compact unit.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec,
   `docs/policies/g4gpu-isolation.md`, `CODING_STANDARDS.md`, and the
   geant4-gpu `docs/SPEC.md` / `docs/VALIDATION.md` files.
2. In MASTER_PLAN, mark the row **G4GPU neutron physics kernel** `RUNNING`
   with lane `g4gpu-neutron-kernel` before editing geant4-gpu files.
3. Create `include/g4gpu/NeutronStepKernel.hh` with a launch function shaped
   consistently with the existing muon launch interface. Keep the interface
   minimal: track buffer, RNG state, material table pointer, track count, and
   optional stream.
4. Create `src/physics/NeutronStepKernel.cu` with a compile-safe scaffold that:
   - selects neutron tracks by PDG 2112 and leaves all other tracks unchanged;
   - preserves total kinetic energy for the first elastic-scattering scaffold;
   - samples an isotropic center-of-mass direction using the existing RNG
     convention when RNG is supplied;
   - records every unimplemented physics-parity feature as `TODO Phase N` or
     `OPEN:` in comments, especially cross-section tables, target isotope
     selection, thermal scattering, inelastic channels, and secondary recoil
     bookkeeping.
5. Create `tests/test_neutron_elastic_scatter.cu` with a small deterministic
   test that verifies non-neutron tracks are unchanged and neutron elastic
   scattering preserves finite direction normalization and kinetic energy.
   Use a CPU-safe fallback path if the current test harness cannot launch CUDA
   kernels locally.
6. Wire `CMakeLists.txt`: when `G4GPU_WITH_NEUTRON` is enabled, add
   `src/physics/NeutronStepKernel.cu` to `G4GPU` and register a ctest target
   named `g4gpu_neutron_elastic_scatter` for the new test.
7. Verify build and isolation with the commands below. If CUDA runtime testing
   is not available locally, the compile target plus a parse/grep check is
   sufficient for this compact unit; record the runtime blocker in
   MASTER_PLAN notes.
8. Commit on `lane/g4gpu-neutron-kernel`, push if that lane is already using a
   remote branch, and update MASTER_PLAN with the commit hash and verification
   result. Do not start neutron physics-parity tuning in this iteration.

## Verification

```bash
rtk wc -l /Volumes/MyDrive/nnbar/geant4-gpu/include/g4gpu/NeutronStepKernel.hh \
          /Volumes/MyDrive/nnbar/geant4-gpu/src/physics/NeutronStepKernel.cu \
          /Volumes/MyDrive/nnbar/geant4-gpu/tests/test_neutron_elastic_scatter.cu
rtk proxy bash -lc 'grep -RIn "NNBAR_Detector\|nnbar_reconstruction" /Volumes/MyDrive/nnbar/geant4-gpu/include /Volumes/MyDrive/nnbar/geant4-gpu/src /Volumes/MyDrive/nnbar/geant4-gpu/tests || echo "ISOLATION_OK"'
rtk proxy bash -lc 'cd /Volumes/MyDrive/nnbar/geant4-gpu && cmake -B build -DG4GPU_WITH_NEUTRON=ON -DG4GPU_WITH_OPTICAL=OFF -DG4GPU_WITH_RTX=OFF 2>&1 | tail -20'
rtk proxy bash -lc 'cd /Volumes/MyDrive/nnbar/geant4-gpu && cmake --build build -j4 --target G4GPU 2>&1 | tail -30'
rtk proxy bash -lc 'cd /Volumes/MyDrive/nnbar/geant4-gpu && ctest --test-dir build -R g4gpu_neutron_elastic_scatter --output-on-failure 2>&1 | tail -40'
```

Expected: isolation grep prints `ISOLATION_OK`; touched files are each under
500 lines; configure and library build succeed; the neutron ctest passes when
CUDA test execution is available or is explicitly documented as a runtime-only
blocker.

## Stop condition

Stop after the neutron kernel scaffold, deterministic elastic-scattering test,
CMake wiring, verification evidence, and MASTER_PLAN status update are
committed. Do not run production NNBAR simulations, submit SLURM jobs, or tune
neutron physics parity in this compact unit.
