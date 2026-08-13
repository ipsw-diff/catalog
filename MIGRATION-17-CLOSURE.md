# iOS 17 legacy migration closure

Recorded: 2026-08-12

## Claim and scope

Question: can the five eligible frozen legacy iOS 17 payloads be copied into a
reviewed `ios-17` archive shard, merged, then cataloged without guessing facts
absent from the source corpus?

- First lifecycle stage: classify the complete frozen-census destination-major-17
  set and reconcile it with the reviewed selected paths.
- Last lifecycle stage in this change: every catalog entry independently verifies
  its frozen source subtree against the immutable shard default-branch commit.
- Supported claim after the catalog PR merges unchanged: the named five rows are
  faithfully migrated and cataloged.
- Excluded: deletion of legacy data, repair of missing READMEs, new firmware
  generation, scheduled publication, external announcements, and any claim that
  the four blocked path candidates were migrated.

## Authority map

| Property | Authority |
| --- | --- |
| Frozen source universe and structural classification | Census at legacy commit `d881e84676308404c6947d0218c11f347a6f3a89` |
| Exact planned membership | `migration/major-17.json` |
| iOS routes and future shard | Exact iPad and iPhone input-prefix routes in `migration/major-17.json` |
| Device identity | Device token parsed independently from both census IPSW inputs |
| Versions, builds, paths, trees, counts, bytes, and modes | Frozen census and immutable legacy Git objects |
| Destination identity | Merged `ipsw-diff/ios-17` default-branch commit and independently measured subtrees |
| Release display labels | Exact records at pinned AppleDB commit `3051f8643eaf5d6d7196fb3c01a0f9ade46f1dc7` |
| Publication | Catalog entries and deterministic rendered indexes |

## Closure matrix

| Stage | Required evidence | Status |
| --- | --- | --- |
| Selection and trigger | All five ordinary destination-major-17 rows equal the five reviewed planned paths | Closed |
| Inputs and resources | Planned rows have matching input devices; four no-README rows remain visible | Closed for 5 planned rows; 4 rows unresolved |
| Transformation | Deterministic planning and atomic batch staging reproduce five source trees and manifests | Closed |
| Advertisement and options | The archive README lists exactly the five reviewed rows; no discovery workflow is enabled | Closed |
| Dispatch and transport | One unsigned shard commit contains exactly five payloads, five manifests, and the archive README | Closed |
| State transition | Shard PR 1 merged before catalog recording; all entries pin its immutable default-branch commit | Closed |
| Outcome oracle | Five source and destination trees pass local audit; catalog publication must still merge unchanged and pass default-branch CI | Unresolved |

## Expected inventory

| Classification | Rows | Payload files | Logical bytes |
| --- | ---: | ---: | ---: |
| Planned | 5 | 132 | 298,284 |
| Census-blocked path candidates: missing README | 4 | 993 | 190,309,794 |
| Total iOS 17 path candidates | 9 | 1,125 | 190,608,078 |

The planned rows contain five distinct source paths, five distinct spec IDs,
and five distinct source trees. Three rows use matching `iPhone16,2` inputs.
Two use matching `iPad_64bit_TouchID_ASTC` inputs, represented by the source
format's leading device token `iPad`; both raw IPSW names remain in each spec.

The merged shard commit is
`28fd3d571d396c6030354e4a5cab91ab75aba685`. Its root tree
`c66455f1450db13f61dcff06cc8e77eaa0a27c0e` exactly equals reviewed migration
commit `caecb657a790e592d475fc846d7a7eb3d45cc9d2`. The five destination subtrees
retain 132 files and 298,284 logical bytes in total.

`17_6_21G79__vs_17_6_1_21G93` is intentionally not renamed or rewritten. Its
validated README identifies the from IPSW build as `21G80`, so the generated
spec uses build `21G80` while preserving the immutable source path containing
`21G79`. A path label is not treated as build authority.

## Unresolved source rows

The following directory names look like comparisons ending in iOS 17, but they
lack tracked READMEs at the frozen source commit. Their destination version, two
IPSW inputs, and device identity therefore cannot be established without a new
reviewed authority:

- `17_6_21G5052e__vs_17_6_21G5061c`
- `17_6_21G5061c__vs_17_6_21G5066d`
- `17_6_21G5066d__vs_17_6_21G5075a`
- `17_6_21G5075a__vs_17_6_21G79`

## Negative-evidence audit

A path name is not enough to reconstruct missing IPSW inputs. The apparent
path sequence does not establish device identity or prove that `21G79` is the
build recorded by the payload README. Small payloads with valid READMEs remain
eligible because file count is not a validity signal. The absent `ios-17`
repository and catalog rows do not indicate that any source payload was copied
or verified.

## Verification and mutation evidence

- Selection reconciles exactly: five ordinary destination-major-17 rows = five
  planned rows.
- Recomputing the frozen census from legacy Git objects reproduces all 156
  payload classifications, 247,123 files, and 8,475,687,492 logical bytes.
- Planner write followed by `--check` produces five canonical specs.
- Spec source paths, IDs, and trees each have cardinality five.
- Tests reject route ambiguity, device mismatch, source drift, stale scope, and
  an unresolved identifier collision.
- Shard PR 1 merged one unsigned bulk commit; the reviewed head and merge commit
  have the same root tree.
- All five specs re-verify against source commit
  `d881e84676308404c6947d0218c11f347a6f3a89` and destination commit
  `28fd3d571d396c6030354e4a5cab91ab75aba685`.
- Eight unique release endpoints resolve at the pinned AppleDB commit. iPhone
  endpoints come from `osFiles/iOS`; iPad endpoints come from
  `osFiles/iPadOS`, with exact source paths retained in the registry.

## Stop conditions

Do not publish if selected or blocked cardinalities drift; a missing README is
guessed; path text replaces validated README facts; a spec fails source
validation; staging changes a source tree; a metadata root is selected from a
build name instead of device identity; or a destination or catalog audit fails.

## Bounded conclusion

Selection through merged shard state and local catalog verification are closed
for five iOS 17 rows. Four source rows remain explicitly unresolved. Final
publication remains open until this catalog PR merges unchanged and its
default-branch audit passes.
