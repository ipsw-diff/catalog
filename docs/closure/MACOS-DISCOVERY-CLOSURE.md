# macOS 27 discovery closure

Recorded: 2026-08-11

## Claim and scope

Question: can the existing read-only discovery path admit exactly the reviewed
`macos-27` track alongside `ios-27`, query AppleDB with the macOS policy's
platform, device, and numeric-major prefix, and classify the latest result
without weakening the established iOS gates or changing either repository?

- First lifecycle stage: a macOS shard caller selects its checked-in policy and
  invokes the catalog workflow at an immutable commit.
- Last lifecycle stage: the detector emits one validated `current` or
  `candidate` decision plus a platform-aware workflow summary while both
  checked-out repositories remain unchanged.
- Supported claim: exact-major macOS 27 candidate detection uses the same
  fail-closed lifecycle as the existing iOS 27 track.
- Excluded: other platforms or majors, scheduling, firmware download, checksum
  resolution, diff generation, branch or pull-request creation, baseline
  advancement, catalog auto-publication, and external announcements.

## Authority map

| Property | Authority |
| --- | --- |
| Supported track identities | Explicit detector allowlist |
| Platform, device, major, and baseline | Reviewed shard track policy |
| Baseline is represented by the track | Merged shard manifests |
| Latest downloadable build metadata | Pinned `ipsw` AppleDB query output |
| Forward candidate decision | Catalog detector |
| Called workflow identity | Immutable caller reference and reusable-workflow job context |
| Absence of repository mutation | Workflow permissions plus final Git-state oracle |

## Initial closure matrix

| Stage | Required evidence | Initial status |
| --- | --- | --- |
| Selection and trigger | macOS caller pins one catalog commit and selects only `track.json` plus `manifests` | Unresolved |
| Inputs and resources | Strict macOS policy, manifest-backed beta 4 baseline, pinned `ipsw`, and one AppleDB object | Unresolved |
| Transformation | Exact track allowlist, platform/major validation, and forward comparison preserve iOS behavior | Unresolved |
| Advertisement and options | Caller exposes no platform, device, major, build, or mutation overrides | Unresolved |
| Dispatch and transport | Exact macOS policy values reach `ipsw` as ten separate arguments | Unresolved |
| State transition | One deterministic `current` or `candidate` decision and platform-aware summary are emitted | Unresolved |
| Outcome oracle | Mutation tests and a hosted macOS candidate run agree while both repositories remain clean | Unresolved |

## Negative-evidence audit

An iOS success does not prove macOS is reachable, and accepting a policy-shaped
object does not prove its identity, platform, and major form one supported
track. A successful AppleDB query does not prove exact selector dispatch. A
candidate result proves only read-only detection; it is not evidence that the
candidate can be downloaded, generated, published, or announced.

## Stop conditions

Do not call macOS discovery ready if unsupported track combinations parse,
removing either supported-track allowlist row leaves tests green, the macOS
manifest terminal differs from the policy baseline, selector arguments differ,
the existing iOS oracle regresses, the workflow reference is mutable, the
hosted result is not canonical, or either checkout changes.

## Initial bounded conclusion

Every success-critical row remains unresolved until implementation, mutation
tests, live local evidence, and the pinned hosted caller close it. Nothing in
this audit authorizes scheduling, generation, publication, or announcement.

## Current closure matrix

| Stage | Evidence | Current status |
| --- | --- | --- |
| Selection and trigger | `macos-27` PR #2 commit `58147844d38a054e242a30eeaabbe7023eb8a3e2` pins catalog commit `0fcdb7ea63f0cab3d2ccfc117ee530fcc697b2b6` and selects only `track.json` plus `manifests` | Closed |
| Inputs and resources | Strict macOS 27 policy, terminal beta 4 manifest build `26A5388g`, pinned `ipsw` v3.1.707 archive, and one exact AppleDB object | Closed |
| Transformation | The two-row allowlist and 19 focused tests preserve iOS behavior, accept macOS, and reject mismatched identity/platform/major tuples | Closed |
| Advertisement and options | The caller exposes no platform, device, major, build, generation, publication, or mutation override | Closed |
| Dispatch and transport | A fake executable asserts all ten macOS `ipsw` arguments; local and hosted queries used the reviewed selector | Closed |
| State transition | Local and hosted runs emitted the same canonical `candidate` decision and the hosted platform-aware summary passed | Closed |
| Outcome oracle | GitHub-hosted run `31565338497` passed with `contents: read` and proved both checked-out repositories remained clean | Closed |

## Expected versus observed inventory

| Property | Expected | Observed |
| --- | ---: | ---: |
| Explicitly supported track tuples | 2 | 2 |
| macOS policies selected by the caller | 1 | 1 |
| Terminal macOS manifest builds | 1 | 1 |
| AppleDB result objects per run | 1 | 1 |
| Detector decision states covered by tests | 2 | 2 |
| GitHub-hosted macOS caller runs | 1 | 1 |
| Repository paths modified by hosted detection | 0 | 0 |

## Verification and mutation evidence

- Nineteen focused discovery tests and all 50 catalog tests pass. Removing
  either allowlist row or accepting an iOS/macOS identity-platform mismatch
  breaks the focused suite.
- The local live query for `os=macOS`, `device=Mac17,6`, and `version=27.`
  emitted canonical `status=candidate` JSON from beta 4 build `26A5388g` to
  beta 5 build `26A5406e`.
- The pinned `ipsw` v3.1.707 Linux x86-64 archive matched SHA-256
  `002113c7b9eaf4d06d5bb77dcbeb809f9b942ff18ba9fe906f3a8d2aab12df00`.
- The `macos-27` pull-request run
  [`31565338497`](https://github.com/ipsw-diff/macos-27/actions/runs/31565338497/job/94015893113)
  resolved the reusable workflow to the immutable catalog commit, used only
  `contents: read`, emitted the expected candidate, generated the macOS 27
  summary, and passed the final clean-worktree oracle.
- The full catalog quality gates and the two-entry remote integrity audit pass.
  `actionlint` has only its pre-existing schema gaps for GitHub's
  `job.workflow_repository` and `job.workflow_sha` reusable-workflow context;
  the hosted run exercises both successfully.

## Remaining activation conditions

- Merge catalog PR #6, repin the macOS caller to a commit reachable from the
  catalog default branch, and rerun the hosted oracle before merging caller
  PR #2.
- Scheduling, generation, publication, and announcement remain separately
  disabled and outside this closure claim.

## Bounded conclusion

The scoped read-only behavior is closed on the review branches from immutable
macOS caller selection through canonical hosted candidate output and the final
clean-worktree oracle. Default-branch activation remains pending the two merges
and caller repin above. This does not establish readiness for firmware download,
diff generation, publication, scheduling, or announcement.
