# G4GPU Celeritas job 3047497 pending monitor

Date: 2026-05-12 11:13 CEST
Lane: worker-3 / G4GPU isolated
Task: MCAccel competitor benchmarks — Celeritas rerun monitor

## Purpose

This compact-safe iteration monitors the already-submitted Celeritas A40 rerun
(job 3047497) and records evidence without submitting, cancelling, or modifying
any benchmark job. The Celeritas baseline remains `QUEUED`; no timing or
throughput is promoted until `results/results.parquet` exists.

## Guardrails checked

- LUNARC socket guard ran before the SSH checks and reported `Connected`.
- No local `cmake`, compiler, CUDA, Geant4/G4GPU executable, or SLURM command
  was run.
- No new SLURM job was submitted.
- No NNBAR production path was edited.

## Scheduler evidence

Command summary:

```text
squeue -j 3047497 -o "%.10i %.24j %.10T %.12M %.12l %.8D %.24R %.8q"
sacct -j 3047497 -X --format=JobID,JobName%30,State,Elapsed,Start,End,ExitCode,NodeList%20 -P
scontrol show job 3047497
```

Observed state:

```text
JOBID      NAME                 STATE      TIME   TIME_LIMIT  NODES  NODELIST(REASON)  QOS
3047497    mcaccel-celeritas    PENDING    0:00   2:00:00     1      (Priority)        overrun

JobID|JobName|State|Elapsed|Start|End|ExitCode|NodeList
3047497|mcaccel-celeritas|PENDING|00:00:00|Unknown|Unknown|0:0|None assigned
```

Selected `scontrol show job 3047497` fields:

```text
JobName=mcaccel-celeritas
Account=lu2026-2-51
JobState=PENDING
Reason=Priority
RunTime=00:00:00
TimeLimit=02:00:00
SubmitTime=2026-05-12T08:45:15
EligibleTime=2026-05-12T08:45:15
StartTime=2026-05-13T07:58:30
EndTime=2026-05-13T09:58:30
Partition=gpua40
NumNodes=1
Command=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/build-fixed-20260512.sh
WorkDir=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas
StdErr=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/slurm/celeritas-3047497.err
StdOut=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/slurm/celeritas-3047497.out
```

The only active G4GPU-related jobs in `squeue -u scyiu` were the pending
Celeritas rerun 3047497 and historical V7 shakedown 3047502; neither had begun
running.

## Remote file evidence

Work directory:

```text
/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas
```

The corrected Celeritas rerun script still exists at the scheduler command path:

```text
-rwx--x--x 1 scyiu hep 6894 May 12 08:40 build-fixed-20260512.sh
aa02355926582c49846661482cb9d8ede87b698ad263d23e62229492636e4104  build-fixed-20260512.sh
```

Expected job outputs are still absent because the job has not allocated a node:

```text
MISSING slurm/celeritas-3047497.out
MISSING slurm/celeritas-3047497.err
MISSING results/results.parquet
```

Older Celeritas logs remain only for prior jobs 3041372 and 3041282; no
3047497 stdout/stderr file was present in the remote work directory at this
refresh.

## Disposition

Keep `MCAccel competitor benchmarks` in `RUNNING` state. The next compact-safe
worker-3 action is another read-only monitor after the scheduler estimated start
window, or a results-collection iteration if job 3047497 completes and produces
`results/results.parquet`.

## Refresh: 2026-05-12 11:46 CEST

The required LUNARC socket guard reported `Connected` before the read-only SSH
queries. Job 3047497 is still waiting for a GPU allocation; no benchmark result
has been produced and no new job was submitted.

```text
JOBID      NAME                 STATE      TIME   TIME_LIMIT  NODES  NODELIST(REASON)  QOS
3047497    mcaccel-celeritas    PENDING    0:00   2:00:00     1      (Priority)        overrun

JobID|JobName|State|Elapsed|Start|End|ExitCode|NodeList
3047497|mcaccel-celeritas|PENDING|00:00:00|Unknown|Unknown|0:0|None assigned

JobState=PENDING
Reason=Priority
StartTime=2026-05-13T07:58:30
EndTime=2026-05-13T09:58:30
SchedNodeList=cg06
Command=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/build-fixed-20260512.sh
StdErr=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/slurm/celeritas-3047497.err
StdOut=/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/slurm/celeritas-3047497.out
```

Remote file checks were unchanged from the 11:13 refresh:

```text
-rwx--x--x 1 scyiu hep 6894 May 12 08:40 build-fixed-20260512.sh
aa02355926582c49846661482cb9d8ede87b698ad263d23e62229492636e4104  build-fixed-20260512.sh
MISSING slurm/celeritas-3047497.out
MISSING slurm/celeritas-3047497.err
MISSING results/results.parquet
```

Disposition remains unchanged: keep the Celeritas rerun in `QUEUED`/external
scheduler wait, keep `MCAccel competitor benchmarks` in `RUNNING`, and do not
collect or promote timing until `results/results.parquet` exists.
