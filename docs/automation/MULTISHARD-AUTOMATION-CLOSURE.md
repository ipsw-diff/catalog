# Multi-shard firmware automation closure

Recorded: 2026-08-13

## Claim and scope

Question: can every supported iOS, iPadOS, and macOS shard discover every new
downloadable release, beta, and RC in its tracked major line, generate each
missing consecutive diff, and hand the merged result to the central catalog
without guessed builds or hard-coded IPSW URLs?

- First lifecycle stage: a scheduled shard run selects a reviewed track and
  obtains an ordered AppleDB release inventory.
- Last lifecycle stage: the exact merged shard commit is proposed in a generated
  central-catalog pull request.
- Supported claim after closure: all downloadable builds visible to the pinned
  `ipsw` and exact AppleDB snapshot are queued as consecutive edges for each
  reviewed track, with immutable source, destination, and catalog identities.
- Excluded: automatically merging pull requests, publishing social posts, and
  claiming coverage for a device or artifact type outside a track policy.

## Authority map

| Property | Authority |
| --- | --- |
| Tracked platform, major, representative device, and activation anchor | Reviewed shard `track.json` |
| Release version, build, date, beta, and RC metadata | Exact AppleDB Git commit |
| Downloadable IPSW URL, size, SHA-256, and device compatibility | Pinned `ipsw dl appledb` result |
| Already published edge and payload identity | Shard manifests at the checked-out commit |
| Generated payload | Pinned `ipsw diff` invocation and immutable source tag |
| Published shard identity | Final shard pull-request merge commit |
| Catalog identity and labels | Catalog spec, entry, release registry, and audit |

## Feature-closure matrix

| Stage | Required evidence | Initial status |
| --- | --- | --- |
| Selection and trigger | Reviewed policies for all ten shards plus a bounded schedule | Unresolved |
| Inputs and resources | Exact AppleDB commit and one verified IPSW source per queued build | Unresolved |
| Transformation and signing | Consecutive build pairs, verified downloads, pinned generator, unsigned commits | Unresolved |
| Advertisement and options | Each caller pins the reviewed reusable workflow and generator contract | Unresolved |
| Dispatch and transport | Candidate queue dispatches one non-overwriting generation branch and opens a PR | Unresolved |
| State transition | Merged manifest advances one version-train head; backlog remains visible | Unresolved |
| Outcome oracle | Post-merge catalog PR pins the exact shard merge SHA and passes the full audit | Unresolved |

## Expected inventory

The reviewed repository set contains ten shards:

- iOS 12, 15, 16, 17, 18, 26, and 27;
- macOS 15, 26, and 27.

Every shard must be classified as active, intentionally paused with affirmative
evidence, or blocked with an explicit missing resource. A successful run on one
major or one platform does not close another row.

## Negative-evidence audit

- An empty latest query does not prove a track is retired.
- A green detector does not prove intermediate builds were enumerated.
- An AppleDB release record without a compatible active IPSW source is not a
  generatable candidate.
- A generated branch does not prove a pull request was opened or merged.
- A merged shard pull request does not prove the central catalog was updated.

## Verification and mutation evidence

The schema-v2 queue has focused mutation coverage for track routing, anchor
metadata, manifest backing, skipped intermediate releases, same-train date
ambiguity, AppleDB origin, missing `ipsw` observations, and changed SHA-256
facts. It also rejects an already-merged destination whose manifest records the
wrong predecessor. A parallel-train test proves that an overlapping maintenance
release is not paired to a newer beta train.

A read-only rehearsal used AppleDB commit
`ff4db9a3836c567087dc7f2efda2b27877664ebb`, live `ipsw` 3.1.708 source
inventories, and every shard's merged manifests:

| Track | Decision | Missing edges |
| --- | --- | ---: |
| iOS 12 | Current at `16H88` | 0 |
| iOS 15 | `19H411` to `19H422` | 1 |
| iOS 16 | `20H380` to `20H392` | 1 |
| iOS 17 via iPadOS | `21H440` through `21H461` | 3 |
| iOS 18 | `22H340` through `22H373` | 3 |
| iOS 26 | Current at `23G82` | 0 |
| iOS 27 | Current at `24A5408d` | 0 |
| macOS 15 | Two independent trains from `24E248` and `24F5042g`, through `24G90` | 10 |
| macOS 26 | Current at `25G82` | 0 |
| macOS 27 | Current at `26A5406e` | 0 |

The macOS 15 rehearsal initially exposed a false chronological edge from a
15.5 beta back to 15.4.1. The final planner instead continues 15.5 betas from
the 15.5 beta anchor and routes 15.4.1 from merged 15.4 final build `24E248`.
Generation state and final shard/catalog merge identities remain unexercised.

## Unresolved rows and stop conditions

All lifecycle rows remain unresolved until the central queue contract is merged
and each shard has a reviewed policy and caller. Generation must stop on an
ambiguous release order, missing intermediate build, duplicate active source,
unsupported device, moving dependency revision, existing publication ref, or
catalog identity mismatch.

## Bounded conclusion

The current macOS 27 run proves one manually dispatched path only. It does not
establish unattended or multi-shard coverage. This document remains open until
the expected inventory and every success-critical matrix row are closed.
