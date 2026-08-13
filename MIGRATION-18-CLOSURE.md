# iOS 18 legacy migration closure

Recorded: 2026-08-12

## Claim and scope

Question: which frozen legacy iOS 18 payloads can be deterministically planned,
published to an `ios-18` shard, and cataloged without inventing missing source
facts or hiding device identity conflicts?

- First lifecycle stage: classify the complete frozen-census destination-major-18
  set and reconcile it with reviewed selected and excluded paths.
- Last lifecycle stage in this change: record catalog entries only after every
  selected source tree matches the immutable shard `main` commit, while retaining
  all unresolved rows as visible stop conditions.
- Supported claim after this stage: the named 55 rows are published and verified
  from the frozen source through the shard and central catalog.
- Excluded: deletion of legacy data, repair of missing READMEs, coercion of the
  cross-device row, and any claim that all iOS 18 source candidates migrated.

## Authority map

| Property | Authority |
| --- | --- |
| Frozen source universe and structural classification | Census at legacy commit `d881e84676308404c6947d0218c11f347a6f3a89` |
| Exact planned and reviewed-excluded membership | `migration/major-18.json` |
| iOS route and future shard | Exact input-device prefix route in `migration/major-18.json` |
| Device identity | Device token parsed independently from both census IPSW inputs |
| Versions, builds, paths, trees, counts, bytes, and modes | Frozen census and immutable legacy Git objects |
| Spec identity for the second device-specific build pair | Reviewed device-qualified path in `migration/major-18.json` |
| Published destination | `ipsw-diff/ios-18` `main` commit `1b95b2b8bed3efaac679421c1a8a6b3111957280` |
| Human release labels | AppleDB commit `3051f8643eaf5d6d7196fb3c01a0f9ade46f1dc7` |

## Closure matrix

| Stage | Required evidence | Status |
| --- | --- | --- |
| Selection and trigger | All 56 ordinary destination-major-18 rows equal 55 planned plus one reviewed exclusion | Closed |
| Inputs and resources | Planned rows have matching input devices; seven no-README rows remain visible | Closed for 55 planned rows; 8 rows unresolved |
| Transformation | Deterministic planner writes and checks 55 unique specs; atomic staging preserves all source trees and generated manifests | Closed for 55 selected rows |
| Advertisement and options | `ipsw-diff/ios-18` has a generated 55-row archive README, and the catalog renders all 55 rows with pinned AppleDB labels | Closed for 55 selected rows |
| Dispatch and transport | One explicit 55-spec batch staged 55,821 files and 55 manifests with no unexpected paths | Closed for 55 selected rows |
| State transition | Shard PR #1 merged before catalog entries were generated against immutable shard `main` | Closed for 55 selected rows |
| Outcome oracle | The merge tree equals the reviewed migration tree, and the 129-entry remote catalog audit re-verifies every source and destination | Closed for 55 selected rows; 8 source rows unresolved |

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
single-device catalog schema. Fifty-five green destination verifications do not
prove that the eight excluded or blocked source rows migrated; they remain
outside the published selection and visible above.

## Verification and mutation evidence

- Selection reconciles exactly: 56 ordinary rows = 55 planned + 1 reviewed
  exclusion.
- Recomputing the frozen census from the legacy Git objects reproduces all 156
  payload classifications, 247,123 files, and 8,475,687,492 logical bytes.
- Planner write followed by `--check` produces 55 canonical specs.
- Spec source paths and IDs both have cardinality 55.
- Atomic staging and independent pre-commit revalidation both report 55
  payloads, 55,821 files, 355,604,076 logical bytes, and 55 manifests.
- All 55 payloads pass post-commit source-to-destination verification.
- Shard merge commit `1b95b2b8bed3efaac679421c1a8a6b3111957280`
  and reviewed migration commit `277a9a9136c01509d646b7002871aad1a4407be7`
  have the same tree `51397bf03ef8f738d6bfaeef18fc7e18affa98cc`.
- The generated catalog contains 55 iOS 18 entries at that one destination
  commit, with 55 distinct integrity trees and matching aggregate files/bytes.
- The pinned AppleDB registry covers all 59 unique iOS 18 endpoint builds used
  by the entries: 30 beta, 7 RC, and 22 release records.
- The full remote audit passes for all 129 catalog entries.
- Tests reject an unreviewed exclusion, a missing reviewed exclusion, device
  mismatch, route ambiguity, source drift, stale scope, and unresolved ID
  collision; one reviewed device-qualified path resolves the real collision,
  while an unnecessary device qualification is rejected.

## Stop conditions

Do not expand the published iOS 18 set if selected, excluded, or blocked
cardinalities drift; a missing README is guessed; a cross-device row is
silently coerced to one device; a spec fails source validation; staging changes
a source tree; or a destination, release-metadata, or catalog audit fails.

## Bounded conclusion

The frozen-source-to-catalog lifecycle is closed for 55 iOS 18 rows. They are
published at one immutable shard commit and independently re-verified by the
catalog audit. Eight source rows remain explicitly unresolved, so this does not
claim that every iOS 18 source candidate migrated; the legacy corpus remains
authoritative for those rows.
