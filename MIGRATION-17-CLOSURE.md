# iOS 17 legacy migration closure

Recorded: 2026-08-12

## Claim and scope

Question: which frozen legacy iOS 17 payloads can be deterministically planned
for an `ios-17` shard without guessing facts absent from the source corpus?

- First lifecycle stage: classify the complete frozen-census destination-major-17
  set and reconcile it with the reviewed selected paths.
- Last lifecycle stage in this change: produce canonical migration specs for
  every eligible selected path and retain blocked rows as visible stop conditions.
- Supported claim after this stage: the named five rows are ready for later
  source-to-destination staging and verification.
- Excluded: repository creation, copying, commits, pushes, catalog publication,
  deletion of legacy data, repair of missing READMEs, and any final migration
  claim.

## Authority map

| Property | Authority |
| --- | --- |
| Frozen source universe and structural classification | Census at legacy commit `d881e84676308404c6947d0218c11f347a6f3a89` |
| Exact planned membership | `migration/major-17.json` |
| iOS routes and future shard | Exact iPad and iPhone input-prefix routes in `migration/major-17.json` |
| Device identity | Device token parsed independently from both census IPSW inputs |
| Versions, builds, paths, trees, counts, bytes, and modes | Frozen census and immutable legacy Git objects |

## Closure matrix

| Stage | Required evidence | Status |
| --- | --- | --- |
| Selection and trigger | All five ordinary destination-major-17 rows equal the five reviewed planned paths | Closed |
| Inputs and resources | Planned rows have matching input devices; four no-README rows remain visible | Closed for 5 planned rows; 4 rows unresolved |
| Transformation | Deterministic planner writes and checks five unique specs | Closed for planning only |
| Advertisement and options | `ipsw-diff/ios-17` exists with an archive README | Unresolved |
| Dispatch and transport | Every planned source tree is staged into a bounded shard batch | Unresolved |
| State transition | Shard merge precedes catalog publication | Unresolved |
| Outcome oracle | Destination trees and catalog entries independently equal source trees | Unresolved |

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

## Stop conditions

Do not create or populate the shard if selected or blocked cardinalities drift;
a missing README is guessed; path text replaces validated README facts; a spec
fails source validation; staging changes a source tree; or a destination or
catalog audit fails.

## Bounded conclusion

The selection-to-spec lifecycle is closed for five iOS 17 rows. Four source
rows remain explicitly unresolved, and every destination and publication stage
remains open. No payload has been copied or published by this planning change.
