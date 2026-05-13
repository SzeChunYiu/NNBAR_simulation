# Lane: cry-settings-audit

## Goal
Audit the CRY (Cosmic-Ray Shower Library) configuration used in the NNBAR
simulation. Extract all CRY parameters, estimate background event rate,
and document in a standalone report.

## Steps

### Step 1: Find CRY configuration files
Search for:
- CRY macro files: `find macro/ -name '*.mac' | xargs grep -l 'CRY\|cosmic' 2>/dev/null`
- CRY initialization in source: `grep -r 'CRYSetup\|CRYGenerator\|CRY' NNBAR_Detector/src/ --include='*.cc' -l`
- SLURM scripts: `cat NNBAR_Detector/slurm/run_cosmic_array.slurm` (or similar)

### Step 2: Extract CRY parameters
Look for in source code and macro files:
- subBox size (defines generator area, m)
- altitude (m above sea level)
- date (YYYYMMDD, affects solar activity)
- latitude (degrees)
- particle types enabled (muon, proton, neutron, gamma, electron, pion)
- energy cutoffs
- returnNeutrons, returnProtons, returnGammas, returnElectrons, returnMuons, returnPions

### Step 3: Estimate event rate
CRY produces primary cosmic ray interactions. Document:
- Area of subBox (m²)
- Expected muon flux at surface: ~1 muon/cm²/min = 1.67e-4/cm²/s
- Expected proton flux (primary CR): ~1.8e-4/cm²/s/sr (integrated)
- Number of simulated events per SLURM job
- Livetime equivalent: N_simulated / (flux × area)

### Step 4: Cross-check with published values
- muon flux at sea level: 10^4/m²/min (Particle Data Group)
- primary proton spectrum: dN/dE ~ E^{-2.7} for E > 1 GeV

### Output
Write `docs/reports/cry_cosmic_settings_audit.md`:
- Table: parameter | value | notes
- Estimated effective livetime (seconds)
- Dominant particle types by fraction
- Any non-default settings that affect background rate estimate

## Constraints
- grep/find/read only, no SLURM, no code changes
- Search from local simulation repo root: /Volumes/MyDrive/nnbar/nnbar/simulation/
- If CRY config is only on LUNARC, note this and stop (don't attempt remote access)
