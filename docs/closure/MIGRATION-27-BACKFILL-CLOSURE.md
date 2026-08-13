# iOS and macOS 27 legacy backfill closure

Recorded: 2026-08-12

## Claim and scope

Question: can the seven remaining ordinary census rows whose destination major
is 27 be copied into their reviewed iOS 27 or macOS 27 shards, merged there,
then recorded in the catalog with source and destination Git identity preserved
for every row?

- First lifecycle stage: select the exact set difference between ordinary
  target-major-27 census rows and existing catalog source identities, then bind
  every row to one reviewed shard track.
- Last lifecycle stage: each shard default-branch commit and each catalog entry
  independently verify against the frozen legacy source subtree.
- Supported claim: the named seven legacy rows are faithfully backfilled and
  cataloged after both shard PRs and the later catalog PR merge.
- Excluded: blocked census rows; other platform majors; deletion or rewriting
  of the legacy repository; new firmware generation; scheduled publication;
  and external announcements.

## Authority map

| Property | Authority |
| --- | --- |
| Frozen source universe and structural eligibility | Merged canonical census at legacy commit `d881e84676308404c6947d0218c11f347a6f3a89` |
| Already migrated source identities | Merged catalog entries |
| Platform, device, and target major | Reviewed `track.json` in each destination shard |
| Versions, builds, and input filenames | Strictly parsed source README |
| Source path, tree, file count, bytes, and modes | Immutable source Git objects |
| Destination route and generated manifest | Reviewed migration spec validated by catalog schema |
| Destination identity | Merged shard Git commit and independently measured subtree |
| Publication | Later catalog entry and deterministic rendered indexes |

## Initial closure matrix

| Stage | Required evidence | Initial status |
| --- | --- | --- |
| Selection and trigger | Ordinary target-major-27 census set minus cataloged source identities equals seven exact rows | Unresolved |
| Inputs and resources | Seven specs validate source README metadata, immutable trees, and reviewed shard tracks | Unresolved |
| Transformation | Same-shard batch staging reproduces every source tree and generated manifest | Unresolved |
| Advertisement and options | Shard README lists every merged payload without advancing track baselines | Unresolved |
| Dispatch and transport | One iOS PR contains four exact payloads; one macOS PR contains three exact payloads | Unresolved |
| State transition | Both shard PRs merge before any catalog row points at their immutable destination commits | Unresolved |
| Outcome oracle | Seven source trees equal seven merged destination trees and seven catalog entries pass remote audit | Unresolved |

## Expected inventory

| Shard | Remaining rows | Payload files | Logical bytes |
| --- | ---: | ---: | ---: |
| iOS 27 | 4 | 35,148 | 1,415,161,174 |
| macOS 27 | 3 | 17,456 | 688,076,888 |
| Total | 7 | 52,604 | 2,103,238,062 |

The expected set is:

- iOS: `26_5_23F77_vs_27_0_24A5355q`,
  `27_0_24A5355q_vs_27_0_24A5370h`,
  `27_0_24A5370h_vs_27_0_24A5380h`, and
  `27_0_24A5380h_vs_27_0_24A5390f`.
- macOS: `27_0_26A5353q_vs_27_0_26A5368g`,
  `27_0_26A5368g_vs_27_0_26A5378j`, and
  `27_0_26A5378j_vs_27_0_26A5378n`.

## Observed inventory

The observed inventory equals the expected inventory exactly: four iOS rows
with 35,148 payload files and 1,415,161,174 logical bytes, plus three macOS
rows with 17,456 payload files and 688,076,888 logical bytes. The combined
inventory is seven rows, 52,604 files, and 2,103,238,062 logical bytes.

- iOS default-branch destination commit:
  `148f4599b7caf915be62d6c68b121e8cf8362fd7`.
- macOS default-branch destination commit:
  `2c87c1970492719b2083e391c178c6c10fc00ddc`.
- Every new source subtree ID equals its destination subtree ID at the named
  merged commit.
- The two previously cataloged pilot payloads also re-verify at the new merged
  shard commits.

## Review-time closure matrix

| Stage | Evidence | Status |
| --- | --- | --- |
| Selection and trigger | Frozen census minus the two existing catalog source identities equals the seven expected rows, with no extras or omissions | Closed |
| Inputs and resources | All seven reviewed specs validate source README metadata, immutable source trees, and destination track policies | Closed |
| Transformation | Atomic batch validation reproduced 52,604 source files, 2,103,238,062 logical bytes, seven exact trees, and seven generated manifests | Closed |
| Advertisement and options | Both shard READMEs list the full chains; both `track.json` blobs remained byte-identical to their bases | Closed |
| Dispatch and transport | iOS PR 3 merged four payloads; macOS PR 3 merged three payloads; both discovery checks passed | Closed |
| State transition | Both shard PRs merged before catalog recording, and every entry names a full merged destination commit | Closed |
| Outcome oracle | Nine-entry remote audit passed; this seven-entry catalog PR must still merge unchanged | Unresolved |

## Verification and mutation evidence

- The batch validator rejected a modified shard README while validating the
  payload-only index, proving that an unexpected non-addition cannot silently
  enter the migration batch.
- GitHub initially skipped discovery because its bounded path-filter input did
  not reach `manifests/**`; adding `diffs/**` caused both real shard PRs to
  exercise the reusable detector.
- The detector initially rejected the valid `26.5 -> 27.0` boundary. The
  consuming migration and catalog models established destination-major routing;
  regression tests now accept that boundary and still reject a destination
  outside major 27.
- All seven new specs and both pilot specs pass source-to-merged-destination
  verification. Removing or changing a source tree, destination tree, manifest,
  entrypoint, commit, or route causes that verifier to fail closed.
- The catalog remote audit fetched immutable objects for all nine specifications
  and entries from GitHub and passed source tree, destination tree, manifest,
  entrypoint, route, and catalog-entry comparison for every row.

## Negative-evidence audit

A directory-name prefix or build prefix is not route authority. Absence from
the current catalog is not enough to select a row unless the frozen census also
classifies it as ordinary and its destination version is major 27. A successful
batch stage is not publication: a row remains unresolved until the shard merge
commit is verified and the later catalog entry is merged and remotely audited.

## Stop conditions

Stop if the set difference is not exactly seven, either track policy differs
from the explicit specs, a batch contains a row outside the expected set, any
source or staged inventory differs, a shard push exceeds service limits, a
shard PR is not merged, catalog recording uses a mutable revision, or any remote
audit fails. Do not delete legacy payloads as part of this work.

## Review-time bounded conclusion

Selection through merged shard state and remote verification are closed for the
named seven rows. The outcome remains unresolved until this catalog PR merges
unchanged. This conclusion does not cover blocked census rows, other platform
majors, source deletion, generation of new diffs, scheduled publication, or
external announcements.
