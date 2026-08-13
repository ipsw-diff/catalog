# Legacy TOC payload publication closure

Recorded: 2026-08-13

## Claim and scope

Question: can the 12 previously reviewed legacy payloads whose complete report
lives at root `TOC.md` be recorded after their exact trees merge into the
macOS 15, iOS 17, and iOS 18 shards?

- First lifecycle stage: select the 12 canonical specifications produced from
  frozen legacy commit `d881e84676308404c6947d0218c11f347a6f3a89`.
- Last lifecycle stage in this change: every catalog entry independently
  verifies its source tree against an immutable merged shard commit, and the
  complete catalog audit and deterministic render pass locally.
- Supported claim after the catalog pull request merges unchanged: these 12
  named payload trees are faithfully migrated and cataloged.
- Excluded: deleting the legacy corpus, generating missing firmware diffs,
  resolving OTA, AEA, redirect, or cross-device rows, and any claim that every
  historical iOS or macOS comparison exists.

## Authority map

| Property | Authority |
| --- | --- |
| Exact selected membership and report entrypoint | Reviewed migration specs below `migration/specs-{15,17,18}` |
| Source payload identity and report facts | Legacy commit `d881e84676308404c6947d0218c11f347a6f3a89` |
| Destination payload and manifest identity | Merged shard default-branch commits |
| Trees, paths, modes, counts, and bytes | Independent Git-object inventory performed by `record` and `audit` |
| Human release labels | AppleDB commit `3051f8643eaf5d6d7196fb3c01a0f9ade46f1dc7` |
| Publication | Generated catalog entries, release registry, and deterministic indexes |

## Closure matrix

| Stage | Required evidence | Review status |
| --- | --- | --- |
| Selection and trigger | Exactly 1 macOS 15, 4 iOS 17, and 7 iOS 18 TOC specs | Closed |
| Inputs and resources | All 12 source TOCs parse as exactly two same-device IPSW inputs | Closed |
| Transformation | `record` reproduces every source tree, destination tree, manifest, and entrypoint | Closed |
| Advertisement and options | Generated catalog and README include all 12 immutable links | Closed |
| Dispatch and transport | One unsigned catalog commit and pull request | Unresolved |
| State transition | All three shard pull requests merged before catalog recording | Closed |
| Outcome oracle | Complete local catalog audit passes; hosted pull-request and default-branch checks | Unresolved |

## Expected and observed inventory

| Destination | Rows | Payload files | Logical bytes | Merged commit |
| --- | ---: | ---: | ---: | --- |
| `ipsw-diff/macos-15` | 1 | 2,308 | 41,697,639 | `34ab75014b9350d2496064da4e8193a491568289` |
| `ipsw-diff/ios-17` | 4 | 993 | 190,309,794 | `8516ecf7d7bf141fdba73a2f10fa8bed9341978d` |
| `ipsw-diff/ios-18` | 7 | 17,385 | 1,020,977,539 | `844e6afc8d6113780fb89f48b355b614a222e385` |
| **Total** | **12** | **20,686** | **1,252,984,972** | — |

Each merge commit has the same root tree as its reviewed one-commit shard
branch. Every destination manifest retains `TOC.md` as the payload entrypoint;
no synthetic payload README was introduced.

## Negative-evidence audit

Twelve verified TOC payloads do not make every historical source candidate
migratable. The OTA-input row, AEA-input row, redirect row, and cross-device
iOS 18 row remain outside this publication. Their absence from the catalog is
not evidence that they are irrelevant or safely representable by the current
schema. The legacy corpus remains authoritative for every unverified row.

## Stop conditions

Do not publish if selected cardinality, source or destination tree, merged
default-branch commit, manifest, TOC entrypoint, release record, rendered
count, or complete audit differs. Do not substitute mutable branch names for
the full merged commit identities above.

## Review-time bounded conclusion

Selection through merged shard state and local catalog verification is closed
for the 12 named TOC payloads. Catalog pull-request review, hosted checks,
unchanged merge, and final default-branch audit remain open lifecycle stages.
