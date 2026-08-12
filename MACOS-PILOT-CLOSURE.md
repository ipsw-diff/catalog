# macOS 27 shard pilot closure

Recorded: 2026-08-11

## Claim and scope

Question: can the latest existing macOS 27 diff be selected from reviewed
legacy metadata, copied from one immutable Git subtree into a dedicated shard,
and verified byte-for-byte before it is cataloged or used as an automation
baseline?

- First lifecycle stage: select the exact legacy commit and payload path plus
  reviewed macOS 27 routing metadata.
- Last lifecycle stage: verify the reviewed shard commit against the source
  tree, manifest, file count, logical bytes, modes, and README metadata.
- Supported claim: one already-generated macOS 27 payload is faithfully
  migrated into `ipsw-diff/macos-27`.
- Excluded: earlier macOS 27 payloads, firmware download, diff generation,
  scheduling, automatic branch or pull-request creation, catalog publication,
  baseline advancement, and external announcements.

## Authority map

| Property | Authority |
| --- | --- |
| Payload paths, modes, and contents | Legacy Git subtree at the immutable source commit |
| Versions, builds, and input names | Payload README at the immutable source commit |
| Platform, device, major, and shard route | Reviewed migration specification and production selector |
| Baseline release metadata | Exact AppleDB record for macOS 27 beta 4 |
| Destination integrity | Generated manifest plus source/destination Git-tree comparison |
| Public merge state | GitHub pull-request metadata and default-branch commit |

## Initial closure matrix

| Stage | Required evidence | Initial status |
| --- | --- | --- |
| Selection and trigger | Source `d881e84676308404c6947d0218c11f347a6f3a89:27_0_26A5378n_vs_27_0_26A5388g` and reviewed destination route | Unresolved |
| Inputs and resources | README inputs, full source tree/count/bytes/modes, and exact beta 4 AppleDB metadata | Unresolved |
| Transformation | Mechanical copier preserves the source subtree and derives one manifest | Unresolved |
| Advertisement and options | No inferred platform, major, device, source, or destination fields | Unresolved |
| Dispatch and transport | Only the selected payload and manifest reach the shard review branch | Unresolved |
| State transition | Reviewed shard pull request merges to `main` | Unresolved |
| Outcome oracle | Fresh public source and destination commits reproduce all recorded identities | Unresolved |

## Negative-evidence audit

A README link, matching filename, successful copy, or clean status alone does
not prove fidelity. The source and destination trees, paths, modes, blob-derived
byte totals, README inputs, and generated manifest must agree independently.
The absence of a newer legacy directory does not prove the track is current;
live discovery is a separate lifecycle.

## Scope refinement

The initial dispatch row named only the payload and manifest. The new repository
already had a two-line bootstrap README; its review PR necessarily replaced that
README with the browsable index and added the same MIT license as the iOS pilot.
Those two reviewed shard-shell files are classified explicitly below and are
not treated as part of the payload-identity oracle.

## Current closure matrix

| Stage | Evidence | Current status |
| --- | --- | --- |
| Selection and trigger | The reviewed spec pins source `d881e84676308404c6947d0218c11f347a6f3a89:27_0_26A5378n_vs_27_0_26A5388g` and routes only to `ipsw-diff/macos-27` | Closed |
| Inputs and resources | Source README inputs, tree `59f11312d306e6abf6e6e5a1d4357b16684201bb`, 7,166 files, 70,386,271 bytes, modes, and the exact beta 4 AppleDB record agree | Closed |
| Transformation | `stage` reconstructed the source through a temporary archive and `validate-staged` independently reproduced the same payload tree and manifest | Closed |
| Advertisement and options | The strict spec supplies macOS, `Mac17,6`, major 27, immutable source, and derived shard paths; no platform or route is inferred from a directory name | Closed |
| Dispatch and transport | PR #1 contained exactly 7,166 payload files, one generated manifest, one reviewed README replacement, and one license; no other path was changed | Closed |
| State transition | `ipsw-diff/macos-27` PR #1 merged to `main` as `52185c99752b8f29fd6f344738b8289b88be28f1` | Closed |
| Outcome oracle | The merged commit passed full source/destination verification and the immutable remote audit covering both catalog entries | Closed |

## Expected versus observed inventory

| Property | Expected | Observed |
| --- | ---: | ---: |
| Legacy payloads selected | 1 | 1 |
| Destination payloads created | 1 | 1 |
| Payload files | 7,166 | 7,166 |
| Generated manifests | 1 | 1 |
| Reviewed shard-shell files | 2 | 2 |
| Unexpected changed paths | 0 | 0 |
| Source and destination payload trees | 1 equal pair | 1 equal pair |

## Verification and mutation evidence

- The mechanical copier staged tree
  `59f11312d306e6abf6e6e5a1d4357b16684201bb`, 7,166 files,
  70,386,271 logical bytes, and one generated manifest from the immutable
  legacy commit. `validate-staged` independently reproduced those facts.
- The unsigned review commit `d0841fb82bdcb27f701ab45e75c1473e8093b7f4`
  passed committed verification and a fresh public-branch clone repeated it
  before PR #1 merged.
- The public merge commit
  `52185c99752b8f29fd6f344738b8289b88be28f1` resolves the same payload tree
  and passed full verification.
- Exact AppleDB queries identified `26A5388g` as macOS 27.0 beta 4 for
  `Mac17,6`, released 2026-07-20, and `26A5406e` as the later beta 5
  candidate. No firmware was downloaded.
- The immutable remote audit fetched and verified both public catalog entries.
  Existing mutation tests reject changed payloads, manifests, README inputs,
  routes, paths, counts, bytes, modes, and stale generated indexes.

## Remaining activation conditions

- This catalog PR must merge before the macOS entry is published on the catalog
  default branch.
- macOS read-only discovery requires a separate reviewed policy and detector
  generalization.
- Generation, scheduled writes, catalog auto-publication, and external
  announcements retain their independent gates.

## Stop conditions

Do not call the pilot ready if the source selection is ambiguous, README
metadata disagrees with the reviewed spec, the copier stages an unexpected
path, any inventory property differs, the public shard commit is unmerged, or
the fresh remote audit has not passed.

## Bounded conclusion

The macOS shard pilot is closed from immutable source selection through the
merged public payload and remote integrity oracle. This PR proposes its catalog
record but does not itself establish default-branch catalog publication.
Nothing in this audit authorizes discovery, generation, scheduling, automatic
publication, or announcement.
