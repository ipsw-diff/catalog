# Legacy TOC entrypoint closure

Recorded: 2026-08-13

## Claim and scope

Question: can the 12 legacy payloads whose complete report lives at root
`TOC.md` enter the ordinary migration pipeline without changing a payload byte,
inventing a README, or weakening the two-IPSW contract?

- First lifecycle stage: the frozen census selects one tracked root entrypoint
  from immutable legacy commit `d881e84676308404c6947d0218c11f347a6f3a89`.
- Last lifecycle stage in this change: reviewed major policies produce canonical
  migration specs that retain the exact `TOC.md` entrypoint.
- Excluded: copying or publishing the 12 payloads, cataloging them before shard
  merges, and modeling OTA, AEA, redirect, or cross-device comparisons.

## Authority and closure matrix

| Stage | Evidence | Status |
| --- | --- | --- |
| Selection and trigger | Root `README.md` is preferred; otherwise exact root `TOC.md`; arbitrary and nested paths are rejected | Closed |
| Inputs and resources | All 12 TOCs are tracked at the frozen commit and parse as two same-device IPSW inputs | Closed |
| Transformation | Planner carries the selected basename into source path, destination path, manifest, archive link, and catalog entry | Closed |
| Advertisement and options | Specs disclose non-default `TOC.md`; default README specs remain byte-for-byte unchanged | Closed |
| Dispatch and transport | Stage tests preserve the exact source tree and do not synthesize `README.md` | Closed |
| State transition | This tooling change writes only census, policies, and planned specs; no shard is changed | Closed |
| Outcome oracle | Census reconciles 156 payloads as 153 ordinary plus 3 blocked; generated plans contain 1 macOS 15, 4 iOS 17, and 7 iOS 18 TOC rows | Closed |

## Negative evidence and remaining gaps

The 12 payloads are eligible because their tracked TOCs carry the complete
title and two-IPSW report—not because their directory names resemble diffs.
The following remain outside this model:

- `23D8133__iPhone17,1__vs_23D771330a__iPhone17,1` uses OTA inputs.
- `26_5_23F5043k_vs_26_5_23F5054h` uses AEA inputs.
- `26_0_23A5326a__vs_26_0_23A340` redirects to a corrected report.
- `18_1_22B5045g__vs_18_1_22B5045h` changes device identity and remains an
  explicit major-18 exclusion.

These rows do not become migratable merely because the entrypoint model now
supports TOC files.

## Stop conditions

Stop if a non-root entrypoint is accepted, README precedence changes, a planned
TOC spec loses its explicit entrypoint, staging changes the source tree, any of
the three blocked rows is silently selected, or the major policies no longer
exactly reconcile their census scope.

## Bounded conclusion

The entrypoint and planning stages are closed for the 12 reviewed TOC payloads.
Publication remains unresolved until separate shard PRs merge and the catalog
re-verifies their immutable destination commits.
