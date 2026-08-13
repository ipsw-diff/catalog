# Release metadata closure

Recorded: 2026-08-12

## Claim and scope

Question: can the catalog deterministically annotate every indexed iOS and
macOS build with human-curated AppleDB release labels without treating those
labels as IPSW-derived payload facts?

- First lifecycle stage: select the unique `(platform, build)` keys from all
  validated catalog entry endpoints.
- Last lifecycle stage: reproduce a canonical release registry from one exact
  AppleDB Git commit and report every unresolved or ambiguous key.
- In scope: exact build/platform matching, AppleDB display versions, beta/RC
  flags, release dates, source paths, source commit provenance, deterministic
  output, and mutation/error tests.
- Excluded: catalog README rendering, changing verified entry/spec metadata,
  inferring beta ordinals from build IDs, downloading firmware, Apple Developer
  portal automation, and correcting AppleDB upstream data.

## Authority map

| Property | Authority |
| --- | --- |
| Required platform/build keys | Validated catalog entries |
| Display version, beta/RC flags, and release date | Exact AppleDB `osFiles` record |
| AppleDB source identity | Caller-supplied full Git commit plus exact repository-relative path |
| Payload version, build, content, and integrity | Existing catalog entries and immutable shard commits |
| Registry ordering and encoding | Catalog importer |

## Closure matrix

| Stage | Required evidence | Status |
| --- | --- | --- |
| Selection and trigger | Complete unique endpoint-key inventory from catalog entries | Closed: 74 entries produce 82 unique endpoint keys |
| Inputs and resources | Exact AppleDB repository, full commit, and `osFiles` records | Closed: origin and full commit are validated before immutable Git objects are read |
| Transformation | One unambiguous exact record per key; no build-pattern inference | Closed: 82 records matched; missing=0 and ambiguous=0 |
| Advertisement | Canonical registry distinguishes curated labels from payload facts | Closed: separate schema records source commit and source path per label |
| Dispatch and transport | Explicit CLI paths and commit; no implicit clone or network | Closed: importer accepts local repository, commit, entries, and output arguments |
| State transition | Check mode proves the checked-in registry is reproducible | Closed: canonical regeneration matches `metadata/releases.json` byte-for-byte |
| Outcome oracle | Cardinalities reconcile and missing/duplicate/mutated sources fail closed | Closed: 82 total records = 50 beta + 10 RC + 22 release |

## Verification evidence

- Source repository: `https://github.com/littlebyteorg/appledb`
- Source commit: `3051f8643eaf5d6d7196fb3c01a0f9ade46f1dc7`
- Real-corpus check: 82 required keys, 82 unique registry keys, no unresolved key
- Mutation checks: wrong platform, build, base version, beta/RC combination,
  display qualifier, date, repository origin, missing record, duplicate record,
  dirty worktree, and stale output
- Generated-registry channels: 50 beta, 10 RC, 22 release

The display version is copied exactly. In particular, AppleDB represents a
first beta as `beta` rather than `beta 1`; the importer does not normalize or
guess the omitted ordinal.

## Bounded conclusion

Within the selection-to-registry scope above, every catalog endpoint has one
reproducible curated label at the pinned source commit. This does not establish
that AppleDB is historically infallible, that the labels came from the IPSW, or
that README rendering consumes the registry. Rendering remains a separate
follow-up lifecycle.

## Stop conditions

Do not publish a historical registry if any required catalog key is missing or
ambiguous, the AppleDB commit is not exact, source paths escape `osFiles`, beta
and RC are both true, output is stale, or catalog entries/specifications would
need to be rewritten to accept the annotation.
