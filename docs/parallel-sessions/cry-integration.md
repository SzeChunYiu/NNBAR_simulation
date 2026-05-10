# Lane: cry-integration

## Goal

Integrate the CRY (Cosmic-Ray Shower Library) v1.7 into the NNBAR detector simulation.
This adds a new primary generator mode that produces cosmic particles on a 24m×24m plane,
with correct position/direction from CRY and energy sampled uniformly per bin.
The event weight (from thesis Eq. 6.1) is stored in the Parquet output.

## Repo

Work in: `/Volumes/MyDrive/nnbar/nnbar/simulation/NNBAR_Detector/`
Branch: `lane/cry-integration`

After completing local C++ work, the NNBAR_Detector directory must be rsynced to LUNARC
and the binary rebuilt. The rsync and rebuild commands are listed below — run them via SSH.

## Read first

- `docs/parallel-sessions/MASTER_PLAN.md` — project status
- `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/6_Signal_Bkg_simulation.tex` — the CRY setup (Section 6.2)
- `src/core/PrimaryGeneratorAction.cc` — existing generator to extend
- `include/core/PrimaryGeneratorAction.hh` — add CRY mode here
- `CMakeLists.txt` — add WITH_CRY option

## Physics spec (from thesis)

- CRY plane: 24m × 24m at +500 cm height (5m above detector top)
- Location: Lund, latitude 55.71°, longitude 13.19°, altitude=sea level
- Date: 1-1-2024
- 6 particle types: mu-, mu+, gamma, e-, neutron, proton (thesis uses these 6)
- 6 energy bins (GeV): [0, 0.5], [0.5, 1], [1, 5], [5, 10], [10, 50], [>50]
- Energy sampling: UNIFORM within the bin (NOT CRY natural spectrum)
  CRY provides position + direction; energy is overridden with uniform sample
- Weight formula (thesis Eq. 6.1):
  w_{i,j} = (N_{i,j} / S_{i,j}) × (N_{i,j} / sum_i(N_{i,j}))
  where N_{i,j} = expected events from Table 6.1, S_{i,j} = 1,000,000

## Expected N_{i,j} values from Table 6.1 (3-year totals reaching passive shielding)

```
# [energy_bin_index][particle]: expected events N_{i,j}
# particle order: mu, gamma, e-, neutron, proton
N = {
  0: [1.69e11, 2.30e12, 4.02e11, 4.33e11, 2.04e10],  # 0-0.5 GeV
  1: [1.90e11, 1.09e10, 1.05e10, 1.23e10, 4.34e9],   # 0.5-1 GeV
  2: [7.69e11, 6.21e9,  5.63e9,  6.03e9,  3.24e9],   # 1-5 GeV
  3: [2.68e11, 7.23e8,  2.24e8,  1.28e8,  1.44e8],   # 5-10 GeV
  4: [2.18e11, 2.30e7,  0,       5.92e7,  8.37e7],   # 10-50 GeV
  5: [2.00e11, 0,       0,       6.25e6,  5.00e6],   # >50 GeV
}
S = 1_000_000  # events simulated per bin
```

## Files to produce / modify

### 1. CMakeLists.txt — add WITH_CRY option

```cmake
option(WITH_CRY "Enable CRY cosmic ray generator" OFF)
if(WITH_CRY)
    find_path(CRY_INCLUDE_DIR CRYSetup.h HINTS $ENV{CRY_DIR}/src REQUIRED)
    find_library(CRY_LIBRARY NAMES CRY HINTS $ENV{CRY_DIR}/lib REQUIRED)
    add_compile_definitions(WITH_CRY=1)
    include_directories(${CRY_INCLUDE_DIR})
    target_link_libraries(nnbar-detector-simulation PRIVATE ${CRY_LIBRARY})
endif()
```

### 2. include/core/CRYPrimaryGenerator.hh (NEW FILE, <200 lines)

```cpp
#pragma once
#ifdef WITH_CRY
#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4ThreeVector.hh"
#include <string>
#include <vector>
class CRYSetup;
class CRYGenerator;
class CRYParticle;
class G4ParticleGun;

class CRYPrimaryGenerator {
public:
    CRYPrimaryGenerator();
    ~CRYPrimaryGenerator();

    // Call from PrimaryGeneratorAction::GeneratePrimaries when in CRY mode
    void GenerateCRYPrimaries(G4Event* anEvent);

    // Macro interface
    void SetParticleType(const G4String& name);  // "mu-","mu+","gamma","e-","neutron","proton"
    void SetEnergyMin(double emin_GeV);
    void SetEnergyMax(double emax_GeV);
    void SetEnergyBinIndex(int i);   // 0-5, sets N_{i,j} for weight
    void SetParticleIndex(int j);    // 0-4, sets N_{i,j} for weight
    void SetCRYDataPath(const G4String& path);

private:
    CRYSetup*     fSetup = nullptr;
    CRYGenerator* fGenerator = nullptr;
    G4ParticleGun* fGun = nullptr;
    G4String      fParticleType = "mu-";
    double        fEmin = 0.0;       // GeV
    double        fEmax = 0.5;       // GeV
    int           fEnergyBinIdx = 0;
    int           fParticleIdx = 0;
    double        fWeight = 1.0;
    G4String      fDataPath;

    void UpdateCRYSetup();
    double ComputeWeight(int iBin, int jParticle) const;
    static const double N_ij[6][5];  // expected counts from thesis Table 6.1
    static constexpr double S = 1e6;  // simulated events per bin
};
#endif  // WITH_CRY
```

### 3. src/core/CRYPrimaryGenerator.cc (NEW FILE, <400 lines)

Full implementation:
- `UpdateCRYSetup()`: constructs CRYSetup with input string:
  ```
  "date 1-1-2024 latitude 55.71 altitude 0 subboxLength 2400"
  ```
  ("subboxLength" is CRY's parameter for half-plane size in cm — 2400 cm = 24m)
- `GenerateCRYPrimaries()`:
  1. Call `fGenerator->gen()` to get a list of CRYParticles
  2. Find the one particle matching `fParticleType`
  3. Override its kinetic energy: `KE = fEmin + G4UniformRand()*(fEmax-fEmin)` [GeV → MeV]
  4. Position: take CRY's (x,y) on the plane, z = +500 cm (plane height)
  5. Set particle gun, fire
  6. Write ParticleRecord with `weight = fWeight` to ParquetOutputManager

- `ComputeWeight()`: implements thesis Eq. 6.1:
  ```cpp
  double N_ij_val = N_ij[iBin][jParticle];
  double sum_i = 0;
  for (int i=0; i<6; i++) sum_i += N_ij[i][jParticle];
  return (N_ij_val / S) * (N_ij_val / sum_i);
  ```

### 4. src/core/PrimaryGeneratorAction.cc — add CRY mode

Add to `GeneratePrimaries()`:
```cpp
#ifdef WITH_CRY
    if (sCRYMode && fCRYGenerator) {
        fCRYGenerator->GenerateCRYPrimaries(anEvent);
        return;
    }
#endif
```

Add static `G4bool sCRYMode = false` and CRY macro commands via `G4GenericMessenger`:
- `/cosmic/mode true` — enable CRY generator
- `/cosmic/particle mu-` — particle type
- `/cosmic/energyMin 0 GeV`
- `/cosmic/energyMax 0.5 GeV`
- `/cosmic/energyBin 0` — 0-5, for weight lookup
- `/cosmic/particleIdx 0` — 0-4, for weight lookup
- `/cosmic/dataPath /path/to/cry/data`

### 5. Write run_cosmic.slurm on LUNARC

After the binary is rebuilt with `-DWITH_CRY=ON`, create a SLURM array script:
- Array: 30 jobs (5 particles × 6 energy bins, skip zero N_{i,j} combinations)
- Each job: 1,000,000 events
- Output: `output/cosmic_{particle}_{ebin}/`
- Use 4 threads (`-t 4`), 16G RAM, 8h time limit, partition=lu48

Use this mapping:
```bash
PARTICLES=(mu- gamma e- neutron proton)
EBINS=(0 1 2 3 4 5)
EMIN=(0 0.5 1 5 10 50)
EMAX=(0.5 1 5 10 50 200)
```
Skip (gamma, bin 4), (gamma, bin 5), (e-, bin 4), (e-, bin 5) — N_{i,j}=0.

## CRY library setup on LUNARC

Run these SSH commands to download and build CRY (do this before the cmake build):

```bash
ssh lunarc "
cd /projects/hep/fs10/shared/nnbar/billy/packages
curl -L https://nuclear.llnl.gov/simulation/cry_v1.7.tar.gz -o cry_v1.7.tar.gz
tar xzf cry_v1.7.tar.gz
cd cry_v1.7
make
ls lib/libCRY.a src/CRYSetup.h
"
```

After CRY is built, set:
```bash
export CRY_DIR=/projects/hep/fs10/shared/nnbar/billy/packages/cry_v1.7
```
Pass this to cmake: `-DCRY_DIR=$CRY_DIR`

## Rsync and rebuild commands

```bash
# Sync local source to LUNARC
rsync -av --exclude build/ --exclude build-codex/ --exclude external/ \
  /Volumes/MyDrive/nnbar/nnbar/simulation/NNBAR_Detector/ \
  lunarc:/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/

# Submit rebuild SLURM job with WITH_CRY=ON
ssh lunarc "
  sed -i 's/-DMCPL_BUILD=ON/-DMCPL_BUILD=ON -DWITH_CRY=ON -DCRY_DIR=\/projects\/hep\/fs10\/shared\/nnbar\/billy\/packages\/cry_v1.7/' \
    /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/build_nnbar.slurm
  sbatch /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/build_nnbar.slurm
"
```

## Iteration cycle

1. Read the spec files listed above
2. Write/modify the C++ files listed above (local repo)
3. Verify syntax: check headers compile with `clang++ -std=c++17 -fsyntax-only` on any available .hh
4. Commit on `lane/cry-integration`
5. Run the rsync + rebuild SSH commands
6. Monitor build job: `ssh lunarc "tail -f .../slurm/build-\$(ssh lunarc squeue -u scyiu -h -o %i | tail -1).out"`
7. Once built, submit one test cosmic muon job (bin 0): 10,000 events, verify output/cosmic_mu-_0/ has Parquet files
8. Merge to main

## Stop condition

Stop when:
- CRY C++ files committed and merged
- Binary rebuilt on LUNARC with `-DWITH_CRY=ON`
- Test cosmic run (10k events) produces Parquet output with `weight` column

Write "DONE: CRY integrated, binary rebuilt, test run submitted" to stdout.

## Self-check

After completing, re-read MASTER_PLAN.md and check: does this completion unlock any BLOCKED task?
(Answer: yes — CRY SLURM array becomes NEXT. Write a one-line note about that.)
