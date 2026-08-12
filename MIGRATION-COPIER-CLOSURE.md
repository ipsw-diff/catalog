# Mechanical migration copier closure

Recorded: 2026-08-11

## Claim and scope

Question: can one reviewed migration specification materialize an exact Git
subtree from an immutable legacy commit into its derived shard paths, generate
the manifest from measured facts, and leave only those outputs staged for human
review without overwriting or modifying any pre-existing content?

- First lifecycle stage: accept an explicit spec, a source repository containing
  its immutable commit, and a clean destination worktree at a known `HEAD`.
- Last lifecycle stage: reconstruct the destination index, prove the staged
  payload is the same Git tree as the source subtree, and report the staged
  paths without committing, pushing, or deleting anything.
- Supported claim: the copier faithfully stages one already-selected payload
  and its derived manifest.
- Excluded: selecting migrations, inferring metadata, creating repositories or
  branches, committing, pushing, merging, deleting legacy data, generating new
  firmware diffs, updating the catalog, and announcing externally.

## Authority map

| Property | Authority |
| --- | --- |
| Source payload paths, modes, and blobs | Source Git subtree at the spec's immutable commit |
| Versions, builds, inputs, platform, device, and route | Reviewed migration spec validated against the source README |
| Destination payload path and manifest path | Deterministic derivation enforced by the spec schema |
| Staged payload identity | Destination Git index reconstructed with `git write-tree` |
| Allowed staged scope | Exact index delta against destination `HEAD` |

## Initial closure matrix

| Stage | Required evidence | Initial status |
| --- | --- | --- |
| Selection and trigger | Explicit spec plus exact source commit/path and destination `HEAD` | Unresolved |
| Inputs and resources | Source README and full tree/count/bytes/modes inventory | Unresolved |
| Transformation | Archive extraction and destination materialization preserve the source tree | Unresolved |
| Advertisement and options | CLI exposes no inference, overwrite, commit, push, or deletion options | Unresolved |
| Dispatch and transport | Only payload and manifest paths enter the destination index | Unresolved |
| State transition | Clean worktree becomes one verified staged payload and manifest | Unresolved |
| Outcome oracle | Reconstructed staged subtree equals source tree/count/bytes/modes | Unresolved |

## Expected versus observed inventory

| Property | Expected | Observed |
| --- | ---: | ---: |
| Source payloads selected | 1 | 1 |
| Destination payloads created | 1 | 1 |
| Destination manifests created | 1 | 1 |
| Pre-existing paths overwritten | 0 | 0 |
| Unexpected staged paths | 0 | 0 |

## Negative-evidence audit

A clean worktree, successful archive extraction, or successful `git add` alone
does not prove fidelity. The outcome oracle must compare the source inventory to
the destination index after materialization. Absence of an overwrite error does
not prove the target was absent; both the worktree and `HEAD` must be checked.

## Stop conditions

Do not call the copier ready while any success-critical row is unresolved, the
real pilot has not reproduced all 4,389 files and 57,800,821 logical bytes, an
overwrite or mutation test succeeds unexpectedly, or the command can stage a
path outside its exact payload and manifest targets.

## Current closure matrix

| Stage | Evidence | Current status |
| --- | --- | --- |
| Selection and trigger | Explicit spec pins source `d881e84676308404c6947d0218c11f347a6f3a89`; caller pins destination base `e406041df6f1a0cda7402d7a961c724aba5af86a` | Closed |
| Inputs and resources | Strict README validation plus source tree `c8b4d57f870c15eedcb953456ab61707ed0e3cbe`, 4,389 files, 57,800,821 bytes, and modes | Closed |
| Transformation | Temporary archive extraction is re-indexed and compared to the source before destination copying | Closed |
| Advertisement and options | CLI accepts only spec, source repo, destination repo, and full destination base commit | Closed |
| Dispatch and transport | Destination status contains exactly 4,389 payload files plus one derived manifest | Closed |
| State transition | Disposable pre-pilot shard clone remains at the pinned `HEAD` with exactly 4,390 additions staged | Closed |
| Outcome oracle | Reconstructed staged payload tree equals both the source and merged pilot tree | Closed |

## Verification and mutation evidence

- The real iOS 27 rehearsal staged tree `c8b4d57f870c15eedcb953456ab61707ed0e3cbe`,
  4,389 files, 57,800,821 logical bytes, and one manifest from the pre-pilot
  destination commit.
- The payload tree equals the merged pilot payload tree. The newly generated
  manifest is semantically identical to the pilot manifest but uses canonical
  sorted JSON keys; manifest byte identity is deliberately not a payload oracle.
- Tests reject dirty worktrees, changed bases, wrong remotes, pre-existing
  targets, payload mutation, manifest mutation, extra staged paths, duplicate
  Markdown sections, unexpected Markdown content, unsafe input paths, and
  symlinked destination parents.
- A forced post-copy mutation fails the staged-tree oracle and rolls the
  destination back to a clean worktree.
- A simulated concurrent manifest collision is never overwritten or removed;
  rollback deletes only paths that the copier exclusively reserved itself.

## Bounded conclusion

The scoped copier candidate faithfully stages one explicitly selected payload
and derived manifest for review. This does not establish selection policy,
bulk-migration readiness, source deletion safety, or any automation beyond the
first and last lifecycle stages named above. Publication readiness still waits
for review, CI, and merge of both the catalog base and this stacked follow-up.
