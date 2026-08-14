# Catalog reconciliation closure

Recorded: 2026-08-14

## Claim and scope

Question: can catalog tooling deterministically find generated shard manifests
that are absent from the catalog and materialize their exact specs and entries
without guessing release facts or mutating GitHub?

- First lifecycle stage: an operator supplies one local shard repository and
  one full merged commit SHA.
- Last lifecycle stage: all generated manifests missing from the supplied
  catalog snapshot are verified against immutable source and destination Git
  objects and written as canonical local spec/entry pairs.
- Supported claim after closure: the local reconciliation slice is complete for
  the explicit shard commit and checked-in entry set.
- Excluded: cloning or fetching repositories, choosing a moving branch, release
  label regeneration, README/catalog rendering, commits, pushes, pull requests,
  schedules, merges, announcements, and multi-shard orchestration.

## Authority map

| Property | Authority |
| --- | --- |
| Destination identity | Explicit full commit supplied by the caller |
| Shard repository identity | Exact Git `origin` matched to the generated manifest route |
| Missing versus recorded IDs | Generated manifests at that commit and checked-in catalog entries |
| Versions, builds, inputs, route, and source commit | Canonical generated manifest |
| Generated-workflow provenance | Matching `provenance/` document and immutable source tag |
| Payload contents and integrity | Source/destination Git trees plus the existing verifier |
| Output encoding and collision behavior | Canonical catalog model and fail-closed output preflight |

## Initial feature-closure matrix

| Stage | Required evidence | Status |
| --- | --- | --- |
| Selection and trigger | Explicit local repository, full commit, and output directories | Unresolved |
| Inputs and resources | Exact manifest/provenance inventory and existing entry IDs | Unresolved |
| Transformation and signing | Manifest-derived specs pass the source/destination verifier | Unresolved |
| Advertisement and options | CLI exposes only the bounded local reconciliation contract | Unresolved |
| Dispatch and transport | Canonical writes are limited to explicit spec/entry directories | Unresolved |
| State transition | Every missing ID creates one matching pair; existing IDs remain untouched | Unresolved |
| Outcome oracle | Output sets, immutable identities, tree/count/bytes, and collision tests reconcile | Unresolved |

## Expected inventory

For one exact shard commit, manifests are partitioned into:

1. IDs already present in the supplied catalog entry directory;
2. generated IDs with matching provenance that require reconciliation; and
3. any unbacked, malformed, duplicated, or conflicting ID, which stops the
   whole operation before outputs are written.

The classification total must equal the complete manifest count observed at
the commit. A green result for one shard commit says nothing about another
commit or repository.

## Negative-evidence audit

- A payload directory without a canonical manifest is not a catalog candidate.
- A manifest absent from the current checkout is not evidence that no remote
  candidate exists; the caller owns repository fetching and commit selection.
- A manifest ID already present does not prove its destination is current; the
  existing catalog audit remains authoritative for recorded rows.
- A source commit string without matching provenance and source tag does not
  establish generated-workflow provenance.
- Successfully writing a spec does not establish catalog publication; release
  metadata, deterministic rendering, audit, review, and merge remain separate.

## Verification and mutation evidence

Ten focused tests cover exact spec/entry materialization, idempotent recorded
rows, recorded legacy-source manifests, abbreviated revisions, mutated
provenance, boolean schema confusion, missing source tags, substituted origins,
changed payload trees, and preflighted output collisions. Every tested
validation failure occurs before reconciler-owned outputs are written; abrupt
process, filesystem, or host failure during final writes remains outside this
slice.

A real rehearsal used macOS 15 merge
`b8fb5003141a9e25b08b76b0f319f74bad7c5c03`. Four of its five manifests were
present in a temporary copy of the catalog and the generated 15.4 (`24E248`) to
15.4.1 (`24E263`) row was deliberately omitted. Reconciliation classified all
five manifests, verified source tag
`payload/15_4_24E248_vs_15_4_1_24E263` at
`16017099a9f8adf8505442068fce719fa34ad1eb`, and recreated exactly one spec and
entry. Both outputs matched the reviewed catalog files byte-for-byte, including
tree `e7469b5b4c627865c3aa5ede8cd6c8e7571ea836`, 160 files, and 89,282 bytes.

## Final feature-closure matrix

| Stage | Evidence | Status |
| --- | --- | --- |
| Selection and trigger | CLI requires one local repository, one full SHA, and explicit output directories | Closed |
| Inputs and resources | Complete manifest inventory is partitioned against validated catalog entry IDs | Closed |
| Transformation and signing | Missing generated rows require provenance/tag agreement and pass the existing verifier | Closed |
| Advertisement and options | Help and generated README expose only the bounded local contract | Closed |
| Dispatch and transport | Preflight limits writes to canonical spec/entry paths and rejects collisions | Closed |
| State transition | Idempotence and legacy tests preserve recorded rows; one missing ID creates one pair | Closed |
| Outcome oracle | Focused mutations plus the five-manifest real rehearsal reconcile exact identities and counts | Closed |

## Unresolved rows and stop conditions

No success-critical row remains unresolved inside the local reconciliation
slice. Reconciliation still stops before writing on an abbreviated or moving
revision, origin mismatch, malformed manifest or provenance, missing source
tag, source/destination mismatch, output collision, or incomplete manifest
classification. Network discovery, multi-shard orchestration, release metadata,
rendering, audit, GitHub writes, and publication remain outside this claim.

## Bounded conclusion

The deterministic local reconciliation slice is closed for one explicit shard
commit and catalog snapshot. It does not establish scheduled catalog discovery,
automatic catalog pull requests, multi-shard coverage, or publication. This
artifact does not authorize GitHub mutation.
