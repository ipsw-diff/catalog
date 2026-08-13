# iOS 18 legacy migration closure

Recorded: 2026-08-12

## Claim and scope

Question: which frozen legacy iOS 18 payloads can be deterministically planned
for an `ios-18` shard without inventing missing source facts or hiding device
identity conflicts?

- First lifecycle stage: classify the complete frozen-census destination-major-18
  set and reconcile it with reviewed selected and excluded paths.
- Last lifecycle stage in this change: produce canonical migration specs for
  every eligible selected path and retain all unresolved rows as visible stop
  conditions.
- Supported claim after this stage: the named 55 rows are ready for later
  source-to-destination staging and verification.
- Excluded: repository creation, copying, commits, pushes, catalog publication,
  deletion of legacy data, repair of missing READMEs, and any final migration
  claim.

## Authority map

| Property | Authority |
| --- | --- |
| Frozen source universe and structural classification | Census at legacy commit `d881e84676308404c6947d0218c11f347a6f3a89` |
| Exact planned and reviewed-excluded membership | `migration/major-18.json` |
| iOS route and future shard | Exact input-device prefix route in `migration/major-18.json` |
| Device identity | Device token parsed independently from both census IPSW inputs |
| Versions, builds, paths, trees, counts, bytes, and modes | Frozen census and immutable legacy Git objects |
| Spec identity for the second device-specific build pair | Reviewed device-qualified path in `migration/major-18.json` |

## Closure matrix

| Stage | Required evidence | Status |
| --- | --- | --- |
| Selection and trigger | All 56 ordinary destination-major-18 rows equal 55 planned plus one reviewed exclusion | Closed |
| Inputs and resources | Planned rows have matching input devices; seven no-README rows remain visible | Closed for 55 planned rows; 8 rows unresolved |
| Transformation | Deterministic planner writes and checks 55 unique specs | Closed for planning only |
| Advertisement and options | `ipsw-diff/ios-18` exists with an archive README | Unresolved |
| Dispatch and transport | Every planned source tree is staged into a bounded shard batch | Unresolved |
| State transition | Shard merge precedes catalog publication | Unresolved |
| Outcome oracle | Destination trees and catalog entries independently equal source trees | Unresolved |

## Expected inventory

| Classification | Rows | Payload files | Logical bytes |
| --- | ---: | ---: | ---: |
| Planned | 55 | 55,821 | 355,604,076 |
| Reviewed exclusion: from/to devices differ | 1 | 3 | 612,358 |
| Census-blocked: missing README | 7 | 17,385 | 1,020,977,539 |
| Total iOS 18 source candidates | 63 | 73,209 | 1,377,193,973 |

The planned rows contain 55 distinct source paths and 55 distinct spec IDs.
Two source paths compare the same builds on different devices. The ordinary
top-level iPhone17,1 row retains the conventional build-pair ID; the nested
iPhone17,5 row receives the reviewed suffix `iPhone17,5`. Both source paths and
both payload trees remain distinct.

## Unresolved source rows

The following seven paths lack tracked READMEs at the frozen source commit, so
their two IPSW inputs and device identity cannot be established without a new
reviewed authority:

- `17_5_1_21F90__vs_18_0_22A5282m`
- `18_0_22A5282m__vs_18_0_22A5297f`
- `18_0_22A5297f__vs_18_0_22A5307f`
- `18_0_22A5307f__vs_18_0_22A5307i`
- `18_0_22A5307i__vs_18_0_22A5316j`
- `18_0_22A5316k__vs_18_0_22A5326f`
- `18_0_22A5316k__vs_18_1_22B5007p`

`18_1_22B5045g__vs_18_1_22B5045h` has a valid README but compares
`iPhone16,2` with `iPhone17,1`. It is explicitly excluded from planning rather
than silently represented as a single-device diff.

## Negative-evidence audit

A path name is not enough to reconstruct missing IPSW inputs. Matching version
or build text does not prove matching device identity. A structurally valid
README does not make a cross-device comparison representable by the existing
single-device catalog schema. The absent `ios-18` repository and catalog rows
do not indicate that any source payload was copied or verified.

## Verification and mutation evidence

- Selection reconciles exactly: 56 ordinary rows = 55 planned + 1 reviewed
  exclusion.
- Recomputing the frozen census from the legacy Git objects reproduces all 156
  payload classifications, 247,123 files, and 8,475,687,492 logical bytes.
- Planner write followed by `--check` produces 55 canonical specs.
- Spec source paths and IDs both have cardinality 55.
- Tests reject an unreviewed exclusion, a missing reviewed exclusion, device
  mismatch, route ambiguity, source drift, stale scope, and unresolved ID
  collision; one reviewed device-qualified path resolves the real collision,
  while an unnecessary device qualification is rejected.

## Stop conditions

Do not create or populate the shard if selected, excluded, or blocked
cardinalities drift; a missing README is guessed; a cross-device row is
silently coerced to one device; a spec fails source validation; staging changes
a source tree; or a destination or catalog audit fails.

## Bounded conclusion

The selection-to-spec lifecycle is closed for 55 iOS 18 rows. Eight source
rows remain explicitly unresolved, and every destination and publication stage
remains open. No payload has been copied or published by this planning change.
