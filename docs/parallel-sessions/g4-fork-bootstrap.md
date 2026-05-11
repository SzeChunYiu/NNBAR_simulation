# Lane: g4-fork-bootstrap (Clone Geant4, prepare upstream-patch workflow)

## Goal

Set up the infrastructure for contributing optimizations upstream to Geant4
itself. This is the foundation for every Phase 5+ patch that targets vanilla
Geant4 (as opposed to the `libG4Accel` opt-in library).

Read first:
- `docs/specs/g4gpu-line-by-line-acceleration.md` (broad strategy)
- `docs/policies/g4gpu-isolation.md` (isolation policy still applies)

## Output

A working Geant4 fork at two locations:

- Local: `/Volumes/MyDrive/nnbar/geant4-fork/`
- LUNARC: `/projects/hep/fs10/shared/nnbar/billy/geant4-fork/`

Both are clones of `https://gitlab.cern.ch/geant4/geant4.git` at tag
`v11.2.2` (matches the production build NNBAR uses). On both, a branch
`accel/master` is created off the tag and pushed to a private GitHub mirror
under the user's account at `git@github.com:scyiu/geant4-accel.git` (create
if it does not exist; if creation is blocked, document the manual step).

## Iteration cycle

1. Mark `g4-fork-bootstrap` RUNNING in MASTER_PLAN.md
2. Clone Geant4 source (local first, then LUNARC):
   ```bash
   git clone https://gitlab.cern.ch/geant4/geant4.git /Volumes/MyDrive/nnbar/geant4-fork
   cd /Volumes/MyDrive/nnbar/geant4-fork
   git checkout v11.2.2
   git checkout -b accel/master
   ```
3. Verify the canonical examples build on LUNARC:
   ```bash
   rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
   rtk proxy rsync -av /Volumes/MyDrive/nnbar/geant4-fork/ \
     lunarc:/projects/hep/fs10/shared/nnbar/billy/geant4-fork/
   rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/geant4-fork && \
     cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
       -DGEANT4_INSTALL_DATA=ON -DGEANT4_BUILD_MULTITHREADED=ON \
       -DGEANT4_BUILD_EXAMPLES=ON && \
     cmake --build build -j8 2>&1 | tail -30"
   ```
4. Identify the **upstream contribution workflow** documented at
   `https://geant4.web.cern.ch/develop/code-contribution`. Document the
   process in `docs/strategies/g4-upstream-process.md`:
   - Required formatting (Geant4 coding style guide)
   - Test suite to run before submission
   - MR conventions (target branch, label, reviewer assignment)
   - Estimated review timeline
5. Identify which Geant4 reviewers are likely to assign for hot-path patches
   (Apostolakis for tracking/transport; Asai for build/CMake; Wright for
   physics processes; etc. — confirm from CONTRIBUTORS or recent MRs).
6. Pick **one trivial documentation-only fix** as the first MR to test the
   submission pipeline end-to-end. Examples: a typo in a comment, a missing
   `final` keyword on a class that should clearly be final, a deprecated
   header include. The goal is to walk the submission process before any
   real performance patch goes through it.
7. Commit fork URL + branch name + first-MR-target into
   `docs/strategies/g4-upstream-process.md`.
8. Mark `g4-fork-bootstrap` DONE.

## Acceptance

- Geant4 fork exists at both local and LUNARC paths
- `accel/master` branch is checked out and pushed to GitHub mirror
- LUNARC build of vanilla Geant4 succeeds (smoke test)
- `docs/strategies/g4-upstream-process.md` documents the contribution
  workflow with concrete next steps
- A throwaway first-MR target is identified (and ideally already submitted
  to validate the pipeline)

## Stop condition

After committing the strategy doc, stop.
