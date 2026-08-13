# Catalog pilot closure

Recorded: 2026-08-11

## Claim and scope

Question: can a checked-in, explicit specification verify one migrated Git
subtree at immutable source and destination commits, then produce a deterministic
human and machine catalog without deriving platform or release semantics from a
legacy directory name?

- First lifecycle stage: select an exact source commit/path and reviewed semantic
  metadata in a migration specification.
- Last lifecycle stage: fetch the immutable source and destination, verify their
  identity and manifest, and reproduce the catalog outputs byte-for-byte.
- In scope: schema validation, local full verification, scalable remote audit,
  deterministic rendering, mutation tests, CI, and the merged iOS 27 pilot.
- Excluded: mechanical staging of additional legacy payloads, bulk migration,
  source deletion, redirects, generation of new diffs, macOS publication,
  scheduler activation, X credentials, and external announcements.

## Authority map

| Property | Authority |
| --- | --- |
| Payload paths, modes, and contents | Source and destination Git subtrees at immutable commits |
| Versions, builds, and input names | Source payload README plus reviewed spec |
| Platform, device, major, and destination route | Reviewed spec constrained by schema policy |
| Manifest facts | Full local source/destination inventory |
| Catalog records and README | Validated entry files rendered deterministically |
| Public repository and merge state | GitHub API and a fresh default-branch clone |

## Initial closure matrix

| Stage | Required evidence | Initial status |
| --- | --- | --- |
| Selection and trigger | Full source/destination commits and explicit spec | Unresolved |
| Inputs and resources | Exact source README, tree, count, bytes, and modes | Unresolved |
| Transformation | Entry and indexes derive only from verified facts | Unresolved |
| Advertisement | README and JSON catalog use immutable links | Unresolved |
| Dispatch and transport | Reviewed catalog branch reaches public remote | Unresolved |
| State transition | Catalog PR merges to default branch | Unresolved |
| Outcome oracle | Fresh public clone reproduces outputs and remote audit | Unresolved |

## Current closure matrix

| Stage | Evidence | Current status |
| --- | --- | --- |
| Selection and trigger | Spec pins source `d881e84676308404c6947d0218c11f347a6f3a89`, destination `2ed100600c64666ae0347694e17e0aa2f80cb63e`, and exact paths | Closed |
| Inputs and resources | README metadata, tree `c8b4d57f870c15eedcb953456ab61707ed0e3cbe`, 4,389 files, 57,800,821 bytes, and modes agree | Closed |
| Transformation | Entry and generated outputs reproduce deterministically | Closed |
| Advertisement | Commit-pinned payload and manifest links resolve | Closed |
| Dispatch and transport | Public `ipsw-diff/catalog` repository and `agent/catalog-pilot` review branch | Closed |
| State transition | PR #1 merged to `main` as `56ae4039fb6e287daf9765dc23755979f36df96a` with successful CI | Closed |
| Outcome oracle | A fresh public `main` clone at `db63199852bb5e4014ac02c4ed3569974f0cd252` reproduced the generated outputs and passed the immutable remote audit | Closed |

## Expected versus observed inventory

| Property | Expected | Observed |
| --- | ---: | ---: |
| Catalog entries | 1 | 1 |
| Migration specifications | 1 | 1 |
| Payload files | 4,389 | 4,389 |
| Logical bytes | 57,800,821 | 57,800,821 |
| Payload tree | `c8b4d57f870c15eedcb953456ab61707ed0e3cbe` | `c8b4d57f870c15eedcb953456ab61707ed0e3cbe` |

## Negative-evidence audit

A rendered link, matching count, or successful fetch alone does not prove
fidelity. Full recording compares tree IDs, paths, modes, blob-derived byte
totals, README metadata, and the manifest. Recurring remote audit uses the tree
identity as the primary content oracle and fetches only the source README plus
destination README and manifest; it does not pretend that absence of downloaded
payload blobs proves their contents.

## Verification and mutation evidence

- The real pilot passes full local verification and an independent partial-clone
  remote audit from both public GitHub repositories.
- PR #1 merged to the public default branch as
  `56ae4039fb6e287daf9765dc23755979f36df96a`. A later fresh clone of public
  `main` at `db63199852bb5e4014ac02c4ed3569974f0cd252` passed formatting, lint,
  type checking, all 31 tests, deterministic rendering, and the remote audit.
- Tests reject payload mutation, manifest mutation, README/spec disagreement,
  unsafe routes and paths, unknown schema keys, duplicate entries, mismatched
  spec/entry sets, overwrite attempts, and stale generated files.
- Formatting, lint, type checking, tests, and generated-output checks run from a
  locked uv environment. CI repeats them and the public remote audit.

## Stop conditions

Do not call the catalog pilot complete if the public repository is not on
`main`, the review PR is unmerged, a fresh clone cannot reproduce generated
outputs, remote audit fails, or any success-critical row above is unresolved.

## Bounded conclusion

The one-entry catalog pilot is published and complete within the lifecycle scope
defined above. This does not establish bulk-migration safety or activate shard
and X automation.

## Landing-page navigation extension

Recorded: 2026-08-12

Claim: the generated landing page places each platform's newest major-version
diffs side by side and newest first, while retaining every catalog entry in a
collapsed, versioned integrity table.

- First lifecycle stage: load the complete, schema-validated catalog entry set.
- Last lifecycle stage: deterministically render the README with a compact
  latest section and one complete browser group per platform and major version.
- Excluded: GitHub responsive styling, claims that disconnected historical
  comparisons form one release sequence, and publication or merge state.

| Stage | Evidence | Status |
| --- | --- | --- |
| Selection and trigger | All checked-in entries are loaded before grouping | Closed |
| Inputs and resources | Platform, major, version, build, links, and integrity facts come from validated entries | Closed |
| Transformation | Current major is selected independently per platform; comparisons use deterministic release/build ordering | Closed |
| Advertisement | The top table exposes at most five iOS and five macOS links together; collapsed platform groups contain collapsed major-version groups in descending order | Closed |
| Dispatch and transport | Every link remains commit-pinned and uses the existing comparison renderer | Closed |
| State transition | Rendering does not mutate entries, specifications, or shard state | Closed |
| Outcome oracle | Tests and generated-output checks prove ordering, grouping, balanced disclosure blocks, and deterministic output | Closed |

The navigation layer is intentionally derived from catalog records rather than
maintained by hand. Moving supporting Markdown into `docs/` changes repository
navigation only; it does not delete audit evidence or alter catalog authority.
