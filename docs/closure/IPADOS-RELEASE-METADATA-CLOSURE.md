# iPadOS release-metadata closure

Recorded: 2026-08-12

## Claim and scope

Question: can catalog entries routed as platform `iOS` select pinned AppleDB
`iPadOS` records when their preserved device identity is iPad, without widening
all iOS metadata lookup or changing catalog platform identity?

- First lifecycle stage: a catalog endpoint supplies platform, device, version,
  and build.
- Last lifecycle stage: the checked release registry preserves catalog platform
  `iOS`, exact AppleDB source path, and curated display label for rendering.
- Supported claim: iPad catalog endpoints select only `osFiles/iPadOS`; other
  iOS endpoints select only `osFiles/iOS`; macOS remains unchanged.
- Excluded: changing shard routing, inferring product families from build text,
  supporting other AppleDB OS aliases, or modifying AppleDB data.

## Authority map

| Property | Authority |
| --- | --- |
| Catalog platform and device | Validated catalog entry |
| AppleDB OS family | Device selection rule: iPad prefix maps to iPadOS; otherwise iOS remains iOS |
| Version, build, channel, and release date | Record at pinned AppleDB commit |
| Registry source provenance | Exact AppleDB Git path selected by the importer |
| Rendered label | Registry record after exact endpoint-coverage validation |

## Closure matrix

| Stage | Required evidence | Initial status |
| --- | --- | --- |
| Selection and trigger | Preserved device prefix `iPad` selects iPadOS while catalog platform remains iOS | Closed |
| Inputs and resources | Importer requires exactly one matching build below only the selected AppleDB OS root | Closed |
| Transformation | AppleDB `osStr: iPadOS` is validated before only the registry platform field normalizes to iOS | Closed |
| Advertisement and options | CLI exposes no caller override for the device-derived AppleDB OS root | Closed |
| Dispatch and transport | Generated registry preserves every exact iPadOS source path | Closed |
| State transition | Stale output, mismatched `osStr`, and both directions of root swapping fail | Closed |
| Outcome oracle | All 148 endpoints load with exact coverage and the 134-entry catalog renders deterministically | Closed |

## Stop conditions

Do not publish if an iPad endpoint falls back to `osFiles/iOS`; an iPhone
endpoint accepts `osFiles/iPadOS`; AppleDB `osStr` differs from the selected
root; the registry loses the exact source path; or coverage becomes ambiguous.

## Verification evidence

- An iPad fixture with same-build iOS decoys selects only iPadOS records and
  emits catalog platform `iOS` with exact iPadOS paths.
- A record below `osFiles/iPadOS` whose `osStr` says iOS is rejected.
- Checked-registry tests reject an iPad endpoint below `osFiles/iOS` and an
  iPhone endpoint below `osFiles/iPadOS`.
- The pinned AppleDB rehearsal resolves iOS 17 iPad builds `21H420`, `21H423`,
  `21H433`, and `21H440` below `osFiles/iPadOS`, while the four iPhone builds
  remain below `osFiles/iOS`.
- Path enumeration reads Git tree identity without requesting every blob size;
  only matched catalog-endpoint records are read. The rehearsal reads 148
  matched records in total, including the eight new iOS 17 endpoints.

## Bounded conclusion

All success-critical rows are closed for the scoped iPadOS release-metadata
mapping. This does not add iPadOS as a catalog platform, infer device identity
from build text, or cover unreviewed AppleDB OS aliases.
