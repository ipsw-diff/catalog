# Atomic batch migration closure

Recorded: 2026-08-12

## Claim and scope

Question: can one command take two or more reviewed migration specifications
from the same frozen legacy snapshot, stage every exact payload and generated
manifest into one clean shard worktree, verify the whole destination index, and
restore the original destination if any member fails?

- First lifecycle stage: a caller supplies an explicit non-empty spec list, one
  source repository, one destination repository, and the full destination
  `HEAD` commit.
- Last lifecycle stage: every selected payload and manifest is staged and
  verified in one reconstructed Git tree, or every copier-owned path and index
  entry is rolled back.
- Supported claim: the batch copier atomically stages already-selected,
  non-overlapping payloads for one shard.
- Excluded: selecting census rows; inferring platform, device, or route;
  generating specs; transactions across repositories; committing, pushing,
  merging, deleting legacy data, updating the catalog, or announcing. Recovery
  after abrupt process or host termination and uncooperative concurrent writers
  is also excluded; rollback covers handled in-process failures.

## Authority map

| Property | Authority |
| --- | --- |
| Batch membership | Exact spec files supplied by the caller |
| Common source snapshot | Source repository and full commit in every spec |
| Source metadata and payload identity | Strict README validation and immutable Git subtrees |
| Common destination and paths | Reviewed spec routes and destination repository origin |
| Allowed staged scope | Union of exact payload files and generated manifest paths |
| Atomic state transition | Destination index and copier-owned worktree paths relative to pinned `HEAD` |
| Outcome | One reconstructed staged Git tree checked against every source inventory |

## Initial closure matrix

| Stage | Required evidence | Initial status |
| --- | --- | --- |
| Selection and trigger | Explicit unique specs share one source snapshot and destination repository | Unresolved |
| Inputs and resources | Every source README and tree/count/bytes/modes inventory validates before use | Unresolved |
| Transformation | Each archive reconstruction and generated manifest preserves its source facts | Unresolved |
| Advertisement and options | CLI exposes no selection, inference, overwrite, commit, push, or deletion option | Unresolved |
| Dispatch and transport | Staged status equals the disjoint union of every expected batch path | Unresolved |
| State transition | Success stages all members; any failure restores the original index and removes only owned targets | Unresolved |
| Outcome oracle | Every payload and manifest validates from the same final staged root tree | Unresolved |

## Negative-evidence audit

Several successful single-payload stages do not prove atomic batch behavior.
A clean final status proves rollback only when a failure occurred after at least
one earlier member had already changed the destination. An exact aggregate file
count does not prove member identity; every subtree, manifest, and entrypoint
must be checked independently from the same staged root.

## Stop conditions

Do not call batch staging ready if empty, duplicate, overlapping, cross-source,
or cross-destination membership is accepted; a later-member failure leaves an
earlier member staged; rollback deletes a collision the copier did not create;
an unexpected path can enter the index; single-stage behavior regresses; or a
real multi-payload rehearsal has not passed both staging and independent
revalidation.

## Initial bounded conclusion

Every success-critical row is unresolved pending implementation, mutation
tests, a real two-payload rehearsal, and fresh-eyes review. This artifact does
not authorize choosing or migrating any census row.

## Current closure matrix

| Stage | Evidence | Current status |
| --- | --- | --- |
| Selection and trigger | The batch API requires at least two unique specs, sorts them by ID, and requires one source repository, full source commit, and destination repository | Closed |
| Inputs and resources | Every member passes the existing strict README validator and independent source tree/count/bytes/modes inventory before destination mutation | Closed |
| Transformation | Each member is archived, extracted, re-indexed, and compared with its source before being copied; manifests come only from measured facts | Closed |
| Advertisement and options | `stage-batch` and `validate-staged-batch` accept repeated explicit specs, repository roots, and one full destination base; neither exposes selection, routing, overwrite, commit, push, or deletion | Closed |
| Dispatch and transport | Final porcelain status must equal the disjoint union of all expected payload files and manifests | Closed |
| State transition | Synthetic later-member corruption rolls back both members; a concurrent manifest collision is preserved while every copier-owned path and index entry is removed | Closed |
| Outcome oracle | The real rehearsal and independent revalidation checked both payloads and manifests from staged root `43eef7f4d12cb13d77fce20f5bf0750a137ac311` | Closed |

## Real rehearsal inventory

| Property | Expected | Observed |
| --- | ---: | ---: |
| Explicit source payloads | 2 | 2 |
| Generated manifests | 2 | 2 |
| Payload files | 16,759 | 16,759 |
| Total staged paths | 16,761 | 16,761 |
| Payload logical bytes | 133,621,353 | 133,621,353 |
| Pre-existing paths overwritten | 0 | 0 |
| Unexpected staged paths | 0 | 0 |

The disposable iOS 27 shard began and remained at
`5bb591d78629da2a9874744a7ceb7a0c56baa709`. The source and staged tree IDs
matched independently for both real members:

- `27_0_24A5370h_vs_27_0_24A5380h`:
  `b18e701d23438ebeffd3092cb72cf6dd0506c9ef`, 8,534 files, 76,432,711 bytes.
- `27_0_24A5380h_vs_27_0_24A5390f`:
  `0f83eb81bd45938f8583ccbe2468761b00e5b5df`, 8,225 files, 57,188,642 bytes.

No rehearsal output was committed or pushed.

## Verification and mutation evidence

- Existing single-stage tests pass through the shared engine, preserving its
  exact target, origin, base, source, manifest, and rollback checks.
- Batch tests reject fewer than two specs, duplicate IDs/source paths,
  different source commits, different destination repositories, overlapping
  destination paths, and unexpected staged paths.
- A forced mutation in the second copied payload fails the final member oracle
  after the first payload was staged, then restores a clean destination with
  neither payload nor manifest remaining.
- A manifest created concurrently during the second copy is never overwritten
  or deleted; all earlier copier-owned work and index entries are rolled back.
- Formatting, lint, type checking, deterministic rendering, all 73 tests, the
  two-entry remote audit, real staging, and independent real batch revalidation
  passed.

## Bounded conclusion

Atomic batch staging is closed for two or more explicit, non-overlapping specs
from one frozen source snapshot into one clean destination shard. This does not
select census rows, generate specs, span repositories, commit or push staged
output, update the catalog, establish crash-safe transactions, or establish
publication readiness.
