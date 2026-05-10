---
id: 44_background_taxonomy
title: Background taxonomy — full channel tree per source
version: 0.1
status: draft
owner: Analysis WG
depends_on: [00_README, 04_statistical_uncertainty, 14_background_models, 21_sample_cosmic_CRY, 22_sample_neutron_beam]
outputs:
  - {path: docs/rebuild_plans/44_background_taxonomy.md, schema: this file}
  - {path: data/background_taxonomy/tree.yml, schema: machine-readable tree}
acceptance:
  - {test: every background channel has node = (source, sub-channel, sample, expected rate, survivor count), method: tree review, pass_when: complete tree}
  - {test: zero-survivor channels report Feldman-Cousins upper limits per plan 04 §5, method: review of upper-limit rows, pass_when: zero "0 / N = 0" entries}
risks:
  - {risk: an unmodelled background source slips through, mitigation: §3 explicit registry of unmodelled sources from plan 01 §6 limitations}
estimated_effort: M
last_updated: 2026-05-09
---

# Background taxonomy

*Charter.* The full enumeration of backgrounds the analysis claims
to control. Every claim of "no surviving background" or "1 in 10⁶
survival" is a specific rate on a specific node in this tree.

## 1. Tree structure

Each background node is a row in the canonical tree. `survivors` is
filled by the reconstruction output; if it is zero, §2 supplies the
reported upper limit rather than a literal zero rate.

| Source | Sub-channel | Source citation | Sample id / label | Expected-rate convention | Observable signature | Related plan-24 leaf |
|---|---|---|---|---|---|---|
| cosmic | `cosmic_muon` | CRY mixture and per-species split: plan 14 §§1.1–1.3; sample sizing: plan 21 §4 | `cosmic_cry_essLund_overburdenA_v1` primary species label `mu±`; `overburdenB_v1` systematic cross-check | CRY normalisation at ESS Lund; target survival upper limit `ε90 ≤ 1e-5` for 244k events if zero survivors | through-going charged track, high scintillator energy, timing outlier, hemisphere imbalance | C.1, C.4, E.8, E.9, S.1, S.5 |
| cosmic | `cosmic_electron` | CRY particle set includes e±: plan 14 §1.1; legacy per-species macros retained: plan 14 §1.3 | same CRY sample with primary species label `e±`; per-species macro row in plan 47 | CRY e± flux component times measured survival; zero survivors reported with F-C `ε90` | EM shower with charged track, possible photon-like cluster contamination | P.1, P.2, P.3, P.4, E.5, S.4 |
| cosmic | `cosmic_gamma` | CRY particle set includes γ: plan 14 §1.1 | same CRY sample with primary species label `γ`; per-species macro row in plan 47 | CRY γ flux component times measured survival; zero survivors reported with F-C `ε90` | isolated EM clusters, π⁰-like photon pairs, little TPC activity | P.1, P.2, P.5, P.6, E.7, S.3 |
| cosmic | `cosmic_neutron` | Cosmic hadron sub-channel: plan 14 §1.2; `_HP` dependency: plan 21 §9 | same CRY sample with primary species label `n` | CRY neutron component times measured survival; zero survivors reported with F-C `ε90` | delayed hadronic activity, capture γ, secondary charged tracks | C.1, P.1, E.8, S.1, S.6 |
| cosmic | `cosmic_proton` | Cosmic hadron sub-channel: plan 14 §1.2 | same CRY sample with primary species label `p` | CRY proton component times measured survival; zero survivors reported with F-C `ε90` | stopping charged track, high dE/dx, scintillator asymmetry | C.2, C.3, C.5, E.9, S.5 |
| beam_neutron | `direct_beam_neutron` | HIBEAM source choice: plan 22 §1; sub-channel table: plan 22 §3 | `beam_neutron_hibeam_direct_v1` | per-event survival folded with per-pulse yield; plan 22 target false-positive rate `≤1e-4` per pulse at 90% C.L. | neutron reaches detector volume; prompt hadronic secondaries near beam direction | C.1, E.8, E.9, S.6 |
| beam_neutron | `scattered_neutron` | sub-channel table: plan 22 §3; beam-line source: plan 14 §2.1 | `beam_neutron_hibeam_scattered_v1` | same per-pulse convention as direct beam neutrons, with beampipe/collimator interaction label | off-axis hadronic activity, displaced vertex/topology, timing compatible with beam | V.4, V.5, E.5, E.8, S.4 |
| beam_neutron | `capture_gamma` | capture-γ source details: plan 14 §3; sample id: plan 22 §3 | `beam_neutron_hibeam_captgamma_v1` | neutron-transport capture rate folded with survival; zero survivors reported with F-C `ε90` | low-to-moderate energy γ cascade in lead glass/scintillator, can fake π⁰ photons in pile-up | P.1, P.2, P.5, P.6, E.1, E.8 |
| beam_neutron | `secondary_hadronic` | neutron inelastic sub-channel: plan 14 §2.2; sample id: plan 22 §3 | `beam_neutron_hibeam_secondaries_v1` | secondary-fragment rate folded with per-pulse neutron yield; F-C for zero survivors | charged hadrons with pion/proton PID-like signatures and calorimeter deposits | C.2, C.3, C.5, P.5, E.9, S.2 |

Unmodelled nodes are listed separately in §3 because they have no
registered simulated sample in the first rebuild cycle.

Decision-log stubs for freezing the rate conventions:

| DEC id | Convention to sign | Default in this plan |
|---|---|---|
| `DEC-44-COSMIC-RATE-SOURCE` | Cosmic total-rate source and overburden baseline | CRY ESS Lund `overburdenA_v1` is the conservative baseline; `overburdenB_v1` is the systematic cross-check. |
| `DEC-44-BEAM-RATE-SOURCE` | Beam-neutron source and per-pulse conversion | Prefer ESS HIBEAM MCPL; fallback is plan-22 parameterised spectrum; per-event survivors are folded with per-pulse yield. |
| `DEC-44-ZERO-SURVIVOR-REPORTING` | Zero-survivor reporting convention for all background nodes | Report Feldman-Cousins 90% C.L. upper limits per plan 04 §5; never quote `0 / N = 0`. |

Each node carries:

| Field | Source |
|---|---|
| sample_id | plan 03 |
| events_generated | plan 03 manifest |
| survivors | counted on the reconstruction output |
| rate | survivors / events_generated |
| upper_limit_FC | plan 04 §5 when survivors = 0 |
| systematic | plan 45 |
| limitation_flags | plan 01 §6 |

### 1.1 Rate and survivor accounting

For every §1 node, the machine-readable tree stores both the measured
survivor count and the convention used to convert it to an expected
background contribution:

| Source | Survivor field | Rate conversion | Required zero-survivor output |
|---|---|---|---|
| cosmic | `n_survivors_after_plan37` from the CRY sample, optionally split by primary species label | `survival_fraction * CRY_component_flux * exposure`, with overburden A as baseline and B as systematic | `epsilon90 = FC90(0, n_generated)`; for the 244k-event plan-21 sample this targets `≈ 1.0e-5` |
| beam_neutron | `n_survivors_after_plan37` from each plan-22 sub-channel sample | `survival_fraction * neutron_yield_per_pulse * pulse_count * subchannel_weight` | `epsilon90` plus false-positive-per-pulse upper limit; target `≤ 1e-4` per pulse |

Rows with nonzero survivors quote the measured fraction with the plan
04 interval. Rows with zero survivors quote the F-C upper limit from
§2; no report may collapse a zero-survivor node to exactly zero
expected background.

## 2. Zero-survivor handling

Per plan 04 §5: never quote `0 / N = 0`. Every zero-survivor channel
reports a Feldman-Cousins 90% C.L. upper limit on the survival rate.

## 3. Unmodelled sources

These nodes are not simulated in the first rebuild cycle. They must
appear as explicit caveats beside every total-background quote in plan
50; they do not get folded into `b` until a registered sample exists.

| Unmodelled source | Source citation | Missing sample id | Expected-rate status | Observable signature | Limitation flags |
|---|---|---|---|---|---|
| `environmental_gamma` | plan 14 §4; plan 01 §6 | none | unbounded by current rebuild | room γ activity in lead glass/scintillator, low-energy EM pile-up | L3, L5, L8, L11 |
| `detector_internal` | plan 14 §4; plan 01 §6 | none | unbounded by current rebuild | scintillator self-radioactivity, lead-glass dark/photoelectron activity, dead/hot channel fakes | L4, L5, L8, L12 |
| `beampipe_activation` | plan 14 §4; plan 01 §6 | none | unbounded by current rebuild | delayed activation γ/charged secondaries correlated with beam operation | L5, L6, L8, L11 |

DEC stub: `DEC-44-UNMODELLED-CAVEATS` — keep these rows out of the
numeric background sum until simulated samples are registered, but
require them as plan-50 caveats for every quoted total-background
result.

## 4. Acceptance criteria

- §1 tree complete.
- §2 zero-survivor handling correct.
- §3 unmodelled list audited against plan 01 §6.

## 5. Dependencies

- **04, 14, 21, 22** — inputs.
- *Consumed by:* plan 45 (systematics), plan 46 (significance), plan
  47, plan 50.
