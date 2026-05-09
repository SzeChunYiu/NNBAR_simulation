# Codex-supervisor harness for the NNBAR rebuild

Project-local configuration for the `codex-supervisor` tool living at
`/Users/billy/Desktop/projects/codex-supervisor/`. This directory holds:

- `codex-prompts.txt` — one prompt per parallel pane (lane).
- `start.sh` — launches the supervisor with this prompt set.
- `merge.sh` — merges a lane branch into `main`, locked to serialise
  concurrent calls.
- `lanes.md` — human-readable map: lane → branch → worktree → goal.

## Setup (already done by the rebuild plan-set bootstrap)

Each lane runs in its own git worktree:

```
/Volumes/MyDrive/nnbar/nnbar/
├── simulation/        (main worktree, branch: main)
├── simulation-L0/     (worktree, branch: lane/L0-sim-walkthrough)
├── simulation-L1/     (worktree, branch: lane/L1-reco-walkthrough)
├── simulation-L2/     (worktree, branch: lane/L2-io-macros)
└── simulation-L3/     (worktree, branch: lane/L3-foundations-code)
```

The four lanes are file-disjoint by design (see `lanes.md`); merges
into `main` cannot conflict.

## Workflow

```
                start.sh
                   │
                   ▼
       codex-supervisor (tmux, 4 panes)
        │      │      │      │
        L0     L1     L2     L3      (each in its worktree)
        │      │      │      │
        ▼      ▼      ▼      ▼
   commit on lane branch (per iteration)
        │      │      │      │
        ▼      ▼      ▼      ▼
   merge.sh lane/Lx                  (serialises via mkdir lock)
        │
        ▼
   main updated; lane keeps working
```

## Per-iteration cycle (each lane)

1. Make a small unit of progress (one builder, one function, one
   column-table, one module).
2. Stage and commit on the lane's branch.
3. Run pytest (lane L3 only) — must pass.
4. Run `bash /Volumes/MyDrive/nnbar/nnbar/simulation/scripts/codex-supervisor/merge.sh lane/Lx`.
5. Repeat.

## Conventions

- 500-line file cap per `CODING_STANDARDS.md` §1.
- Every code-touching commit has a paired DEC entry per plan 05 if
  it changes methodology.
- Branches are file-disjoint by lane; lanes do not edit each others'
  files.
- `main` is append-only; no force pushes, no history rewrites.

## Stopping

```
codex-supervisor stop          # kill all panes
codex-supervisor status        # check pane states
codex-supervisor logs -f       # tail the supervisor log
```

## References

- Upstream: <https://github.com/SzeChunYiu/codex-supervisor>
- Local: `/Users/billy/Desktop/projects/codex-supervisor/codex-supervisor.sh`
- Plan 06 — governance and review gates.
- Plan 53 — CI regression suite.
- `CODING_STANDARDS.md` — file-size + naming + import discipline.
