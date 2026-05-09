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

```
backgrounds:
  cosmic:
    - sub_channel: cosmic_muon
      sample_id: cosmic_cry_essLund_overburdenA_v1
      expected_rate_per_pulse: <number>
      events_generated: 244000
      survivors: <observed>
      rate_or_upper_limit: <FC if zero-survivor>
    - sub_channel: cosmic_electron
      ...
    - sub_channel: cosmic_gamma
      ...
    - sub_channel: cosmic_neutron
      ...
    - sub_channel: cosmic_proton
      ...
  beam_neutron:
    - sub_channel: direct_beam_neutron
      sample_id: beam_neutron_hibeam_direct_v1
      ...
    - sub_channel: scattered_neutron
      ...
    - sub_channel: capture_gamma
      ...
    - sub_channel: secondary_hadronic
      ...
  unmodelled:
    - environmental_gamma
    - detector_internal
    - beampipe_activation
```

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

## 2. Zero-survivor handling

Per plan 04 §5: never quote `0 / N = 0`. Every zero-survivor channel
reports a Feldman-Cousins 90% C.L. upper limit on the survival rate.

## 3. Unmodelled sources

§1 `unmodelled` block enumerates background sources not in the
simulation. These are limitations from plan 01 §6 and accompany every
quoted total background as caveats in plan 50 (defence package).

## 4. Acceptance criteria

- §1 tree complete.
- §2 zero-survivor handling correct.
- §3 unmodelled list audited against plan 01 §6.

## 5. Dependencies

- **04, 14, 21, 22** — inputs.
- *Consumed by:* plan 45 (systematics), plan 46 (significance), plan
  47, plan 50.
