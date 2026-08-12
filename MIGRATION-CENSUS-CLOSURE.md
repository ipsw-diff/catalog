# Bulk migration census closure

Recorded: 2026-08-12

## Claim and scope

Question: can a read-only command freeze one immutable legacy commit, classify
every tracked path under an explicit source-layout policy, validate the two
known ordinary README input-section labels without weakening their exact
two-IPSW contract, and emit a canonical census in which every selected payload
is either structurally migratable or blocked with an observable reason?

- First lifecycle stage: a caller supplies the exact legacy repository, full
  source commit, and reviewed source-layout policy.
- Last lifecycle stage: the command emits canonical census JSON and proves its
  tracked-file coverage is disjoint and exhaustive for that commit.
- Supported claim: the census is a deterministic planning input; it does not
  itself authorize a semantic route or copy a payload.
- Excluded: choosing platform, device, or destination repositories; generating
  migration specs; staging or committing payloads; creating repositories or
  pull requests; deleting legacy data; and enabling generation, scheduling,
  publication, or announcements.

## Authority map

| Property | Authority |
| --- | --- |
| Frozen source state | Full legacy Git commit supplied by the caller |
| Tracked namespaces and files | Git tree at that immutable commit |
| Payload roots and explicit exclusions | Reviewed source-layout policy |
| Versions, builds, and input artifacts | Exact source README structure and content |
| Tree, file-count, byte, and mode facts | Git object inventory |
| Migratable versus blocked status | Census parser with explicit reason codes |
| Semantic shard route | Excluded; later reviewed migration specs |

## Initial closure matrix

| Stage | Required evidence | Initial status |
| --- | --- | --- |
| Selection and trigger | Full source commit plus exact payload-root and exclusion policy | Unresolved |
| Inputs and resources | Every policy path resolves to tracked Git objects at that commit | Unresolved |
| Transformation | Known README variants normalize to the same exact two-IPSW record | Unresolved |
| Advertisement and options | CLI exposes no semantic inference, staging, commit, push, or deletion switches | Unresolved |
| Dispatch and transport | Canonical JSON contains every payload once and no excluded file | Unresolved |
| State transition | Source tree remains unchanged and output changes only when source or policy changes | Unresolved |
| Outcome oracle | Classified plus excluded tracked-file counts equal the immutable source total exactly | Unresolved |

## Negative-evidence audit

A directory name containing `vs` does not establish that it is a valid firmware
diff, and a README title does not establish platform or destination routing.
Absence of a README cannot be repaired from the path. A redirect, OTA/RSR
comparison, or non-IPSW input is a blocked row until a later schema explicitly
models it. A successful parse proves only census eligibility, not migration
readiness.

## Stop conditions

Do not call the census closed if any tracked file is unclassified or classified
twice, an exclusion overlaps a payload, a policy root is absent, either known
README label can bypass the exact two-IPSW check, malformed or missing metadata
is silently inferred, output depends on worktree state, or the source worktree
changes.

## Initial bounded conclusion

Every success-critical row remains unresolved until implementation, mutation
tests, a real frozen-source run, and exact tracked-file reconciliation close it.
Nothing in this artifact authorizes copying or publishing legacy payloads.

## Current closure matrix

| Stage | Evidence | Current status |
| --- | --- | --- |
| Selection and trigger | Policy pins legacy commit `d881e84676308404c6947d0218c11f347a6f3a89`, its expected GitHub origin, 156 exact payload roots, two excluded roots, and three excluded files | Closed |
| Inputs and resources | Every policy root resolves at root tree `77410c1e00105cfa2a8ec906078a298da205b825`; every excluded file resolves to one blob | Closed |
| Transformation | One parser enforces the same exact title and two-IPSW contract for 104 `## IPSWs` and 37 `## Inputs` rows; all other structures are blocked | Closed |
| Advertisement and options | `census` accepts only policy, source repository, output, and check mode; it exposes no routing, staging, commit, push, deletion, or inference option | Closed |
| Dispatch and transport | Canonical JSON contains each of the 156 policy payload roots once plus the five exact exclusions and no other namespace | Closed |
| State transition | Generation and check mode read only immutable Git objects; tests prove dirty tracked and untracked worktree state is preserved and ignored | Closed |
| Outcome oracle | 247,115 payload files plus 8 excluded files equal all 247,123 tracked files; 8,475,631,754 plus 55,738 logical bytes equal all 8,475,687,492 bytes | Closed |

## Real census inventory

| Property | Observed |
| --- | ---: |
| Payload roots | 156 |
| Ordinary two-IPSW payloads | 141 |
| Blocked payloads | 15 |
| Missing README blockers | 12 |
| Redirect blockers | 1 |
| Non-IPSW input blockers | 1 |
| Unsupported README blockers | 1 |
| Tracked payload files | 247,115 |
| Explicitly excluded files | 8 |
| Total tracked files | 247,123 |
| Total logical bytes | 8,475,687,492 |

The independent root-tree inventory returned the same tree, file count, and
logical byte total as the generated census. The source-layout policy SHA-256 is
`365a073c4839ff74c71851d01b0c3249b564f656f7ded09686b73190b6f55f77`; the
canonical census SHA-256 is
`c77cdef51847e7d479c39d94562a4ccff15babbb922932c71470d861b2eb8ce5`.

## Verification and mutation evidence

- `census --check` regenerated the real result from the frozen commit and
  matched the checked-in census byte for byte.
- Tests reject an unclassified tracked file, an overlapping path policy, an
  absent policy root, changed or non-UTF-8 generated output, and output inside
  the source repository.
- Tests prove a dirty source worktree is neither consulted nor changed.
- README tests accept both known ordinary headings and reject mixed or duplicate
  headings, extra section content, title/input disagreement, and non-IPSW input
  artifacts.
- Atomic generation writes a normal non-executable `0644` output file.
- Formatting, lint, type checking, and all 61 tests passed.

## Bounded conclusion

The scoped census is closed as a deterministic migration-planning input. It
accounts for every tracked file at the frozen legacy commit and identifies 141
structurally ordinary payloads plus 15 explicit blockers. It does not establish
platform, device, route, copy readiness, destination capacity, or publication
readiness for any row.
