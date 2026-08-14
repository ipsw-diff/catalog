# Catalog publication workflow closure

Recorded: 2026-08-14

## Claim and scope

Question: can the catalog periodically inspect every reviewed shard, pin each
default branch to one exact commit, reconcile every newly merged generated
manifest, regenerate AppleDB-backed release labels and rendered indexes, and
open one review pull request without guessing identities or writing during
detection?

- First lifecycle stage: a scheduled or manually dispatched catalog workflow
  starts from the catalog default branch and the checked-in shard registry.
- Last lifecycle stage: one unsigned, non-overwriting generated branch is
  pushed and one ready catalog pull request identifies every exact shard and
  AppleDB commit used.
- Supported claim after hosted closure: the reviewed registry is completely
  reconciled for the recorded shard commits and proposed for human review.
- Excluded: shard diff generation, pull-request merge, announcement, social
  posting, repository discovery, and unattended pull-request check approval.

## Authority map

| Property | Authority |
| --- | --- |
| Shard set and default branches | Reviewed `automation/shards.json` |
| Shard snapshot identity | Full commit returned for each registered default branch and replayed by the publication job |
| Missing catalog rows | Canonical generated manifests at each exact shard commit versus checked-in catalog entries |
| Payload identity and integrity | Generated provenance, immutable source tags, and the existing source/destination verifier |
| Release labels | Exact AppleDB commit recorded in `metadata/releases.json` |
| Rendered README and JSON | Deterministic catalog renderer |
| Publication identity | Staged catalog tree, unsigned commit, deterministic non-overwriting branch, and ready pull request |

## Initial feature-closure matrix

| Stage | Required evidence | Status |
| --- | --- | --- |
| Selection and trigger | Default-branch-only schedule/manual dispatch and exact reviewed registry | Unresolved |
| Inputs and resources | Every registered shard and AppleDB resolve to full replayable commits | Unresolved |
| Transformation and signing | Reconciliation, release metadata, rendering, tests, and audit pass; commit is unsigned | Unresolved |
| Advertisement and options | Workflow exposes no arbitrary repository, branch, commit, or output inputs | Unresolved |
| Dispatch and transport | Detection has read-only permissions; publication alone can push one branch and create one PR | Unresolved |
| State transition | Candidate status is derived only from canonical spec/entry changes and publication cannot overwrite a ref | Unresolved |
| Outcome oracle | Hosted run opens exactly one ready PR whose body records all immutable inputs | Unresolved |

## Expected inventory

The registry contains exactly the reviewed iOS 12, 15, 16, 17, 18, 26, and 27
shards and macOS 15, 26, and 27 shards. Each record has one canonical HTTPS
repository route and the literal `main` default branch. Registry IDs,
repositories, and branches must be unique, and a malformed or unresolvable row
stops the complete run.

Detection resolves and records all ten shard commits plus one AppleDB commit
before classifying the catalog. Publication must replay that exact inventory;
it may not resolve moving branches again. A green run for a subset is
inconclusive and cannot publish.

## Negative-evidence audit

- No local catalog change does not prove remote shards are current unless all
  registered default branches resolved and reconciled successfully.
- A merged payload directory without its generated manifest is not a candidate.
- A reconciled entry does not establish a trustworthy label until the exact
  AppleDB snapshot supplies the endpoint metadata.
- A rendered README does not establish payload integrity; the full immutable
  catalog audit remains mandatory before publication.
- A pushed branch does not prove a ready pull request exists.
- A ready pull request created with `GITHUB_TOKEN` does not prove its
  pull-request-triggered checks ran; GitHub requires manual approval for those
  runs.

## Verification and mutation evidence

The first ten-shard rehearsal stopped at iOS 18 because its already-recorded
legacy manifests are nested below device directories. That result proved the
reconciler's flat-path assumption was not complete for the reviewed registry.
The reconciler now inventories canonical JSON paths recursively, still
classifies by manifest ID before interpreting generated provenance, and has a
regression test for a recorded nested manifest.

A complete blobless replay then resolved and reconciled this inventory:

| Shard | Exact commit | Manifests | Reconciled |
| --- | --- | ---: | ---: |
| iOS 12 | `df992098767a840532b623d707291de636dcf53e` | 1 | 0 |
| iOS 15 | `c76c3b55d4e33e86776327c54d57dabc52febb57` | 1 | 0 |
| iOS 16 | `99f4bfca44467006135abc23def654918f2d5fba` | 2 | 0 |
| iOS 17 | `1d5fb7447a64c6a15cec4450831cca359d69074d` | 25 | 0 |
| iOS 18 | `13cb572f327d0bb768e7604b8579348e6983e524` | 62 | 0 |
| iOS 26 | `760c616ec6a23bb734a7e73a6964a1bb162ecbe3` | 57 | 0 |
| iOS 27 | `02a1347af0fba002b609dc4621e49908d94502e3` | 5 | 0 |
| macOS 15 | `b8fb5003141a9e25b08b76b0f319f74bad7c5c03` | 5 | 0 |
| macOS 26 | `e74d2042bc3f6dfe3e877df76fc32c6161ffda1b` | 8 | 0 |
| macOS 27 | `5ae46bec474cd7c18200bf05e0e2c65cea39f0df` | 5 | 0 |

The resulting spec and entry directories were byte-identical to the reviewed
catalog. A second replay deliberately removed
`macos-15.4.1-24E248-24E263` from both directories. It classified 4 of 5 macOS
15 manifests as recorded, reconciled exactly 1, recreated both files
byte-for-byte, and again left the complete spec and entry directories identical
to the reviewed source.

That candidate used AppleDB commit
`d227e42c3a2449bec0c8a3b1962d7157dddb5e34`, regenerated 191 labels (95 beta,
18 RC, and 78 final), rendered both indexes, and passed formatting, lint,
type-checking, all 145 tests, render check, and release-metadata check. The
workflow and CI YAML pass `actionlint`; the helper passes `shellcheck` and Bash
syntax validation. Blobless shard fetches batch only manifest blobs plus the
payload blobs for missing rows, avoiding materialization of the complete shard
corpora.

## Final feature-closure matrix

| Stage | Evidence | Status |
| --- | --- | --- |
| Selection and trigger | Static validation enforces `main`, schedule/manual events, and the exact ten-ID registry | Closed |
| Inputs and resources | Both live replays resolved and replayed all ten full shard SHAs; candidate labels used one exact AppleDB SHA | Closed |
| Transformation and signing | Exact candidate recreation, metadata/render checks, and the 145-test suite pass; unsigned commit command is fail-checked | Closed |
| Advertisement and options | The workflow accepts no caller-controlled repository, ref, or path inputs | Closed |
| Dispatch and transport | Permission split and non-overwriting push/ready-PR commands are statically valid but have not run on GitHub | Unresolved |
| State transition | Zero-delta and one-missing-row rehearsals reconcile exact expected sets with no extra catalog paths | Closed |
| Outcome oracle | Local content oracles pass, but no hosted run has opened the ready pull request | Unresolved |

## Unresolved rows and stop conditions

Hosted dispatch/transport and the final ready-PR oracle remain unresolved. The
workflow must stop on a non-default dispatch ref, registry mismatch, missing or
abbreviated commit, origin mismatch, failed reconciliation, missing AppleDB
endpoint, dirty unexpected path, failed test/render/audit, existing publication
branch, signed commit, or failed ready-PR creation. GitHub will require a writer
to approve the pull-request-triggered CI run created by `GITHUB_TOKEN`.

## Bounded conclusion

The local multi-shard selection, reconciliation, labeling, rendering, and
validation slice is closed for the exact recorded inputs. Automatic catalog
publication is not yet closed: the merged workflow must be manually dispatched
and open one ready pull request before the final two rows can close.
