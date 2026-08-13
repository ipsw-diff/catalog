# Mixed-source shard README closure

Recorded: 2026-08-13

## Claim and scope

Question: can one deterministic shard README include both payloads migrated
from the legacy corpus and payloads generated directly in the shard?

- First lifecycle stage: reviewed specs are selected for one exact destination
  repository.
- Last lifecycle stage: the renderer writes or checks one deterministic README
  containing every selected payload link.
- Supported claim: specs may name multiple immutable source repositories while
  retaining one platform, major version, destination repository, and unique
  source and destination paths.
- Excluded: firmware discovery, acquisition, diff generation, Git mutation,
  pull-request publication, and central catalog insertion.

## Authority and closure matrix

| Stage | Evidence | Status |
| --- | --- | --- |
| Selection and trigger | Exact destination repository filters reviewed specs | Closed |
| Inputs and resources | Parsed specs retain full source repositories and commits | Closed |
| Transformation | Stable device and source-path sort produces deterministic rows | Closed |
| Advertisement and options | Existing explicit output and `--check` mode remain unchanged | Closed |
| Dispatch and transport | `render-archive` writes only the requested README | Closed |
| State transition | Write mode materializes output; check mode rejects stale output | Closed |
| Outcome oracle | Mixed-source test requires links for both immutable origins | Closed |

## Negative evidence and stop conditions

Sharing a destination does not make source histories equivalent. The renderer
does not merge, rewrite, or infer source identity; each manifest and spec keeps
its own repository and full commit. Stop on mixed platforms, major versions,
destinations, duplicate IDs, or duplicate source or destination paths.

## Bounded conclusion

Deterministic README rendering across multiple immutable source repositories is
closed. Generation, publication, and catalog indexing remain separate stages.
