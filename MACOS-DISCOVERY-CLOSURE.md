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

## Bounded conclusion

Every success-critical row remains unresolved until implementation, mutation
tests, live local evidence, and the pinned hosted caller close it. Nothing in
this audit authorizes scheduling, generation, publication, or announcement.
