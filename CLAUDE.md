# NNBAR Simulation — Claude Working Rules

## CRITICAL: G4GPU isolation

The NNBAR simulation MUST NOT link against, call, or depend on the G4GPU R&D
project at any point. All thesis-critical runs use vanilla Geant4 only. See
`docs/policies/g4gpu-isolation.md` for the full policy and the physics-parity
gate that must pass before any switchover.

This rule overrides anything else in this file or in lane specs. If a task
appears to violate it, refuse the task and flag it to the planner.

## Never write to $HOME on LUNARC — use the work directory

LUNARC `$HOME` (`/home/scyiu/`) is quota-restricted and frequently full.
Never write any file, log, lock, flag, cache, or state under `~`/`$HOME`.
Always direct writes to the project work directory or per-user shared dir:

- Project work dir: `/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/`
- Per-user shared dir: `/projects/hep/fs10/shared/codex-tooling/per-user/scyiu/`

If a tool defaults to `$HOME` for state (codex-supervisor's `.disabled`
flags, `.codex` config, gh/git config, npm cache, etc.), redirect via env
vars (`CODEX_HOME`, `GH_CONFIG_DIR`, `GIT_CONFIG_GLOBAL`, `NPM_CONFIG_*`,
etc. — already wired in `env-shared.sh`). If a script hardcodes `$HOME`
writes that can't be redirected, treat the quota-exceeded message as
benign and proceed; never delete files in `$HOME` to make space without
explicit user OK.

## Do not gate on credit/limit reset dates

Never refuse or defer an action because of a credit-reset date, rate-limit
window, or "wait until X" timer. If the user asks for a restart or any
cluster action, just do it. Mentioning credits/limits as a blocker is
explicitly disallowed.

## Role Split

**Claude Code:** Project manager. Plans work, reviews codex output, handles LUNARC/cluster operations, directs next steps. Does NOT write production code.

**codex-supervisor:** All code implementation.
- Tool: `/Users/billy/Desktop/projects/codex-supervisor/codex-supervisor.sh`
- One lane per independent task. Codex agents write and iterate on code.

## Codex Prompt Format

**ALL codex-supervisor prompts MUST start with `/goal`.** This is non-negotiable.

- First word: `/goal`
- Max 50 words total
- No implementation details in the prompt body — all details go in a companion `.md` spec file that codex reads
- Example: `/goal implement data_pipeline package per spec in nnbar_reconstruction/data_pipeline/SPEC.md`

## Workflow

1. Claude analyses the problem, writes a spec `.md` file in the relevant directory.
2. Claude gives user a short `/goal` prompt (≤50 words) to paste into codex-supervisor.
3. Codex implements. Claude reviews the output and plans the next task.

## What Claude Handles Directly

- SSH to LUNARC (`ssh lunarc "..."`)
- SLURM job submission and monitoring
- rsync / file transfer between local and LUNARC
- Git operations
- Reading and understanding code
- Writing specs and prompts for codex-supervisor lanes

## What Goes to codex-supervisor

- Any new Python file in `nnbar_reconstruction/`
- Any modification to existing reconstruction code
- New SLURM scripts or shell scripts
- Tests

## Key Paths

| Location | Path |
|---|---|
| Local simulation repo | `/Volumes/MyDrive/nnbar/nnbar/simulation/` |
| LUNARC project dir | `/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/` |
| LUNARC Geant4 install | Find with: `find /projects/hep -name 'geant4.sh' 2>/dev/null` |
| LUNARC conda envs | `/projects/hep/fs10/shared/nnbar/billy/packages/` |
| codex-supervisor | `/Users/billy/Desktop/projects/codex-supervisor/codex-supervisor.sh` |
| MCPL input file | `/Volumes/MyDrive/nnbar/nnbar/simulation/data/mcpl/NNBAR_rwag_signal_GBL_jbar_100k_9009.mcpl` |

## LUNARC Connection

```bash
ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh
```

SLURM account: `lu2026-2-51` | Partition: `lu48` (CPU), `gpua40` (GPU)

## Current State (2026-05-10)

- `NNBAR_Detector/` C++ code synced to LUNARC at `NNBAR_Detector_sim/`
- MCPL signal file uploaded to `NNBAR_Detector_sim/mcpl_files/`
- Build job failed: Geant4 path `/projects/hep/fs12/nnbar/software/geant4-MT/install/` does not exist — correct path needs to be found
- `nnbar_reconstruction/data_pipeline/` does not exist yet — pending codex-supervisor implementation
- `nnbar_reconstruction/tracking/clustering_config.yaml` does not exist yet — pending
