# macOS 27 beta 5 catalog closure

Recorded: 2026-08-13

## Claim and scope

Question: can the directly generated macOS 27 beta 4 to beta 5 diff be added to
the central catalog from immutable Git and AppleDB identities without manually
copying payload facts?

- First lifecycle stage: verify shard PR 5 merged at exact commit
  `317343def47d4173c9605fb7f38726256e0bfbbc` and its permanent source tag points
  to payload-only commit `79b016493a2b0e5b0719ef722af873554474572b`.
- Last lifecycle stage: re-audit the derived entry and deterministically render
  the catalog, release metadata, and README.
- Supported claim: the catalog entry and beta label are derived from immutable
  shard and AppleDB commits and agree with the merged payload manifest.
- Excluded: changing the shard payload, dispatching another generation run,
  merging this catalog change, or announcing the release.

## Authority and closure matrix

| Stage | Evidence | Status |
| --- | --- | --- |
| Selection and trigger | Exact merged shard commit and reviewed one-entry spec | Closed |
| Inputs and resources | Source tag commit, merged destination, and AppleDB `ff4db9a3836c567087dc7f2efda2b27877664ebb` | Closed |
| Transformation | `record` measures Git and checks the canonical shard manifest | Closed |
| Advertisement and options | Generated README labels build `26A5406e` as macOS 27.0 beta 5 | Closed |
| Dispatch and transport | Catalog links pin the merged shard commit, never a moving branch | Closed |
| State transition | macOS 27 catalog count advances from four to five diffs | Closed |
| Outcome oracle | Source, destination, manifest, entry, and rendered catalog share tree `ce3233a4f0a57953c0e12864b02c4dab3085ff7c` | Closed |

## Expected and observed inventory

Exactly one spec and one catalog entry were added. The measured payload has
7,172 tracked files, 76,302,937 logical bytes, and Git tree
`ce3233a4f0a57953c0e12864b02c4dab3085ff7c`. Release metadata gained exactly
one endpoint: macOS build `26A5406e`, version 27.0 beta 5, released 2026-08-10.

## Negative evidence and stop conditions

The successful generator run alone did not establish catalog publication. The
catalog pass stops on a moving revision, mismatched source or destination tree,
different manifest, missing entrypoint, ambiguous AppleDB record, stale release
registry, or nondeterministic README/catalog output. Absence of any older item
from the bounded latest-diffs list is not deletion; the complete entry remains
in the collapsed version browser and `catalog.json`.

## Bounded conclusion

The post-merge shard-to-catalog stage is closed for this one macOS 27 beta 5
diff. Catalog PR review and merge remain separate owner actions.
