# iOS 12 and iOS 15 catalog closure

Recorded: 2026-08-13

## Claim and scope

Question: can the two already-merged iOS 12 and iOS 15 archive payloads be
recorded in the catalog with exact source and destination provenance?

- First lifecycle stage: select the two reviewed migration specifications for
  `12_5_7_16H81__vs_12_5_8_16H88` and
  `15_8_6_19H402__vs_15_8_7_19H411`.
- Last lifecycle stage: the generated catalog entries and release registry pass
  the complete source-to-merged-destination audit.
- Supported claim after closure: these two named payload trees are faithfully
  represented by immutable catalog entries.
- Excluded: claiming a complete Apple release history, generating missing
  historical diffs, migrating iOS 16 or macOS 15, and resolving the census's
  exceptional rows.

## Authority map

| Property | Authority |
| --- | --- |
| Source payload identity | Legacy commit `d881e84676308404c6947d0218c11f347a6f3a89` |
| Destination payload identity | Merged shard default-branch commits |
| Versions, builds, devices, and inputs | Strictly parsed source README and reviewed specs |
| Files, bytes, and tree identity | Independent source-to-destination Git inventory |
| Display labels and release dates | AppleDB commit `3051f8643eaf5d6d7196fb3c01a0f9ade46f1dc7` |
| Catalog presentation | Deterministic catalog and README renderers |

## Closure matrix

| Stage | Evidence | Review status |
| --- | --- | --- |
| Selection and trigger | Exactly two explicitly named specs | Closed |
| Inputs and resources | Both specs parse two same-device IPSW inputs | Closed |
| Transformation | `record` independently verifies both source and destination trees | Closed |
| Advertisement and options | Generated catalog contains 152 entries and release registry contains 169 endpoints | Closed |
| Dispatch and transport | One unsigned catalog commit and pull request | Unresolved |
| State transition | Catalog merge follows both shard merges | Unresolved |
| Outcome oracle | Full catalog audit and hosted CI pass | Unresolved |

## Expected and observed inventory

| Catalog ID | Destination commit | Files | Logical bytes | Git tree |
| --- | --- | ---: | ---: | --- |
| `ios-12.5.8-16H81-16H88` | `7a2d48af608bbe9fdd0325b192518d79bdc62bca` | 1 | 43,191 | `75d983d5b0fc124644e3a543a76abc7d1cadbba4` |
| `ios-15.8.7-19H402-19H411` | `57d0ea0143913199c0585265319d6800d858fc39` | 1 | 10,605 | `721ca55fb96c8b41ba4de83693c2ab40ff229056` |

The generated release records identify all four endpoints as final releases.
Their display versions are 12.5.7, 12.5.8, 15.8.6, and 15.8.7; no beta or RC
ordinal is inferred from build numbers.

## Negative-evidence audit

Two catalog entries do not establish a complete iOS 12 or iOS 15 release
history. They establish only faithful migration of the two named legacy trees.
The absence of earlier diffs from the legacy tree is not evidence that those
Apple releases or possible comparisons did not exist. This change also does
not silently treat the remaining ordinary or blocked census rows as migrated.

## Stop conditions

Stop if either source tree, merged destination tree, manifest, catalog entry,
release record, deterministic render, full audit, PR head, or default-branch
merge commit differs from the recorded evidence.

## Review-time bounded conclusion

Selection, immutable input verification, entry recording, release metadata,
and deterministic rendering are closed for these two rows. Publication,
hosted verification, and the final catalog default-branch state remain
unresolved until the pull request lifecycle completes.
