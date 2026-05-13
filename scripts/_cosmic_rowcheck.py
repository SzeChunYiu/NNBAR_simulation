"""Check parquet row counts for a cosmic shard output directory.

Called by monitor_jobs.sh with one positional arg:
  argv[1] = local directory to scan for *.parquet files
"""
import sys
import pathlib
import warnings

warnings.filterwarnings("ignore")

base = pathlib.Path(sys.argv[1])
try:
    import pandas as pd
except ImportError:
    print("  pandas not available — skipping row count check")
    sys.exit(0)

total = 0
for pq in sorted(base.rglob("*.parquet")):
    try:
        df = pd.read_parquet(pq)
        n = len(df)
        stub = " [STUB?]" if n < 10 else ""
        print(f"  {pq.relative_to(base)}: {n} rows{stub}")
        total += n
    except Exception as e:
        print(f"  {pq.relative_to(base)}: ERROR {e}")
print(f"  total rows: {total}")
