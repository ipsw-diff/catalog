# Release-label rendering closure

Recorded: 2026-08-12

## Claim and scope

Question: can every catalog README comparison display the exact curated
AppleDB beta, RC, or release label for both endpoints without changing payload
facts, link targets, sorting, or `catalog.json`?

- First lifecycle stage: load validated catalog entries and the checked-in
  release registry.
- Last lifecycle stage: render each endpoint label into the generated README
  and reject incomplete or conflicting registry coverage.
- In scope: registry schema validation, exact `(platform, build)` selection,
  display-label rendering in Latest and Browse sections, deterministic output,
  coverage reconciliation, and mutation tests.
- Excluded: generating or updating AppleDB metadata, inferring beta ordinals,
  rewriting catalog entries, changing release ordering, and shard contents.

## Authority map

| Property | Authority |
| --- | --- |
| Platform, build, link, device, ordering, and integrity | Validated catalog entry |
| Human-readable release label and channel | Checked-in release registry |
| README layout | Catalog renderer |
| Machine-readable catalog payload | Existing catalog entry serialization |

## Closure matrix

| Stage | Required evidence | Status |
| --- | --- | --- |
| Selection and trigger | Explicit registry path supplied to `render` | Closed: CLI default and override are explicit |
| Inputs and resources | Valid registry schema and one record per required endpoint | Closed: full schema and exact coverage are validated before rendering |
| Transformation | Exact `(platform, build)` lookup with no fallback or inference | Closed: every label lookup uses the catalog platform and build |
| Advertisement | Latest and Browse comparisons show both endpoint labels | Closed: tests and generated README exercise both surfaces and endpoints |
| Dispatch and transport | CLI passes the same validated registry to README rendering | Closed: one loaded mapping is passed through both rendering paths |
| State transition | Regeneration changes README only; `catalog.json` remains entry-derived | Closed: pre/post hashes for `catalog.json` and the registry are identical |
| Outcome oracle | 82 required keys equal 82 consumed keys; mutations fail closed | Closed: missing=0, unexpected=0, duplicate=0 |

## Expected versus observed inventory

| Inventory | Expected | Observed |
| --- | ---: | ---: |
| Catalog entries | 74 | 74 |
| Endpoint references | 148 | 148 |
| Unique `(platform, build)` endpoints | 82 | 82 |
| Registry records | 82 | 82 |
| Beta / RC / release records | 50 / 10 / 22 | 50 / 10 / 22 |
| Missing / unexpected / duplicate records | 0 / 0 / 0 | 0 / 0 / 0 |

## Negative-evidence audit

- A missing label is not treated as a final release; rendering stops.
- Apple build suffixes do not select or number betas; only the registry display
  string is rendered.
- Registry labels do not participate in sorting, links, devices, integrity
  facts, or machine-readable catalog serialization.
- Registry source paths are provenance only. The renderer validates them but
  does not read through them.

## Verification and mutation evidence

- Real-corpus load reconciles all endpoint and channel cardinalities above.
- Missing, unexpected, duplicate, base-version-conflicting,
  channel-conflicting, and parent-escaping registry records fail closed.
- Latest and Browse tests assert exact beta labels for both endpoints and both
  platforms.
- Formatting, lint, type checking, generated-output checks, the full test
  suite, pinned AppleDB regeneration, migration-plan checks, and changed
  workflow lint pass.
- `catalog.json` and `metadata/releases.json` SHA-256 hashes are unchanged by
  real-corpus rendering.

## Unresolved rows

None within the registry-to-README scope. Historical correctness of
human-curated AppleDB labels remains an upstream-source question rather than a
renderer claim.

## Bounded conclusion

The checked-in registry is completely and deterministically consumed for
README endpoint labels. This establishes closure only from validated catalog
and registry inputs through generated README text; it does not establish that
AppleDB labels are IPSW-derived or historically infallible.

## Stop conditions

Do not publish rendered labels if the registry is missing, stale, malformed,
duplicated, contains an unexpected endpoint, disagrees with catalog base
versions, or if the change alters catalog ordering, URLs, integrity facts, or
`catalog.json` payloads.
