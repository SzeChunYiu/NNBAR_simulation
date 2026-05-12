# Vertex scan position check — r10 fixed-vertex sample

## Result

**PASS.** The local r10 fixed-vertex Parquet sample contains 500 rows with every generated particle at x = 10 cm and y = 0 cm.

Input file:
`build_lunarc/output/studies/pi0_vertex_scan_r10mev/Particle_output_0.parquet`

## Position statistics

| Quantity | Value (cm) | Expected | Check |
| --- | ---: | ---: | --- |
| mean(x) | 10 | 10 | pass |
| mean(y) | 0 | 0 | pass |
| RMS(x) about zero | 10 | 10 | pass |
| RMS(y) about zero | 0 | 0 | pass |
| residual RMS(x - 10 cm) | 0 | 0 | pass |
| residual RMS(y - 0 cm) | 0 | 0 | pass |
| population sigma(x) | 0 | 0 | pass |
| population sigma(y) | 0 | 0 | pass |

## Range and uniqueness checks

| Field | min (cm) | max (cm) | unique values |
| --- | ---: | ---: | ---: |
| x | 10 | 10 | 1 |
| y | 0 | 0 | 1 |

## Verification command

~~~bash
rtk proxy python - <<'PY'
from pathlib import Path
import math
import pandas as pd
p = Path('build_lunarc/output/studies/pi0_vertex_scan_r10mev/Particle_output_0.parquet')
df = pd.read_parquet(p)
print(len(df), df['x'].mean(), df['y'].mean())
print(math.sqrt(((df['x'] - 10.0) ** 2).mean()), math.sqrt((df['y'] ** 2).mean()))
PY
~~~

Observed output summary: `500 10 0` and residual RMS values `0 0`.

No SLURM job, simulation, or production data generation was run for this check.
