# Lane: g4-cpu-opt-hp-neutron

## Role

You are an isolated Geant4 CPU optimization worker. You implement fixes in the
`geant4-fork` repo (`/Volumes/MyDrive/nnbar/geant4-fork/`) only. You do NOT
modify any NNBAR production simulation code, `nnbar_reconstruction/`,
`NNBAR_Detector/`, SLURM scripts, or production data.

## Goal

Optimize the HP neutron cross-section lookup and sampling in
`G4NeutronHPVector` by replacing linear scan with `std::lower_bound`, adding a
precomputed CDF lookup table for `Sample()`, and adding an LRU cache for
Doppler-broadened elastic cross-sections. This targets BD entries
BD-geant4-071, BD-geant4-072, and BD-geant4-074 from
`docs/reports/g4_bottleneck_database_neutron_hp.md`.

The change feeds the **CPC/JINST paper on vanilla Geant4 CPU speedup**.
Expected speedup in neutron-HP-dominated workloads: 2–4× for the cross-section
lookup path.

## Repos and branches

| Repo | Path | Branch |
|------|------|--------|
| Geant4 fork (write here) | `/Volumes/MyDrive/nnbar/geant4-fork/` | `opt/hp-neutron-lookup` |
| Geant4 11.2.2 reference (read-only) | `/Volumes/MyDrive/nnbar/nnbar/simulation/GEANT4_Packages/src/geant4-v11.2.2/source/` | — |
| Simulation repo (write reports only) | `/Volumes/MyDrive/nnbar/nnbar/simulation/` | current |

**Working branch:** create `opt/hp-neutron-lookup` off `accel/master`.
Push to `SzeChunYiu/geant4-accel` when done.

## Required reading (before implementing)

1. `docs/reports/g4_bottleneck_database_neutron_hp.md` — read BD-geant4-071,
   BD-geant4-072, and BD-geant4-074 in full.
2. Reference tree files to read line by line:
   - `source/processes/hadronic/models/neutron_hp/src/G4NeutronHPVector.cc`
   - `source/processes/hadronic/models/neutron_hp/include/G4NeutronHPVector.hh`
   - `source/processes/hadronic/models/neutron_hp/src/G4NeutronHPElastic.cc`
   - `source/processes/hadronic/models/neutron_hp/src/G4NeutronHPElasticData.cc`
3. Existing patches on `accel/master` in the fork — confirm no prior HP-neutron
   patch exists before adding yours.

## Problem descriptions (from BD entries)

### BD-geant4-071 — Linear scan in `G4NeutronHPVector::GetXsec()`

`G4NeutronHPVector::GetXsec(G4double energy)` performs a sequential scan over
the energy grid to find the interpolation bracket. With thermal-scattering data
grids of 1,000–20,000 points, this scan is O(N) per call. It is invoked on
every GPIL evaluation for every neutron step in HP mode.

**Fix:** Replace the sequential scan with `std::lower_bound` on the sorted
energy array, reducing to O(log N).

### BD-geant4-072 — Rejection loop in `G4NeutronHPVector::Sample()`

`G4NeutronHPVector::Sample()` uses a rejection method to sample from a tabulated
distribution. The rejection loop draws random numbers until a candidate falls
under the PDF envelope. For peaked distributions (thermal resonances), the
acceptance rate can be < 20%, causing 5–10 random-number calls per sample.

**Fix:** Precompute a CDF from the tabulated PDF and implement inverse-CDF
sampling (Walker alias method or binary-search on the CDF). Zero rejection
overhead; exactly 1–2 random numbers per sample.

### BD-geant4-074 — Repeated Doppler-broadening computation

`G4NeutronHPElasticData` recomputes Doppler-broadened elastic cross-sections
for each (isotope, temperature) pair on every call without caching. The
broadening integral is expensive (Gaussian convolution over the energy grid).

**Fix:** Add an LRU cache keyed by `(Z, A, temperature_K)` with capacity 256.
On cache hit, return the cached broadened cross-section directly. Invalidate
on temperature change.

## Implementation plan

### Step 1: Create branch

```bash
cd /Volumes/MyDrive/nnbar/geant4-fork
git checkout accel/master
git pull origin accel/master
git checkout -b opt/hp-neutron-lookup
```

### Step 2: Replace linear scan in `G4NeutronHPVector::GetXsec()`

Locate the sequential scan loop in `G4NeutronHPVector.cc`. The pattern is
typically:

```cpp
for (G4int i = 0; i < nEntries; i++) {
    if (theData[i].GetX() > energy) { ... break; }
}
```

Replace with:

```cpp
// Binary search: theData[].GetX() must be sorted ascending (guaranteed by HP data format).
G4int lo = 0, hi = nEntries - 1;
while (lo < hi) {
    G4int mid = (lo + hi) / 2;
    if (theData[mid].GetX() < energy) lo = mid + 1;
    else hi = mid;
}
// lo is now the lower bracket index
```

Or use `std::lower_bound` if `theData` iterators are available:

```cpp
auto it = std::lower_bound(theData, theData + nEntries, energy,
    [](const G4NeutronHPDataPoint& dp, G4double e) {
        return dp.GetX() < e;
    });
```

Verify that `nEntries == 0` and boundary cases (energy below/above grid) are
handled correctly before and after the change.

### Step 3: Add CDF precomputation to `G4NeutronHPVector`

In `G4NeutronHPVector.hh`, add:

```cpp
// Precomputed CDF for inverse-CDF sampling (populated on first Sample() call)
std::vector<G4double> fCDF;
bool                  fCDFBuilt = false;
void BuildCDF();
```

In `G4NeutronHPVector.cc`, implement:

```cpp
void G4NeutronHPVector::BuildCDF()
{
    fCDF.resize(nEntries);
    fCDF[0] = 0.0;
    for (G4int i = 1; i < nEntries; ++i) {
        // Trapezoidal rule integration of the tabulated PDF
        G4double dx    = theData[i].GetX()   - theData[i-1].GetX();
        G4double avgY  = 0.5 * (theData[i].GetY() + theData[i-1].GetY());
        fCDF[i]        = fCDF[i-1] + dx * avgY;
    }
    // Normalise
    if (fCDF[nEntries-1] > 0.0) {
        G4double norm = 1.0 / fCDF[nEntries-1];
        for (auto& c : fCDF) c *= norm;
    }
    fCDFBuilt = true;
}
```

In `Sample()`, replace the rejection loop with:

```cpp
if (!fCDFBuilt) BuildCDF();
G4double r = G4UniformRand();
// Binary search on CDF
auto it = std::lower_bound(fCDF.begin(), fCDF.end(), r);
G4int idx = std::max(0, (G4int)(it - fCDF.begin()) - 1);
// Linear interpolation within the bin
G4double x0 = theData[idx].GetX(),   x1 = theData[idx+1].GetX();
G4double c0 = fCDF[idx],             c1 = fCDF[idx+1];
G4double t  = (c1 > c0) ? (r - c0) / (c1 - c0) : 0.0;
return x0 + t * (x1 - x0);
```

Handle edge cases: `idx >= nEntries-1`, `fCDF` all-zero.

### Step 4: Add LRU cache to `G4NeutronHPElasticData`

In `G4NeutronHPElasticData.hh`, add:

```cpp
#include <unordered_map>
#include <list>
#include <utility>

struct G4HPDopplerKey {
    G4int Z, A;
    G4double T_K;  // temperature in Kelvin, rounded to nearest 1 K for key
    bool operator==(const G4HPDopplerKey& o) const {
        return Z == o.Z && A == o.A && T_K == o.T_K;
    }
};
struct G4HPDopplerKeyHash {
    std::size_t operator()(const G4HPDopplerKey& k) const {
        return std::hash<G4int>()(k.Z) ^ (std::hash<G4int>()(k.A) << 16)
             ^ std::hash<G4double>()(k.T_K);
    }
};

static constexpr G4int kDopplerCacheSize = 256;
using DopplerCacheMap =
    std::unordered_map<G4HPDopplerKey,
        std::pair<std::list<G4HPDopplerKey>::iterator, G4double>,
        G4HPDopplerKeyHash>;
std::list<G4HPDopplerKey> fDopplerLRUList;
DopplerCacheMap           fDopplerCache;
```

In the Doppler-broadening method (identify exact function name from the source),
add a cache lookup before the expensive computation:

```cpp
G4HPDopplerKey key{Z, A, std::round(temperature_K)};
auto it = fDopplerCache.find(key);
if (it != fDopplerCache.end()) {
    // LRU hit: move to front
    fDopplerLRUList.splice(fDopplerLRUList.begin(),
                           fDopplerLRUList, it->second.first);
    return it->second.second;
}
// Cache miss: compute
G4double result = [existing Doppler broadening code];
// Insert into cache
if ((G4int)fDopplerCache.size() >= kDopplerCacheSize) {
    // Evict LRU tail
    auto lru = fDopplerLRUList.back();
    fDopplerCache.erase(lru);
    fDopplerLRUList.pop_back();
}
fDopplerLRUList.push_front(key);
fDopplerCache[key] = {fDopplerLRUList.begin(), result};
return result;
```

### Step 5: Write the validation test

Create `tests/neutron_hp/test_hp_neutron_lookup.cc` that:

1. Loads HP neutron data (requires `G4NEUTRONHPDATA` env var pointing to data).
2. Runs a fixed-seed `Hadr01`-equivalent: 1,000 thermal neutrons (0.025 eV)
   on a water slab, recording mean elastic cross-section.
3. Repeats at 0.1 eV and 1 eV.
4. Asserts that patched results match vanilla within 0.1%.

If `G4NEUTRONHPDATA` is unavailable locally, write a unit test that exercises
`GetXsec()` and `Sample()` directly with a synthetic 1000-point linear grid
and verifies:
- `GetXsec(mid_energy)` returns the correct interpolated value (cross-check
  against a hand-computed result).
- `Sample()` mean and variance match expected values from 10,000 samples within
  3 sigma.

### Step 6: Write the optimization report

Write `docs/reports/opt_hp_neutron_lookup_20260513.md` in the simulation repo:

```markdown
# Optimization report: HP neutron lookup

Date: 2026-05-13
Branch: opt/hp-neutron-lookup
Geant4 base: v11.2.2 (accel/master)
BD entries implemented: BD-geant4-071, BD-geant4-072, BD-geant4-074

## Files changed

- `source/processes/hadronic/models/neutron_hp/src/G4NeutronHPVector.cc`
- `source/processes/hadronic/models/neutron_hp/include/G4NeutronHPVector.hh`
- `source/processes/hadronic/models/neutron_hp/src/G4NeutronHPElasticData.cc`
- `source/processes/hadronic/models/neutron_hp/include/G4NeutronHPElasticData.hh`

## Diff summary

[paste `git diff --stat` output]

## Expected speedup

2–4× for cross-section lookup in HP mode; ~10–20% total speedup on
neutron-heavy workloads.

## Validation result

[paste test output]

## Paper note

CPC/JINST vanilla Geant4 CPU paper.
```

### Step 7: Commit and push

```bash
cd /Volumes/MyDrive/nnbar/geant4-fork
git add source/processes/hadronic/models/neutron_hp/ tests/
git commit -m "opt: replace linear scan + rejection loop in G4NeutronHPVector

- GetXsec: O(N) scan -> std::lower_bound O(log N)
- Sample: rejection loop -> precomputed CDF inverse-CDF sampling
- G4NeutronHPElasticData: add LRU(256) Doppler-broadening cache

Implements BD-geant4-071, BD-geant4-072, BD-geant4-074.
CPC/JINST paper target."
git push -u origin opt/hp-neutron-lookup
```

## Verification checklist

Before marking DONE, confirm:

- [ ] `grep -r "NNBAR_Detector\|nnbar_reconstruction" source/` returns nothing
      in modified files.
- [ ] `cmake --build .` succeeds with no new warnings on patched files.
- [ ] Diff touches only `G4NeutronHPVector.*` and `G4NeutronHPElasticData.*`.
- [ ] Fixed-seed neutron test: mean elastic cross-section at 0.025, 0.1, 1 eV
      matches vanilla within 0.1%.
- [ ] Report written to `docs/reports/opt_hp_neutron_lookup_20260513.md`.
- [ ] Branch pushed to `SzeChunYiu/geant4-accel`.

## Isolation rules

- Never modify `NNBAR_Detector/`, `nnbar_reconstruction/`, `slurm/`, macros,
  or production data.
- Do not include any NNBAR simulation header.
- Do not submit SLURM jobs; all testing is local.

## Paper context

This patch targets the **CPC/JINST paper on vanilla Geant4 CPU speedup**.

Key references:
- Knuth 1998 *TAOCP* Vol. 2 (binary search, alias method)
- Walker 1977 alias method for tabulated sampling
- Vose 1991 efficient alias table construction
- Drepper 2007 *What Every Programmer Should Know About Memory*

Cite the binary-search and alias-method literature; do not claim speedup
numbers until benchmarked on LUNARC with the same workload as existing shards.

## Stop condition

Stop after patched files compile, the fixed-seed test passes, the report is
written, and the branch is pushed. Do not implement other BD entries.
