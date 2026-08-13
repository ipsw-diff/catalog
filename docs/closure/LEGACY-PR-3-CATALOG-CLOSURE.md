# Legacy pull request 3 catalog publication closure

Recorded: 2026-08-12

## Claim and scope

Question: can the 16 iOS 17 comparison subtrees submitted in
`blacktop/ipsw-diffs#3` be cataloged from the contributor's immutable pull
request head after their exact Git trees have merged into the `ios-17` shard?

- First lifecycle stage: select the exact iOS 17 root set added between pull
  request base `80869317ef5f4fc9e9cce6836e7f49b454bd11ac` and head
  `707bb335823a7869c2ec6f41f0ef88e6dc701183`.
- Last lifecycle stage: every new catalog entry independently verifies its
  selected source subtree against merged shard commit
  `a234b0187dbcac26fa7c0c1ee8095c9a59140da2`, then resolves both release
  endpoints from the pinned AppleDB snapshot.
- Supported claim after closure: the 16 named Git subtrees were faithfully
  migrated and cataloged with immutable source, destination, and release-label
  provenance.
- Excluded: identifying the exact `ipsw` executable that produced the rerun,
  regenerating the diffs from IPSWs, validating the contributor's differ
  semantics, merging or closing the legacy pull request, and resolving the four
  missing-README candidates documented by the earlier frozen-census migration.

## Authority map

| Property | Authority |
| --- | --- |
| Pull request base and head | GitHub pull request 3 and immutable Git commits |
| Exact migration membership | Added iOS 17 top-level roots between the pinned base and head |
| Versions, builds, and input filenames | Strictly parsed README in each selected source subtree |
| Device identity | Matching device token parsed independently from both IPSW inputs |
| Source trees, counts, bytes, and modes | Git objects at contributor head `707bb335823a7869c2ec6f41f0ef88e6dc701183` |
| Destination trees and manifests | Merged `ipsw-diff/ios-17` default-branch commit `a234b0187dbcac26fa7c0c1ee8095c9a59140da2` |
| Release display labels | Exact records at AppleDB commit `3051f8643eaf5d6d7196fb3c01a0f9ade46f1dc7` |
| Publication | Catalog entries and deterministic rendered indexes |
| Diff-generator version | Unresolved; comments establish a rerun but no exact final version |

## Initial closure matrix

| Stage | Required evidence | Initial status |
| --- | --- | --- |
| Selection and trigger | Base-to-head root set equals the reviewed 16-path allowlist | Closed |
| Inputs and resources | Every root has one valid two-IPSW README and matching device identities | Closed |
| Transformation | Generated entries reproduce every source and merged destination tree | Closed |
| Advertisement and options | Rendered README and `catalog.json` contain all 150 reviewed entries | Closed |
| Dispatch and transport | One unsigned catalog commit contains only the bounded publication changes | Unresolved |
| State transition | Shard PR 2 merged before catalog records were generated | Closed |
| Outcome oracle | Full 150-entry source-to-destination audit and catalog PR default-branch CI pass | Unresolved |

## Expected inventory

The new source set contains 16 payloads, 42,315 tracked files, and 275,569,163
logical bytes. All source objects use mode `100644`. The merged archive now
contains 21 comparisons: the 16 new rows plus the 5 previously cataloged rows.

| Catalog state | Entries | Release endpoints | Beta | RC | Final |
| --- | ---: | ---: | ---: | ---: | ---: |
| Before this publication | 134 | 148 | 80 | 17 | 51 |
| Proposed | 150 | 165 | 80 | 17 | 68 |

The 16 comparisons use 18 unique endpoints. Build `21G80` was already required
by the earlier five-row iOS 17 migration, so this publication adds 17 release
records. AppleDB classifies all 17 added records as final releases at the pinned
commit.

## Mixed immutable source commits

The five earlier iOS 17 specs use frozen legacy commit
`d881e84676308404c6947d0218c11f347a6f3a89`; these 16 specs use the immutable
pull-request head. The archive renderer previously required one shared source
commit even though source commit is per-spec provenance and is not an
archive-wide property. That restriction is removed. The renderer continues to
require one source repository, platform, major version, and destination
repository, and continues to reject duplicate source or destination paths. A
regression test covers rendering one archive from multiple immutable commits.

## Review-time closure matrix

| Stage | Required evidence | Review status |
| --- | --- | --- |
| Selection and trigger | Base-to-head root set equals the reviewed 16-path allowlist | Closed |
| Inputs and resources | Every root has one valid two-IPSW README and matching device identities | Closed |
| Transformation | Generated entries reproduce every source and merged destination tree | Closed |
| Advertisement and options | Rendered README and `catalog.json` contain all 150 reviewed entries | Closed |
| Dispatch and transport | One unsigned catalog commit contains only the bounded publication changes | Unresolved |
| State transition | Shard PR 2 merged before catalog records were generated | Closed |
| Outcome oracle | Full 150-entry source-to-destination audit and catalog PR default-branch CI pass | Unresolved |

The local portion of the outcome oracle is closed: `ipsw-diff-catalog audit`
re-fetched and verified all 150 entries. Catalog PR merge and default-branch CI
remain unresolved external state.

## Verification and mutation evidence

- All 16 entries were generated with `record` against source head
  `707bb335823a7869c2ec6f41f0ef88e6dc701183` and merged destination commit
  `a234b0187dbcac26fa7c0c1ee8095c9a59140da2`.
- The full audit reconciles exactly 150 catalog entries.
- Deterministic rendering checks 150 entries in both `README.md` and
  `catalog.json`.
- Release metadata generation and `--check` both resolve exactly 165 endpoints:
  80 beta, 17 RC, and 68 final.
- The regression suite accepts multiple immutable source commits in one archive
  and retains rejection tests for mixed platform, source repository, major
  version, destination repository, and duplicate source or destination paths.
- Formatting, lint, type checking, 119 tests, and all three frozen migration
  plan checks pass.

## Negative-evidence audit

The contributor's rerun statement does not establish the exact final generator
version. Three payloads contain only a README:
`17_0_21A329__vs_17_0_1_21A340`,
`17_0_1_21A340__vs_17_0_2_21A351`, and
`17_4_1_21E236__vs_17_4_1_21E237`. Exact Git-tree verification makes them
faithful payload migrations, but neither their small size nor a passing catalog
audit proves that the original diff generation was semantically complete.
GitHub's current zero-file comparison for the stale legacy PR is not evidence
that its pinned base-to-head Git objects are empty.

## Stop conditions

Do not publish if the base, head, path set, inventory totals, parsed README
facts, source tree, merged destination tree, manifest facts, AppleDB source
record, rendered counts, or full audit differs. Do not substitute a mutable
fork branch for the pinned pull-request head or infer the unavailable generator
version.

## Review-time bounded conclusion

Selection through merged shard state and deterministic local catalog rendering
are closed for the 16 named rows, and the full 150-entry local audit passes. The
single unsigned publication commit, catalog PR merge, and default-branch CI
remain open. The four earlier missing-README candidates and the exact final
`ipsw` generator version remain explicitly unresolved outside this claim.
