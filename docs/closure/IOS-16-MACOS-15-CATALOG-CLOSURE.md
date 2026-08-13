# iOS 16 and macOS 15 catalog closure

Recorded: 2026-08-13

## Claim and scope

Question: can the four already-merged iOS 16 and macOS 15 archive payloads be
recorded in the catalog with exact source and destination provenance?

- First lifecycle stage: select the four reviewed migration specifications for
  the two iOS 16 and two ordinary macOS 15 payloads.
- Last lifecycle stage: generated entries and release metadata pass the full
  source-to-merged-destination audit.
- Supported claim after closure: the four named payload trees are faithfully
  represented by immutable catalog entries.
- Excluded: the cross-device iOS 18 row, all 15 blocked census rows, generating
  missing release history, and repairing incomplete legacy payloads.

## Authority map

| Property | Authority |
| --- | --- |
| Source payload identity | Legacy commit `d881e84676308404c6947d0218c11f347a6f3a89` |
| iOS 16 destination identity | Shard commit `3ee5b908fd4e21f8379aa62fc335d4ab2a8f44e7` |
| macOS 15 destination identity | Shard commit `ba046ef569c7720f90236324bec58cd908346237` |
| Versions, builds, devices, and inputs | Strictly parsed source README and reviewed specs |
| Files, bytes, and tree identity | Independent source-to-destination Git inventory |
| Display labels and release dates | AppleDB commit `3051f8643eaf5d6d7196fb3c01a0f9ade46f1dc7` |

## Closure matrix

| Stage | Evidence | Review status |
| --- | --- | --- |
| Selection and trigger | Exactly four explicitly named specs | Closed |
| Inputs and resources | Every spec contains two same-device IPSW inputs | Closed |
| Transformation | `record` independently verifies every source and destination tree | Closed |
| Advertisement and options | Generated catalog has 156 entries and release registry has 175 endpoints | Closed |
| Dispatch and transport | One unsigned catalog commit and pull request | Unresolved |
| State transition | Catalog merge follows both shard merges | Unresolved |
| Outcome oracle | Full local audit and hosted CI pass | Unresolved |

## Expected and observed inventory

| Catalog ID | Destination commit | Files | Logical bytes | Git tree |
| --- | --- | ---: | ---: | --- |
| `ios-16.7.14-20H365-20H370` | `3ee5b908fd4e21f8379aa62fc335d4ab2a8f44e7` | 1 | 557 | `2442f3cdd9416a5e89b3cfd4d46cd88030b22db6` |
| `ios-16.7.15-20H370-20H380` | `3ee5b908fd4e21f8379aa62fc335d4ab2a8f44e7` | 1 | 10,678 | `52ef7212cfd8353d38f0f74f3da1cc48911c341f` |
| `macos-15.4-24D81-24E248` | `ba046ef569c7720f90236324bec58cd908346237` | 7,660 | 218,638,978 | `7ff83e3092b48840eafda969a8c0464e8d23c6ba` |
| `macos-15.5-24E248-24F5042g` | `ba046ef569c7720f90236324bec58cd908346237` | 1,350 | 19,499,337 | `75de4ad3a1104de53862220b80a7acf6d14fb88d` |

The six unique release endpoints add five final releases and one beta label.
The proposed registry contains 175 endpoints: 81 beta, 17 RC, and 77 final
release records.

## Frozen-census reconciliation

The frozen census has 141 ordinary two-IPSW rows. With these four entries, 140
are represented by immutable catalog specifications from the census source
commit. The sole ordinary difference is
`18_1_22B5045g__vs_18_1_22B5045h`, which remains explicitly excluded because
its inputs identify different devices (`iPhone16,2` and `iPhone17,1`). The 15
blocked census rows remain visible and unresolved rather than being counted as
migrated.

## Negative-evidence audit and stop conditions

A same-device success set does not prove the cross-device comparison is valid
or invalid; it proves only that it is outside the current migration contract.
Missing READMEs, an unsupported title, a redirect, and a non-IPSW input are not
treated as evidence of inapplicability. Stop if any selected source tree,
merged destination tree, manifest, release record, census cardinality,
deterministic render, full audit, PR head, or default-branch merge commit
differs.

## Review-time bounded conclusion

Selection, immutable input verification, entry recording, release metadata,
census reconciliation, and deterministic rendering are closed for these four
rows. Publication, hosted verification, and the final catalog default-branch
state remain unresolved until the pull request lifecycle completes.
