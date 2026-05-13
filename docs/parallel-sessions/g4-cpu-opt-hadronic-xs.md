# Lane: g4-cpu-opt-hadronic-xs

## Role

You are an isolated Geant4 CPU optimization worker. You implement fixes in the
`geant4-fork` repo (`/Volumes/MyDrive/nnbar/geant4-fork/`) only. You do NOT
modify any NNBAR production simulation code, `nnbar_reconstruction/`,
`NNBAR_Detector/`, SLURM scripts, or production data.

## Goal

Optimize hadronic cross-section lookup in `G4CrossSectionDataStore` and
memoize the nuclear-radius / log-energy interpolation in the Glauber-Gribov
cross-section model. This targets BD entries BD-geant4-122, BD-geant4-123,
BD-geant4-125, and BD-geant4-126 from
`docs/reports/g4_bottleneck_database_hadronic_proton.md`.

The change feeds the **CPC/JINST paper on vanilla Geant4 CPU speedup**.
Expected speedup in hadronic cross-section evaluation: 1.5–3× for inelastic
cross-section lookups in high-energy hadron transport.

## Repos and branches

| Repo | Path | Branch |
|------|------|--------|
| Geant4 fork (write here) | `/Volumes/MyDrive/nnbar/geant4-fork/` | `opt/hadronic-xs-cache` |
| Geant4 11.2.2 reference (read-only) | `/Volumes/MyDrive/nnbar/nnbar/simulation/GEANT4_Packages/src/geant4-v11.2.2/source/` | — |
| Simulation repo (write reports only) | `/Volumes/MyDrive/nnbar/nnbar/simulation/` | current |

**Working branch:** create `opt/hadronic-xs-cache` off `accel/master`.
Push to `SzeChunYiu/geant4-accel` when done.

## Required reading (before implementing)

1. `docs/reports/g4_bottleneck_database_hadronic_proton.md` — read
   BD-geant4-122, BD-geant4-123, BD-geant4-125, and BD-geant4-126 in full.
2. Reference tree files to read line by line:
   - `source/processes/hadronic/cross_sections/src/G4CrossSectionDataStore.cc`
   - `source/processes/hadronic/cross_sections/include/G4CrossSectionDataStore.hh`
   - Look for `G4BGGNucleonInelasticXS.cc` and `G4GlauberGribovCrossSection.cc`
     (or `G4ComponentGGHadrNucleusXsc.cc`) under
     `source/processes/hadronic/cross_sections/src/`.
3. Existing patches on `accel/master` — confirm no prior hadronic-XS cache patch.

## Problem descriptions (from BD entries)

### BD-geant4-122 / 123 — Linear element scan in `G4CrossSectionDataStore`

`G4CrossSectionDataStore::GetCrossSection()` iterates over registered
cross-section datasets to find the applicable one for the current (particle,
material) pair. With 5–15 datasets registered, this is a short but repeated
linear scan executed on every hadronic GPIL call.

**Fix:** At run initialization, precompute a flat sorted vector of (material ID,
dataset index) pairs. At runtime, use a binary search or a pre-built hash map
`std::unordered_map<G4int, G4VCrossSectionDataSet*>` keyed by material PDG
element Z to locate the applicable dataset in O(1).

### BD-geant4-125 / 126 — Repeated nuclear-radius / log-energy in Glauber-Gribov

In `G4ComponentGGHadrNucleusXsc` (or equivalent), the nuclear radius
`R_A = r0 * A^(1/3)` and log-energy interpolation coefficients are recomputed
on every cross-section call for the same (Z, A, sqrt_s) triple. These
computations involve `std::pow`, `std::log`, and multi-step polynomial
evaluation.

**Fix:** Memoize `(Z, A, sqrt_s_bin)` → cross-section result using a flat hash
map. Use integer-binned `sqrt_s` (bin width configurable, default 10 MeV) as
the key to group nearby energies. Cache size 4096 entries with generation-based
invalidation (generation counter incremented at `BeginOfRun`).

## Implementation plan

### Step 1: Create branch

```bash
cd /Volumes/MyDrive/nnbar/geant4-fork
git checkout accel/master
git pull origin accel/master
git checkout -b opt/hadronic-xs-cache
```

### Step 2: Add material→dataset index in `G4CrossSectionDataStore`

In `G4CrossSectionDataStore.hh`, add:

```cpp
// Prebuilt material-element → dataset index cache (populated at BuildTable())
std::unordered_map<G4int /*element Z*/, G4int /*dataset index*/> fDataSetIndexCache;
G4bool fCacheBuilt = false;
void RebuildDataSetCache();
```

In `G4CrossSectionDataStore.cc`, implement:

```cpp
void G4CrossSectionDataStore::RebuildDataSetCache()
{
    fDataSetIndexCache.clear();
    for (G4int j = 0; j < (G4int)dataSetList.size(); ++j) {
        // For each dataset, record which element Zs it handles
        // (call IsZAApplicable or inspect the dataset applicability)
        // This is a conservative first pass: cache the *last* applicable
        // dataset for each Z (matching the current linear-scan semantics).
    }
    fCacheBuilt = true;
}
```

In `GetCrossSection()`, add at entry:

```cpp
if (!fCacheBuilt) RebuildDataSetCache();
G4int Z = theElement->GetZasInt();
auto it = fDataSetIndexCache.find(Z);
if (it != fDataSetIndexCache.end()) {
    G4VCrossSectionDataSet* ds = dataSetList[it->second];
    // Use cached dataset directly, skip linear scan
    return ds->GetCrossSection(dp, theElement, theMaterial);
}
// Fallback to linear scan for uncached elements
```

**Important:** The cache lookup must produce the identical dataset selection as
the original linear scan for all (particle, element, energy) combinations used
in the validation workload. Verify by running the scan on first access and
comparing.

### Step 3: Add Glauber-Gribov memoization cache

Locate the Glauber-Gribov cross-section class. In Geant4 11.2.2, this may be:
- `G4ComponentGGHadrNucleusXsc` in
  `source/processes/hadronic/cross_sections/src/`
- Or `G4GlauberGribovCrossSection.cc` — check which file exists.

In the header, add:

```cpp
#include <unordered_map>

struct G4GGXSKey {
    G4int Z, A;
    G4int sqrtS_MeV_bin;  // sqrt_s in MeV, divided by kBinWidth=10
    bool operator==(const G4GGXSKey& o) const {
        return Z==o.Z && A==o.A && sqrtS_MeV_bin==o.sqrtS_MeV_bin;
    }
};
struct G4GGXSKeyHash {
    std::size_t operator()(const G4GGXSKey& k) const {
        return (std::hash<G4int>()(k.Z) * 2654435761u)
             ^ (std::hash<G4int>()(k.A) * 40503u)
             ^ std::hash<G4int>()(k.sqrtS_MeV_bin);
    }
};

static constexpr G4int kGGXSCacheSize  = 4096;
static constexpr G4int kGGXSBinWidth   = 10;  // MeV
std::unordered_map<G4GGXSKey, G4double, G4GGXSKeyHash> fGGXSCache;
G4int fGGXSGeneration = 0;
```

In the cross-section evaluation method (identify from BD entry — likely
`GetInelasticHadronNucleonXsc` or similar), add:

```cpp
// Compute cache key
G4int sqrtS_bin = (G4int)(std::sqrt(s_GeV2) * 1000.0 / kGGXSBinWidth);
G4GGXSKey key{Z, A, sqrtS_bin};
auto it = fGGXSCache.find(key);
if (it != fGGXSCache.end()) return it->second;

// Cache miss: compute
G4double result = [existing computation];

// Insert (evict oldest if at capacity — simple: clear at capacity)
if ((G4int)fGGXSCache.size() >= kGGXSCacheSize) {
    fGGXSCache.clear();  // Simple full-clear; upgrade to LRU if needed
}
fGGXSCache[key] = result;
return result;
```

Add a `ClearCache()` method called from `BeginOfRunAction` or equivalent hook
to invalidate between runs.

### Step 4: Write the validation test

Create `tests/hadronic_xs/test_hadronic_xs_cache.cc` (or a macro + runner):

1. Configure Geant4 with `FTFP_BERT` physics list.
2. Run fixed-seed: 1,000 protons on an iron target at 1, 10, 100 GeV.
3. Record total inelastic cross-section for each energy.
4. Assert patched results match vanilla within 0.01%.

If a full Geant4 run is unavailable locally, write a unit test that:
- Instantiates `G4CrossSectionDataStore` with a mock material.
- Calls `GetCrossSection()` 10,000 times with the same arguments.
- Asserts identical return values from all calls (cache-hit correctness).
- Asserts that `GetCrossSection()` returns the same value with and without
  the cache for a range of elements.

### Step 5: Write the optimization report

Write `docs/reports/opt_hadronic_xs_cache_20260513.md` in the simulation repo:

```markdown
# Optimization report: hadronic cross-section cache

Date: 2026-05-13
Branch: opt/hadronic-xs-cache
Geant4 base: v11.2.2 (accel/master)
BD entries implemented: BD-geant4-122, BD-geant4-123, BD-geant4-125, BD-geant4-126

## Files changed

- `source/processes/hadronic/cross_sections/src/G4CrossSectionDataStore.cc`
- `source/processes/hadronic/cross_sections/include/G4CrossSectionDataStore.hh`
- `source/processes/hadronic/cross_sections/src/G4ComponentGGHadrNucleusXsc.cc`
  (or G4GlauberGribovCrossSection.cc — use whichever exists in v11.2.2)
- `source/processes/hadronic/cross_sections/include/G4ComponentGGHadrNucleusXsc.hh`

## Diff summary

[paste `git diff --stat`]

## Expected speedup

1.5–3× for hadronic XS evaluation in proton/neutron-heavy workloads.

## Validation result

[paste test output]

## Paper note

CPC/JINST vanilla Geant4 CPU paper.
```

### Step 6: Commit and push

```bash
cd /Volumes/MyDrive/nnbar/geant4-fork
git add source/processes/hadronic/cross_sections/ tests/
git commit -m "opt: cache hadronic XS dataset lookup and Glauber-Gribov memoization

- G4CrossSectionDataStore: prebuilt element->dataset index hash map
- G4ComponentGGHadrNucleusXsc: flat hash cache (4096) keyed by (Z,A,sqrtS_bin)
  with generation-based invalidation at BeginOfRun

Implements BD-geant4-122, BD-geant4-123, BD-geant4-125, BD-geant4-126.
CPC/JINST paper target."
git push -u origin opt/hadronic-xs-cache
```

## Verification checklist

Before marking DONE:

- [ ] `grep -r "NNBAR_Detector\|nnbar_reconstruction" source/` returns nothing
      in modified files.
- [ ] `cmake --build .` succeeds with no new warnings.
- [ ] Diff touches only `G4CrossSectionDataStore.*` and the Glauber-Gribov file.
- [ ] Proton-on-Fe total inelastic XS at 1, 10, 100 GeV matches vanilla within 0.01%.
- [ ] Report written to `docs/reports/opt_hadronic_xs_cache_20260513.md`.
- [ ] Branch pushed to `SzeChunYiu/geant4-accel`.

## Isolation rules

- Never modify `NNBAR_Detector/`, `nnbar_reconstruction/`, `slurm/`, macros.
- Do not include any NNBAR simulation header.
- Do not submit SLURM jobs.

## Paper context

This patch targets the **CPC/JINST paper on vanilla Geant4 CPU speedup**.

Key references:
- Korobeinikov 1987 (Glauber model review)
- Drepper 2007 *What Every Programmer Should Know About Memory*
- Mitzenmacher and Upfal 2005 *Probability and Computing* (hash-map load factor)
- Intel 2024 *Optimization Reference Manual* (cache-miss cost analysis)

## Stop condition

Stop after patched files compile, the fixed-seed test passes, the report is
written, and the branch is pushed. Do not implement other BD entries.
