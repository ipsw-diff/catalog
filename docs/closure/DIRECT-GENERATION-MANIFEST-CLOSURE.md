# Direct-generation manifest closure

Recorded: 2026-08-13

## Claim and scope

Question: can a firmware diff generated directly in a shard receive the same
canonical manifest as a migrated payload without guessing its Git identity or
creating a circular source commit?

- First lifecycle stage: a reviewed specification names one full immutable
  payload-only source commit.
- Last lifecycle stage: the command re-parses the committed report, measures
  its Git tree, and writes or checks the canonical manifest.
- Supported claim: the emitted manifest is derived from the exact source
  commit by the same model used by staging, recording, and the catalog audit.
- Excluded: downloading firmware, running `ipsw diff`, committing, pushing,
  updating track policy, opening a pull request, or catalog publication.

## Authority and closure matrix

| Stage | Evidence | Status |
| --- | --- | --- |
| Selection and trigger | One explicit reviewed spec and source repository | Closed |
| Inputs and resources | Full source commit, exact payload path, and root report | Closed |
| Transformation | Existing source validator and `MigrationSpec.manifest` produce canonical JSON | Closed |
| Advertisement and options | Explicit output and fail-closed `--check` mode | Closed |
| Dispatch and transport | CLI delegates to one manifest materializer; no Git mutation | Closed |
| State transition | Missing output is created; identical output is idempotent; differing output is rejected | Closed |
| Outcome oracle | Round-trip and mutation tests compare output with the model-derived manifest | Closed |

## Negative evidence and stop conditions

A generated directory in a worktree is not immutable source evidence. The
payload must be committed first, and the spec must name that full commit. A
successful manifest write does not prove that firmware acquisition or diff
generation was complete, nor that a destination PR merged or entered the
catalog. Stop if report facts, source identity, or an existing manifest differ.

## Bounded conclusion

The immutable-payload-to-canonical-manifest stage is closed. The later shard
workflow and catalog publication stages require their own activation and
outcome evidence.
