# iOS 27 discovery closure

Recorded: 2026-08-11

## Claim and scope

Question: can a read-only reusable workflow take the reviewed `ios-27` track
policy, query AppleDB with exactly that platform, device, and numeric-major
prefix, and deterministically classify the latest result as either the current
baseline or a same-major forward candidate?

- First lifecycle stage: a caller selects the checked-in policy and invokes the
  catalog workflow at an immutable commit.
- Last lifecycle stage: the detector emits one validated JSON decision and an
  observable workflow summary without changing either repository.
- Supported claim: exact-major iOS 27 candidate detection is fail-closed and
  reproducible for the exercised AppleDB result.
- Excluded: scheduling, firmware download, input checksum resolution, diff
  generation, branch or pull-request creation, baseline advancement, catalog
  publication, macOS, and external announcements.

## Authority map

| Property | Authority |
| --- | --- |
| Platform, device, allowed major, and baseline | Reviewed shard track policy |
| Baseline is represented by the track | Merged shard manifests |
| Latest downloadable build metadata | Pinned `ipsw` AppleDB query output |
| Version-major and forward-date decision | Catalog detector |
| Called workflow identity | Immutable caller reference and GitHub reusable-workflow job context |
| Absence of repository mutation | Workflow permissions plus before/after Git state |

## Initial closure matrix

| Stage | Required evidence | Initial status |
| --- | --- | --- |
| Selection and trigger | Manual caller pins the reusable workflow and one policy path | Unresolved |
| Inputs and resources | Strict policy, manifest-backed baseline, pinned `ipsw`, and one AppleDB object | Unresolved |
| Transformation | Exact platform and numeric-major validation plus forward comparison | Unresolved |
| Advertisement and options | Caller exposes no OS, device, major, build, or mutation overrides | Unresolved |
| Dispatch and transport | Exact policy selector reaches `ipsw` as separate arguments | Unresolved |
| State transition | One deterministic `current` or `candidate` decision is emitted | Unresolved |
| Outcome oracle | Fixture mutations and a live current-baseline run agree without repository changes | Unresolved |

## Negative-evidence audit

A successful AppleDB command does not prove it used the intended selector, and
an empty repository diff does not prove the result was parsed or classified.
The command arguments, strict result schema, decision JSON, and before/after Git
state must each be checked. A current result proves only detection; it provides
no evidence for generation or publication.

## Current closure matrix

| Stage | Evidence | Current status |
| --- | --- | --- |
| Selection and trigger | `ios-27` PR #2 pins the reusable workflow to `05d2db3e4a2e9af1f3f1b8dec58f93cb85bef8c3` and selects only `track.json` plus `manifests` | Closed |
| Inputs and resources | Strict iOS 27 policy, terminal manifest build, `ipsw` v3.1.707 archive digest, and exact AppleDB object | Closed |
| Transformation | Tests cover current, same-major candidate, wrong major, non-forward date, stale baseline, and ambiguous JSON | Closed |
| Advertisement and options | Detector CLI and shard caller expose no OS, device, major, build, generation, or mutation override | Closed |
| Dispatch and transport | A fake executable asserts all ten `ipsw` arguments, including `--version 27.`; the live query used the same selector | Closed |
| State transition | Canonical decision JSON has exactly `current` or `candidate` status | Closed |
| Outcome oracle | Local and GitHub-hosted run `31562156307` both emitted the same canonical `current` decision and left both worktrees clean | Closed |

## Expected versus observed inventory

| Property | Expected | Observed |
| --- | ---: | ---: |
| Track policies selected | 1 | 1 |
| Terminal manifest builds | 1 | 1 |
| AppleDB result objects | 1 | 1 |
| Decision states | 2 | 2 |
| GitHub-hosted caller runs | 1 | 1 |
| Repository paths modified by live detection | 0 | 0 |

## Verification and mutation evidence

- The pinned `ipsw` v3.1.707 Linux x86-64 archive matched SHA-256
  `002113c7b9eaf4d06d5bb77dcbeb809f9b942ff18ba9fe906f3a8d2aab12df00`
  and contained the expected `ipsw` executable.
- Thirteen focused tests exercise both decision states and reject selector,
  platform, major, date, baseline-chain, and JSON-shape mutations.
- A live query for `os=iOS`, `device=iPhone18,1` returned build `24A5408d` and
  the detector emitted canonical `status=current` without changing either
  repository.
- The `ios-27` pull-request run
  [`31562156307`](https://github.com/ipsw-diff/ios-27/actions/runs/31562156307/job/94006526321)
  resolved the reusable workflow to the pinned catalog commit, verified the
  `ipsw` archive and version on Ubuntu 24.04, used a read-only token, and emitted
  the same canonical `current` decision before proving both checked-out
  repositories remained clean.

## Remaining activation conditions

- No success-critical row in the scoped read-only behavior remains unresolved.
- Catalog PR #4 and `ios-27` PR #2 must merge before manual default-branch
  dispatch is available. Scheduling, generation, and publication retain their
  separate activation gates.

## Stop conditions

Do not call discovery ready if the workflow reference is mutable, the policy
baseline is not backed by a merged manifest, the AppleDB shape is ambiguous,
the OS or numeric major differs, a backward release is accepted, fixture
mutation survives, or either repository changes during the live run.

## Bounded conclusion

The read-only detector is closed from immutable caller selection through its
GitHub-hosted decision output. This establishes the scoped behavior on the
review branches, not default-branch activation. Nothing in this audit authorizes
scheduling, generation, or publication.
