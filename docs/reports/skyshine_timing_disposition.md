# Skyshine and ESS timing-cut disposition

Date: 2026-05-12. Lane: `skyshine-timing-disposition`.

This is an audit-only compact-safe iteration. It does **not** edit C++,
Python reconstruction code, SLURM, macros, or simulation data. Its purpose is
to decide whether the current cosmic plus beam-background evidence already
covers skyshine/groundshine through the Chapter 3 fast-neutron timing cut, or
whether the project must keep an explicit blocker.

## Scope

Inputs inspected:

- `docs/parallel-sessions/skyshine-timing-disposition.md`
- `docs/reports/beam_background_tpc_occupancy.md`
- `scripts/verify_beam_background_occupancy.py`
- `nnbar_reconstruction/reconstruction/timing_window.py`
- `nnbar_reconstruction/scripts/run_reconstruction.py`
- `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/3_HIBEAM_NNBAR_experiment.tex`

The lane spec also named `nnbar_reconstruction/analysis/timing_window_audit.py`.
That file is absent in this checkout, so there was no natural existing audit
module to extend. The disposition is therefore recorded here as structured
blockers instead of adding Python analysis code from the C++/LUNARC worker lane.

## Ch. 3 reference

The Chapter 3 source contains the required skyshine and fast-neutron timing-cut
statements:

| Source evidence | Context |
|---|---|
| `3_HIBEAM_NNBAR_experiment.tex:319-321` | Fast beam neutrons are time-correlated with the ESS pulse; a 5 ms cut from the proton bunch suppresses the highest-energy neutrons and costs about 7% of the pulse interval. |
| `3_HIBEAM_NNBAR_experiment.tex:364-366` | Skyshine/groundshine are significant detector-area phenomena; skyshine is partly mitigated by the same 5 ms fast-neutron timing cut, but is also treated as a cosmic-like residual. |
| `3_HIBEAM_NNBAR_experiment.tex:382` | Fast spallation and skyshine neutrons can be filtered by timing; slow neutrons need a dedicated study. |

This is a thesis-source disposition, not a reproduced local result.

## Evidence inventory

### Grep survey

Requested terms were searched across `nnbar_reconstruction/`, `docs/`, and the
Chapter 3 source:

```text
skyshine/groundshine: only the lane spec, MASTER_PLAN row, and Ch. 3 source
5 ms / fast-neutron timing: Ch. 3 source plus the lane spec and MASTER_PLAN row
timing_cut/apply_timing_cuts: reconstruction timing-window code only
```

No existing `nnbar_reconstruction/` or `docs/reports/` evidence row names a
skyshine source manifest, groundshine source manifest, 5 ms ESS-pulse veto
implementation, or skyshine-specific output artifact.

### Reconstruction timing windows

The existing reconstruction timing code is a nanosecond-scale detector-hit
time-of-flight filter, not the millisecond ESS-pulse cut:

| Verified surface | Meaning for this disposition |
|---|---|
| `nnbar_reconstruction/reconstruction/timing_window.py:59-98` | `scintillator_timing_window` calculates a pion flight-time acceptance window around the reconstructed event time. |
| `nnbar_reconstruction/reconstruction/timing_window.py:101-135` | `leadglass_timing_window` calculates a photon flight-time acceptance window around the reconstructed event time. |
| `nnbar_reconstruction/reconstruction/timing_window.py:138-188` | `apply_timing_cuts` applies those per-hit windows to detector hits. |
| `nnbar_reconstruction/scripts/run_reconstruction.py:74-225` | `reconstruct_event` calls `apply_timing_cuts` after vertex reconstruction. |

These windows can support object reconstruction and cosmic rejection, but they
do not encode "discard the first 5 ms after the ESS proton bunch" or a
skyshine arrival-time phase relative to the ESS pulse.

### Beam-background readiness

`docs/reports/beam_background_tpc_occupancy.md` already keeps Appendix A
beam-background reproduction fail-closed. A fresh run of
`scripts/verify_beam_background_occupancy.py --repo-root .` reported:

```text
[BLOCK] absorber_selector: B4C-only coating/beam-stop use remains hard-coded
[BLOCK] hp_physics_registration: HP header/reference exists, but registered constructor is non-HP
[BLOCK] beam_neutron_registry: missing beam_neutron_hibeam_*_v1 manifest under data/registry
```

Those blockers prevent treating the current beam-background pipeline as a
validated implementation point for the 5 ms fast-neutron cut.

## Disposition

| Source | Covered now? | Disposition |
|---|---:|---|
| Fast spallation neutrons | No | Chapter 3 defines the 5 ms cut, but the local beam-background gate still lacks a beam-neutron manifest, HP physics registration, and configurable absorber/source artifacts. |
| Skyshine fast neutrons | No | Chapter 3 says part of skyshine is mitigated by the same 5 ms cut, but no local source manifest or ESS-pulse timing implementation applies that cut to skyshine events. |
| Groundshine | No | It is named with skyshine in Chapter 3, but there is no separate local source model, rate row, or output artifact. |
| Cosmic-like residual skyshine | Partially conceptual only | The thesis says residual skyshine is cosmic-like, and CRY cosmic work exists, but there is no rate-normalised skyshine residual folded into the cosmic background sum. |

Therefore the project should keep this item **BLOCKED**, not DONE. The
correct next unit is a fail-closed skyshine/groundshine source-and-timing
manifest check or an explicit planner decision that skyshine residuals stay
model-limited until a source model is staged.

## Structured blockers

1. `OPEN: skyshine_source_manifest` — add a skyshine/groundshine source row
   with rate, energy spectrum, angular model, timing phase relative to the ESS
   pulse, provenance citation, and output artifact IDs. Target resolution:
   2026-06-30.
2. `OPEN: ess_5ms_timing_cut_gate` — implement or document the 5 ms fast-neutron
   cut as an ESS-pulse-phase selection separate from nanosecond detector
   time-of-flight windows. Target resolution: 2026-06-30.
3. `OPEN: beam_background_gate_dependency` — resolve the existing
   `absorber_selector`, `hp_physics_registration`, and
   `beam_neutron_registry` blockers before the beam-background pipeline can
   claim to cover the fast-neutron portion of skyshine. Target resolution:
   2026-06-30.
4. `OPEN: residual_cosmic_like_rate` — if residual skyshine is to be absorbed
   into the cosmic-background methodology, record the residual rate and
   uncertainty as a source row instead of relying on prose equivalence. Target
   resolution: 2026-07-05.

## Conclusion

Skyshine/groundshine is **not covered by current executable artifacts**. The
thesis rationale is clear, but the local repository currently has only the
detector hit timing-window code and a fail-closed beam-background audit. Neither
surface applies the Chapter 3 5 ms ESS-pulse cut to a skyshine source model.
The MASTER_PLAN row should be marked `BLOCKED` with the blockers above.
