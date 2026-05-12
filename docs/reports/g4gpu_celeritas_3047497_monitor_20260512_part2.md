# G4GPU Celeritas job 3047497 pending monitor — part 2

Date: 2026-05-12 13:09 CEST
Lane: worker-3 / G4GPU isolated, lane-swapped from `codex-tasks/g4gpu/worker-2.txt`
Task: MCAccel competitor benchmarks — Celeritas rerun monitor rollover

## Rollover rationale

The original monitor report
`docs/reports/g4gpu_celeritas_3047497_monitor_20260512.md` is preserved
unchanged at 455 lines after the 12:59 CEST refresh. This part-2 report is the
continuation file for later refreshes so the original evidence file stays below
the 500-line cap. No earlier evidence was deleted or rewritten.

## Guardrails checked

- The LUNARC socket guard ran before the SSH status check; it refreshed the
  persistent socket and verified it active.
- The refresh was read-only: no SLURM job was submitted, cancelled, or modified.
- No local `cmake`, compiler, CUDA, Geant4/G4GPU executable, or SLURM command
  was run.
- No NNBAR production path was edited.

## Refresh: 2026-05-12 13:09 CEST

Job 3047497 remains scheduler-pending. No stdout, stderr, or benchmark Parquet
result exists, so Celeritas baseline timing remains unpromoted.

```text
REMOTE_DATE=2026-05-12 13:09:10 CEST

JOBID      NAME                    STATE        TIME   TIME_LIMIT  NODES  NODELIST(REASON)  QOS
3047497    mcaccel-celeritas       PENDING      0:00   2:00:00     1      (Priority)        parrun

JobID|JobName|State|Elapsed|Start|End|ExitCode|NodeList
3047497|mcaccel-celeritas|PENDING|00:00:00|Unknown|Unknown|0:0|None assigned

JobName=mcaccel-celeritas
Account=lu2026-2-51
QOS=parrun
JobState=PENDING
Reason=Priority
ExitCode=0:0
RunTime=00:00:00
TimeLimit=02:00:00
SubmitTime=2026-05-12T08:45:15
EligibleTime=2026-05-12T08:45:15
StartTime=2026-05-13T21:58:30
EndTime=2026-05-13T23:58:30
Partition=gpua40
SchedNodeList=cg03
NumNodes=1
Command=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/build-fixed-20260512.sh
WorkDir=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas
StdErr=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/slurm/celeritas-3047497.err
StdOut=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/slurm/celeritas-3047497.out
```

Active G4GPU-related jobs still include the pending Celeritas rerun 3047497 and
pending historical V7 shakedown 3047502. The `mcaccel-sup` holder jobs were
running on `cx08`, `cx12`, and `cx04`; no Celeritas job had allocated a GPU
node.

Remote file checks:

```text
-rwx--x--x 1 scyiu hep 6894 May 12 08:40 build-fixed-20260512.sh
aa02355926582c49846661482cb9d8ede87b698ad263d23e62229492636e4104  build-fixed-20260512.sh
MISSING slurm/celeritas-3047497.out
MISSING slurm/celeritas-3047497.err
MISSING results/results.parquet
```

## Disposition

Keep `MCAccel competitor benchmarks` in `RUNNING`. Future monitor refreshes for
job 3047497 should append to this part-2 report unless stdout/stderr appears or
`results/results.parquet` exists, in which case collect that evidence in a
terminal result/blocker report before promoting any timing.


## Refresh: 2026-05-12 13:40 CEST

Job 3047497 remains scheduler-pending on `Priority`. The LUNARC socket guard
reported `SOCKET=Connected` before the read-only SSH checks. No stdout, stderr,
or `results/results.parquet` exists, so no Celeritas baseline timing has been
captured or promoted.

```text
REMOTE_DATE=2026-05-12 13:40:01 CEST

JOBID      NAME                    STATE        TIME   TIME_LIMIT  NODES  NODELIST(REASON)  QOS
3047497    mcaccel-celeritas       PENDING      0:00   2:00:00     1      (Priority)        parrun

Active G4GPU-related jobs:
3047497    mcaccel-celeritas       PENDING      0:00     2:00:00   1      (Priority)        parrun
3047502    g4gpu-v7-shake          PENDING      0:00     2:00:00   1      (Priority)        parrun
3047628    mcaccel-sup             RUNNING      2:55:49  5-00:00:00 1     cx08              normal
3047941    mcaccel-sup             RUNNING      56:06    5-00:00:00 1     cx12              parrun
3047906    mcaccel-sup             RUNNING      1:01:28  5-00:00:00 1     cx04              parrun

JobID|JobName|State|Elapsed|Start|End|ExitCode|NodeList
3047497|mcaccel-celeritas|PENDING|00:00:00|Unknown|Unknown|0:0|None assigned

JobName=mcaccel-celeritas
Account=lu2026-2-51
QOS=parrun
JobState=PENDING
Reason=Priority
ExitCode=0:0
RunTime=00:00:00
TimeLimit=02:00:00
SubmitTime=2026-05-12T08:45:15
EligibleTime=2026-05-12T08:45:15
StartTime=2026-05-13T21:58:30
EndTime=2026-05-13T23:58:30
Partition=gpua40
SchedNodeList=cg03
NumNodes=1
Command=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/build-fixed-20260512.sh
WorkDir=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas
StdErr=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/slurm/celeritas-3047497.err
StdOut=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/slurm/celeritas-3047497.out
```

Remote file checks:

```text
-rwx--x--x 1 scyiu hep 6894 May 12 08:40 build-fixed-20260512.sh
aa02355926582c49846661482cb9d8ede87b698ad263d23e62229492636e4104  build-fixed-20260512.sh
MISSING slurm/celeritas-3047497.out
MISSING slurm/celeritas-3047497.err
MISSING results/results.parquet
```

Disposition unchanged: keep `MCAccel competitor benchmarks` in `RUNNING`; this
iteration submitted no new job, ran no build/test executable, and did not touch
NNBAR production paths.

## Refresh: 2026-05-12 13:45 CEST

Job 3047497 remains scheduler-pending on `Priority`. The LUNARC socket guard
reported `SOCKET=Connected` before the read-only SSH checks. No stdout, stderr,
or `results/results.parquet` exists, so no Celeritas baseline timing has been
captured or promoted.

```text
REMOTE_DATE=2026-05-12 13:45:41 CEST

JOBID      NAME                    STATE        TIME   TIME_LIMIT  NODES  NODELIST(REASON)  QOS
3047497    mcaccel-celeritas       PENDING      0:00   2:00:00     1      (Priority)        parrun

Active G4GPU-related jobs:
3047497    mcaccel-celeritas       PENDING      0:00     2:00:00   1      (Priority)        parrun
3047502    g4gpu-v7-shake          PENDING      0:00     2:00:00   1      (Priority)        parrun
3047628    mcaccel-sup             RUNNING      3:01:29  5-00:00:00 1     cx08              normal
3047941    mcaccel-sup             RUNNING      1:01:46  5-00:00:00 1     cx12              parrun
3047906    mcaccel-sup             RUNNING      1:07:08  5-00:00:00 1     cx04              parrun

JobID|JobName|State|Elapsed|Start|End|ExitCode|NodeList
3047497|mcaccel-celeritas|PENDING|00:00:00|Unknown|Unknown|0:0|None assigned

JobName=mcaccel-celeritas
Account=lu2026-2-51
QOS=parrun
JobState=PENDING
Reason=Priority
ExitCode=0:0
RunTime=00:00:00
TimeLimit=02:00:00
SubmitTime=2026-05-12T08:45:15
EligibleTime=2026-05-12T08:45:15
StartTime=2026-05-13T21:58:30
EndTime=2026-05-13T23:58:30
Partition=gpua40
SchedNodeList=cg03
NumNodes=1
Command=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/build-fixed-20260512.sh
WorkDir=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas
StdErr=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/slurm/celeritas-3047497.err
StdOut=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/slurm/celeritas-3047497.out
```

Remote file checks:

```text
-rwx--x--x 1 scyiu hep 6894 May 12 08:40 build-fixed-20260512.sh
aa02355926582c49846661482cb9d8ede87b698ad263d23e62229492636e4104  build-fixed-20260512.sh
MISSING slurm/celeritas-3047497.out
MISSING slurm/celeritas-3047497.err
MISSING results/results.parquet
```

Disposition unchanged: keep `MCAccel competitor benchmarks` in `RUNNING`; this
iteration submitted no new job, ran no build/test executable, and did not touch
NNBAR production paths.
