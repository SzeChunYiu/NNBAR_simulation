# Lane: g4gpu-em-gamma-kernel

## Goal

Design and scaffold the `EMStepKernel.cu` GPU kernel for G4GPU per
`docs/SPEC.md` Phase 2 EM physics (photoelectric, Compton, pair production,
bremsstrahlung for e-/e+/gamma). The compact unit delivers a documented kernel
skeleton, one validation test (Klein-Nishina Compton sampling cross-check),
and a CMake target wired under the existing `G4GPU_WITH_EM` option. Full
physics implementation is intentionally deferred — this iteration locks the
interface, SoA contract, and test scaffold. Tracks MASTER_PLAN row "G4GPU
EM/gamma and neutron physics kernels" (PROPOSED).

## Files

Work in the geant4-gpu repo ONLY:

- Repo: `/Volumes/MyDrive/nnbar/geant4-gpu/`
- Branch: `lane/g4gpu-em-gamma`
- Create: `src/physics/EMStepKernel.cu`
- Create: `include/g4gpu/EMStepKernel.hh`
- Create: `tests/test_em_klein_nishina.cu`
- Modify: `CMakeLists.txt` (add EM kernel source + test target under
  `G4GPU_WITH_EM`)
- Update: `/Volumes/MyDrive/nnbar/nnbar/simulation/docs/parallel-sessions/MASTER_PLAN.md`
  row status/notes only.

Read-only references: `/Volumes/MyDrive/nnbar/geant4-gpu/docs/SPEC.md`,
`/Volumes/MyDrive/nnbar/geant4-gpu/docs/VALIDATION.md`,
`/Volumes/MyDrive/nnbar/geant4-gpu/include/g4gpu/G4GPUTrackBuffer.hh`,
`/Volumes/MyDrive/nnbar/geant4-gpu/src/physics/MuonStepKernel.cu`.

**G4GPU isolation:** Do NOT `#include` any `NNBAR_Detector/` header, link any
NNBAR library, or read NNBAR Python/C++ source. No edits to anything under
`/Volumes/MyDrive/nnbar/nnbar/simulation/` except the MASTER_PLAN row.
See `docs/policies/g4gpu-isolation.md` in the NNBAR repo.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, `docs/policies/g4gpu-isolation.md`,
   `CODING_STANDARDS.md`, and the geant4-gpu `docs/SPEC.md` Phase 1/2 sections.
2. Mark the MASTER_PLAN "G4GPU EM/gamma and neutron physics kernels" row
   RUNNING with lane `g4gpu-em-gamma-kernel`.
3. Write `include/g4gpu/EMStepKernel.hh`: device-callable signatures for
   `EMStep(TrackSOA, MaterialData*, curandState*, int n)` plus stubs for
   `SamplePhotoelectric`, `SampleCompton` (Klein-Nishina), `SamplePair`,
   and `SampleBremsstrahlung`. Document each as `__device__` and list the
   inputs/outputs in a header comment.
4. Implement `src/physics/EMStepKernel.cu` with: full Klein-Nishina sampler
   for `SampleCompton` (Khan rejection method), and DOCUMENTED STUBS that
   `return;` for the other three processes with a `// TODO Phase 2.N` line
   and the relevant SPEC section reference.
5. Implement `tests/test_em_klein_nishina.cu`: fire 10,000 1 MeV gammas at a
   single scatter, sample scattered-photon energy, and KS-test against the
   analytic Klein-Nishina differential cross-section (tolerance per
   VALIDATION.md statistical standard, p > 0.05).
6. Wire CMake: under `if(G4GPU_WITH_EM)` add `src/physics/EMStepKernel.cu`
   to the `G4GPU` library and register `tests/test_em_klein_nishina.cu` as a
   ctest target named `g4gpu_em_klein_nishina`.
7. Verify locally that `cmake --build build` succeeds (no GPU required for
   compile). Do NOT submit SLURM in this compact unit — runtime ctest will
   run in the next iteration on `gpua40`.
8. Commit on `lane/g4gpu-em-gamma`, push to GitHub, then update the
   MASTER_PLAN row notes with the commit hash and "compile-only verified;
   GPU runtime + remaining processes deferred to next iteration".

## Verification

```bash
rtk wc -l /Volumes/MyDrive/nnbar/geant4-gpu/include/g4gpu/EMStepKernel.hh \
          /Volumes/MyDrive/nnbar/geant4-gpu/src/physics/EMStepKernel.cu \
          /Volumes/MyDrive/nnbar/geant4-gpu/tests/test_em_klein_nishina.cu
rtk proxy bash -lc 'grep -RIn "NNBAR_Detector\|nnbar_reconstruction" /Volumes/MyDrive/nnbar/geant4-gpu/include /Volumes/MyDrive/nnbar/geant4-gpu/src /Volumes/MyDrive/nnbar/geant4-gpu/tests || echo "ISOLATION_OK"'
rtk proxy bash -lc 'cd /Volumes/MyDrive/nnbar/geant4-gpu && cmake -B build -DG4GPU_WITH_EM=ON -DG4GPU_WITH_OPTICAL=OFF -DG4GPU_WITH_RTX=OFF 2>&1 | tail -20'
rtk proxy bash -lc 'cd /Volumes/MyDrive/nnbar/geant4-gpu && cmake --build build -j4 --target G4GPU 2>&1 | tail -30'
```

Expected: isolation grep prints `ISOLATION_OK`; cmake configure + library
build succeed; each touched file is ≤500 lines.

## Stop condition

Stop after the kernel skeleton, Klein-Nishina test scaffold, CMake wiring,
local compile-verify, and MASTER_PLAN status update are committed on
`lane/g4gpu-em-gamma`. Do NOT implement photoelectric/pair/bremsstrahlung
physics or run GPU ctests in this iteration — defer to next compact unit.
