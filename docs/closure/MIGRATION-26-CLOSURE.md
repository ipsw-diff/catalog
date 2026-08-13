# iOS and macOS 26 legacy migration closure

Recorded: 2026-08-12

## Claim and scope

Question: can every ordinary frozen-census row whose destination major is 26
be deterministically planned, copied into the reviewed iOS 26 or macOS 26
archive shard, merged there, then recorded in the catalog with source and
destination Git identity preserved?

- First lifecycle stage: select the exact ordinary destination-major-26 set
  from the frozen census and prove it equals the reviewed allowlist in
  `migration/major-26.json`.
- Last lifecycle stage: each shard default-branch commit and each catalog entry
  independently verify against the frozen legacy source subtree.
- Supported claim after closure: the named 65 rows are faithfully migrated and
  cataloged.
- Excluded: blocked census rows; other destination majors; deletion or rewrite
  of the legacy repository; new firmware generation; scheduled discovery;
  external announcements; and any claim that the historical graph is a single
  linear release chain.

## Authority map

| Property | Authority |
| --- | --- |
| Frozen source universe and structural eligibility | Merged census at legacy commit `d881e84676308404c6947d0218c11f347a6f3a89` |
| Exact migration membership | Reviewed 65-path allowlist in `migration/major-26.json` |
| Platform and destination shard | Reviewed input-device-prefix routes in `migration/major-26.json` |
| Device identity | Exact shared device token parsed from both IPSW filenames in a census row |
| Versions, builds, inputs, source tree, counts, bytes, and modes | Frozen census and immutable source Git objects |
| Destination paths and manifests | Migration spec schema and deterministic planner output |
| Destination identity | Merged shard Git commit and independently measured subtree |
| Publication | Later catalog entry and deterministic rendered indexes |

## Initial closure matrix

| Stage | Required evidence | Initial status |
| --- | --- | --- |
| Selection and trigger | Ordinary destination-major-26 census set equals the exact 65-path reviewed allowlist | Unresolved |
| Inputs and resources | Every row has one exact route, matching from/to device tokens, and a valid source README/tree | Unresolved |
| Transformation | Planner output is deterministic; same-shard staging reproduces every source tree and manifest | Unresolved |
| Advertisement and options | Archive shard READMEs list exactly the merged payload set; no discovery workflow is enabled | Unresolved |
| Dispatch and transport | One bounded bulk PR per shard contains only its reviewed payloads and manifests | Unresolved |
| State transition | Both shard PRs merge before catalog entries point at immutable destination commits | Unresolved |
| Outcome oracle | All 65 merged destination trees and catalog entries pass local and remote audit | Unresolved |

## Expected inventory

| Shard | Rows | Payload files | Logical bytes |
| --- | ---: | ---: | ---: |
| iOS 26 | 57 | 89,307 | 3,201,091,519 |
| macOS 26 | 8 | 7,251 | 1,181,832,255 |
| Total | 65 | 96,558 | 4,382,923,774 |

The allowlist is stored once, as machine-readable policy, in
`migration/major-26.json`. The unpublished plan remains in
`migration/specs-26/`; `specs/` is reserved for rows with matching published
catalog entries. A planner must reject a missing, additional, duplicated,
blocked, differently routed, or non-major-26 row before writing any
specification.

## Negative-evidence audit

A directory name, build prefix, file count, or current catalog absence is not
route authority. An IPSW filename route is valid only because the reviewed
policy maps its exact device prefix and the planner proves both inputs carry the
same device token. Tiny payloads remain in scope when the census classifies
their README as an ordinary two-IPSW comparison. Branch points and disconnected
device-specific comparisons are not silently linearized.

## Planner review-time closure

| Stage | Evidence | Status |
| --- | --- | --- |
| Selection and trigger | The planner recomputed the complete ordinary destination-major-26 census set and matched all 65 reviewed paths with no omission or extra | Closed |
| Inputs and resources | All 65 specs re-parsed the immutable source README and measured 96,558 files, 4,382,923,774 bytes, and 65 distinct trees | Closed |
| Transformation | A write followed by `--check` produced identical specs in the unpublished migration namespace; preflight tests reject stale scope, partial writes, route ambiguity, source drift, device drift, and identifier collisions | Closed for planning only |
| Advertisement and options | A deterministic archive README renderer/checker is implemented; destination repositories and rendered outputs do not exist yet | Unresolved |
| Dispatch and transport | No payload has been copied or pushed | Unresolved |
| State transition | No shard or catalog merge for major 26 exists | Unresolved |
| Outcome oracle | Source validation passes, but destination and catalog audits cannot run yet | Unresolved |

## Publication-time closure

| Stage | Evidence | Status |
| --- | --- | --- |
| Selection and trigger | The 65 reviewed specs were promoted to `specs/` while the deterministic plan remained in `migration/specs-26/`; the catalog audit proves the complete 74-entry spec and entry identifier sets are equal | Closed |
| Inputs and resources | All 65 rows revalidated against frozen source commit `d881e84676308404c6947d0218c11f347a6f3a89` | Closed |
| Transformation | Staging and independent staged-tree validation reproduced 57 iOS payloads and 8 macOS payloads with exactly 96,558 files and 4,382,923,774 logical bytes | Closed |
| Advertisement and options | Generated archive READMEs check with exactly 57 iOS rows and 8 macOS rows; each shard remains archive-only and the staged scope contained no unexpected path | Closed |
| Dispatch and transport | `ipsw-diff/ios-26#1` and `ipsw-diff/macos-26#1` each contained one unsigned bulk payload commit and were merged without per-diff commits | Closed |
| State transition | iOS `main` is `181d2d99f2d683c3e4df8a62949568c109785dc1` with tree `bd72b971018a7fdcf616eabee5910780696edc48`; macOS `main` is `21b19bf3a6e32c240be5ffd7abc3b78ce2c38a5b` with tree `2bfdd0ff3396f490e066966d4f6314339d9a6c8b`; both trees equal their independently verified PR-head trees | Closed |
| Outcome oracle | The remote audit verified all 74 catalog entries, including all 65 major-26 source trees, destination trees, manifests, entrypoints, and canonical catalog entries | Closed |

## Expected versus observed inventory

| Shard | Expected rows | Observed rows | Expected files | Observed files | Expected bytes | Observed bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| iOS 26 | 57 | 57 | 89,307 | 89,307 | 3,201,091,519 | 3,201,091,519 |
| macOS 26 | 8 | 8 | 7,251 | 7,251 | 1,181,832,255 | 1,181,832,255 |
| Total | 65 | 65 | 96,558 | 96,558 | 4,382,923,774 | 4,382,923,774 |

## Stop conditions

Stop if selection differs from the 65-path allowlist, a row matches zero or
multiple routes, from/to device tokens differ, source facts differ from the
frozen census, a staged batch contains an extra or omission, a shard push is
rejected, a shard PR is not merged, a catalog entry uses a mutable revision, or
any local or remote audit fails. Do not delete legacy payloads in this work.

## Current bounded conclusion

The named 65-row iOS 26 and macOS 26 migration is faithfully copied, merged,
and cataloged within the scope above. Every success-critical row is closed and
the final remote audit reconciles the complete 74-entry published catalog.
This conclusion does not cover blocked census rows, other destination majors,
future release discovery, diff generation, announcement automation, or removal
of the legacy corpus.
