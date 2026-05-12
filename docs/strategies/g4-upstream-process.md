# Geant4 upstream contribution process for G4GPU hot-path patches

## Purpose

This note closes the `g4-fork-bootstrap` compact iteration by recording the
upstream contribution path for CPU-only Geant4 optimizations. GPU-only or risky
work stays in `/Volumes/MyDrive/nnbar/geant4-gpu/`; CPU-only improvements that
can benefit all Geant4 users should move through the Geant4 upstream workflow
instead of remaining in `libG4Accel`.

## Fork and branch state

- Local source tree: `/Volumes/MyDrive/nnbar/geant4-fork/`
- LUNARC source tree: `/projects/hep/fs10/shared/nnbar/billy/geant4-fork/`
- Baseline tag: `v11.2.2`
- Working branch: `accel/master`
- Private GitHub mirror remote: `https://github.com/SzeChunYiu/geant4-accel.git`
- Upstream source remote: `https://gitlab.cern.ch/geant4/geant4.git`

Fresh verification on 2026-05-12 found both local and LUNARC trees checked out
on `accel/master` at the `v11.2.2` tag, with branch tracking the private GitHub
mirror. The LUNARC tree has an untracked `build/` directory only.

## Contribution routes

Geant4 currently exposes two practical routes for this work:

1. **External-user public PR path** — submit a normal GitHub pull request to
   `Geant4/geant4`. Use this for small, sporadic fixes. The public guide says a
   single PR must cover one topic only; uncorrelated changes across modules are
   not considered.
2. **Contributor / collaboration GitLab path** — for sustained hot-path work,
   request contributor status through the spokesperson, deputy spokesperson,
   and relevant Working Group coordinator. Accepted contributors receive CERN
   account access to the development GitLab repository. Mature work is then
   submitted as GitLab merge requests; continuous testing runs automatically,
   and satisfactory MRs can be selected for nightly testing by the shifter.

Simple bug fixes should still open or reference an official Bugzilla issue when
appropriate. User questions and feature-request discussion belong on the Geant4
Forum before they become code changes.

## Coding and formatting rules

- Keep each patch one-topic and module-local.
- Follow the repository `.clang-format` for C++ formatting.
- Follow Geant4 coding guidelines: prefer Geant4 types and stream aliases
  (`G4String`, `G4cout`, `G4cerr`, `G4endl`), avoid global variables, avoid
  hard-coded numbers, use explicit access specifiers, and keep one class or
  related class group per header/source pair.
- For examples, also follow the example-specific guidance: no tabs, avoid lines
  over 100 characters when practical, use `override` for overriding virtual
  functions, and document macros/README changes.
- Do not mix style-only, documentation-only, physics, and performance changes
  in the same PR/MR.

## Tests before submission

For every upstreamable performance patch:

1. Rebase a topic branch on the current public Geant4 target branch (for public
   PRs) or the appropriate development GitLab branch (for contributor MRs).
2. Build the vanilla fork on LUNARC in Release mode with multithreading enabled.
3. Build at least one canonical example that exercises the changed subsystem;
   for the bootstrap smoke test, Basic Example B1 built successfully against the
   LUNARC build tree.
4. Run focused tests/examples for the touched subsystem, with fixed seeds for
   physics-sensitive or performance-sensitive changes.
5. For hot-path changes, attach before/after timing and correctness evidence:
   fixed seed, input macro, compiler, CPU/GPU node type if relevant, Geant4 tag,
   command, wall time, and physics-output comparison.
6. Let upstream CI/continuous testing run on the PR/MR and respond to any
   failures before requesting deeper review or nightly testing.

Bootstrap verification evidence:

```text
LUNARC vanilla Geant4 build: cmake --build build -j8 completed with
[100%] Built target G4physicslists.

LUNARC Basic Example B1 smoke build: configured with
-DGeant4_DIR=/projects/hep/fs10/shared/nnbar/billy/geant4-fork/build
-DWITH_GEANT4_UIVIS=OFF and completed with [100%] Built target exampleB1.
```

## Likely reviewers / owners by area

The checked-out Geant4 repository contains `.gitlab/CODEOWNERS`, which maps
subsystems to Working Group coordinator handles. Likely initial reviewers for
G4GPU-related upstream patches are:

- CMake / build / global infrastructure: `@bmorgan`, `@gunter`, `@gcosmo`
- Geometry and transportation: `@gcosmo`, `@japost`
- Tracking: `@tsasaki`, `@shokada`, `@asaim`
- Track and particles: `@kurashige`, `@shokada`, `@asaim`
- Electromagnetic physics: `@vnivanch`, `@mnovak`, `@dsawkey`
- Hadronic physics: `@ribon`, `@dwright`, `@vnivanch`, plus model-specific
  owners listed in `.gitlab/CODEOWNERS`
- Physics lists: `@gunter`, `@wenzel`, `@ribon`, `@vnivanch`
- Examples used as benchmarks: `@ihrivnac`, `@ahoward`, and per-example owners

Treat these as reviewer-routing hints only; the public PR will be examined by a
responsible Geant4 developer, and GitLab MR ownership may be reassigned by the
collaboration.

## Expected review timeline

No public SLA is documented for GitHub PR review. For contributor status, the
policy says acceptance or rejection should arrive within a few working days.
After GitLab access exists, MR timing depends on continuous-testing results,
shifter selection for nightly testing, Working Group availability, and the
physics-validation burden of the change. Documentation-only or typo-only PRs
should be treated as pipeline tests, not as representative timing for real
hot-path patches.

## First MR target to test the pipeline

Use a documentation-only public GitHub PR that changes exactly one typo in the
repository README:

- File: `README.rst`
- Current text: `Category and Section relevent to your problem`
- Proposed text: `Category and Section relevant to your problem`
- Scope: documentation typo only; no code, examples, physics, build, or data
  changes.

Suggested commands after adding a public GitHub remote/fork:

```bash
cd /Volumes/MyDrive/nnbar/geant4-fork
git remote add public https://github.com/Geant4/geant4.git  # once only
git fetch public master
git checkout -b docs/fix-readme-relevant-typo public/master
python3 - <<PY
from pathlib import Path
p = Path("README.rst")
s = p.read_text()
p.write_text(s.replace("Category and Section relevent to your problem",
                       "Category and Section relevant to your problem"))
PY
git diff -- README.rst
git commit -am "docs: fix README typo"
git push github docs/fix-readme-relevant-typo
```

If the private mirror cannot be used as a fork source for a public PR, create or
select a normal GitHub fork of `Geant4/geant4`, push the same branch there, and
open the PR against `Geant4/geant4:master`.

## Sources

- Geant4 contribution guide: https://geant4.web.cern.ch/contributing/
- Geant4 public repository `CONTRIBUTING.rst`: https://github.com/Geant4/geant4/blob/master/CONTRIBUTING.rst
- Geant4 policies and software-development procedures: https://geant4.web.cern.ch/collaboration/policies/
- Geant4 contributor-status policy: https://www.geant4.org/collaboration/policies/contributors
- Geant4 coding guidelines: https://geant4-internal.web.cern.ch/collaboration/coding_guidelines
- Geant4 example coding guidelines: https://geant4.web.cern.ch/collaboration/working_groups/novextExamples/codingGuidelines.v2.2.html
