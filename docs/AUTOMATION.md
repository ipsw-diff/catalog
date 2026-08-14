# Automation design

Automation is intentionally downstream of the integrity model. Detection,
generation, catalog publication, and external announcements are separate state
transitions with separate permissions and observable success oracles.

The immutable verifier, remote audit, and mechanical copier are merged. The
copier materializes one explicit spec or an explicit same-snapshot batch into a
clean shard worktree, leaves the exact outputs staged for review, and never
commits, pushes, deletes, or selects a payload.

The frozen legacy census is a separate planning gate. It exhaustively accounts
for the tracked tree at one immutable commit and classifies structurally
ordinary versus blocked payloads, but it does not infer a platform, choose a
shard, generate specs, or authorize a copy.

The shared automation foundation is deliberately read-only. `discover`
validates a reviewed schema-v2 track against a merged immutable activation
anchor, reads
release metadata from the exact AppleDB commit populated by `ipsw`, and matches
each selected release to the active URL, size, and SHA-256 emitted by
`ipsw dl appledb`. It emits either `current` or an ordered queue containing
every consecutive same-major edge after the anchor. Merged manifests supply
the current head of each version train, preventing maintenance releases from
being paired with an overlapping beta train. All ten reviewed shards now run
this read-only detector on staggered schedules.

The reusable generator is a separate write-capable contract. It re-runs exact
discovery, accepts only the first queued edge, verifies both selected IPSWs,
creates an immutable payload source commit and tag, materializes canonical
publication metadata, proves the source and destination trees match, and opens
one ready review pull request. It cannot merge, rewrite the activation anchor,
update the catalog, or announce externally.

## Tracked shards

| Track | Repository | Exact AppleDB selector | Anchor build | Status |
| --- | --- | --- | --- | --- |
| iOS 12 | `ipsw-diff/ios-12` | `os=iOS`, `device=iPhone7,1`, major `12` | `16H88` | Scheduled discovery merged |
| iOS 15 | `ipsw-diff/ios-15` | `os=iOS`, `device=iPod9,1`, major `15` | `19H411` | Scheduled discovery merged |
| iOS 16 | `ipsw-diff/ios-16` | `os=iOS`, `device=iPhone10,3`, major `16` | `20H380` | Scheduled discovery merged |
| iOS 17 | `ipsw-diff/ios-17` | `os=iPadOS`, `device=iPad7,5`, major `17` | `21H440` | Scheduled discovery merged |
| iOS 18 | `ipsw-diff/ios-18` | `os=iOS`, `device=iPhone11,8`, major `18` | `22H340` | Scheduled discovery merged |
| iOS 26 | `ipsw-diff/ios-26` | `os=iOS`, `device=iPhone18,1`, major `26` | `23G82` | Scheduled discovery merged |
| iOS 27 | `ipsw-diff/ios-27` | `os=iOS`, `device=iPhone18,1`, major `27` | `24A5408d` | Scheduled discovery merged |
| macOS 15 | `ipsw-diff/macos-15` | `os=macOS`, `device=Mac16,1`, major `15` | `24F5042g` | Two generated edges merged; automatic ready-PR transport proven |
| macOS 26 | `ipsw-diff/macos-26` | `os=macOS`, `device=Mac17,6`, major `26` | `25G82` | Scheduled discovery merged |
| macOS 27 | `ipsw-diff/macos-27` | `os=macOS`, `device=Mac17,6`, major `27` | `26A5406e` | Scheduled discovery and candidate-generation wiring merged |

The selectors preserve the representative artifacts already cataloged at each
shard terminal. iOS 17 intentionally keeps catalog platform `iOS` while routing
firmware discovery through AppleDB `iPadOS`. The selectors remain explicit
reviewed policy; directory names, build prefixes, and AppleDB result ordering
cannot assign platform or major-version semantics.

## Shard workflow contract

Each shard contains a small caller workflow and a machine-readable track policy.
Callers pin reusable catalog workflows by immutable commit SHA, as recommended
by [GitHub's reusable-workflow documentation][reuse].

The reusable workflow must:

1. Use `ipsw dl appledb` with only the exact AppleDB platform, device, and
   numeric-major prefix in the shard policy, retaining its complete source JSON.
2. Record the exact AppleDB commit populated by that same `ipsw` query and read
   beta, RC, final-release, build, and date metadata only from its Git objects.
3. Match every selected compatible record to exactly one active Apple
   IPSW source with the same URL, size, and SHA-256.
4. Use merged manifests as the heads of independent numeric version trains.
   Continue releases, betas, and RCs within their own train; start a new train
   from the closest earlier final release. Equal-date distinct builds within
   one train are ambiguous and stop.
5. Reject a skipped intermediate build, stale anchor, open automation branch,
   existing payload path, ambiguous AppleDB result, or missing input checksum.
6. Pin and record the `ipsw` version, both IPSW names and SHA-256 hashes, AppleDB
   metadata, workflow run URL, generated tree ID, file count, byte total, and
   modes in a versioned generation manifest.
7. Push a deterministic `generated/TRACK-BUILD` branch and open a pull request;
   never push to `main`, merge, rewrite the anchor, update the catalog, or
   announce from the generation job.
8. Run mutation-tested shard CI over the generated payload and manifest. The
   manifest head advances only in the same reviewed PR as the verified diff.

Top-level permissions will be empty. Read-only detection and expensive
generation are separate jobs; only the publication job receives scoped
`contents: write` and `pull-requests: write`. Concurrency is per track and never
cancels an in-progress diff.

The default `GITHUB_TOKEN` generally suppresses workflows caused by its own
writes. To ensure bot PR validation runs normally, publication should use an
organization GitHub App installed only on shard repositories, not a personal
access token. GitHub documents both the recursion behavior and the GitHub App
alternative in its [workflow-trigger guidance][trigger].

## Catalog transition

A merged shard diff is still not announced. A catalog workflow fetches the
immutable shard merge commit, validates the generation manifest, reruns the
tree/count/bytes/mode oracle, and opens a separate catalog PR containing the new
entry and deterministic indexes. Only that catalog merge represents publication.

The local `reconcile` command is the fail-closed core of that transition. It
accepts only an already-fetched shard repository plus a full merge SHA, derives
missing specs from canonical generated manifests, requires matching provenance
and immutable source tags, and writes only preflighted spec/entry pairs. It does
not fetch, render, commit, push, or open a pull request.

The catalog publication workflow keeps that core behind a reviewed ten-shard
registry. Its read-only job resolves every shard default branch and AppleDB to
full commits, reconciles all shards, and reports only `current` or `candidate`.
Only a candidate starts the separately permissioned publication job. That job
replays the exact resolved commits, regenerates release metadata and indexes,
runs the complete audit, creates one unsigned content-addressed commit, and
opens one ready pull request. It cannot overwrite a generated branch, merge,
or announce. Pull-request-triggered checks created with `GITHUB_TOKEN` still
require manual approval by a repository writer.

## X announcement transition

X delivery will be a third PR and remains disabled until an account and app are
ready. The workflow will run only for newly added IDs in a merged `catalog.json`;
changed or removed entries fail closed. It will use an `x-production` GitHub
environment and the official `POST /2/tweets` endpoint with user-context OAuth.

Duplicate prevention must be durable:

1. Serialize delivery with one non-canceling concurrency group.
2. Atomically create a `refs/tags/announce/x/pending/ID` marker before calling X.
3. If either a pending or sent marker already exists, stop for review.
4. After a successful 201 response, record the Post ID in a GitHub issue ledger,
   create `refs/tags/announce/x/sent/ID`, then remove the pending marker.
5. If the process fails after posting, the pending marker blocks automatic retry
   and therefore blocks accidental duplicate Posts.

The account setup must follow [X's automation requirements][x-guidelines]: label
the account as automated, disclose the bot and operator in its bio, link a
human-managed account, use only the official API, and avoid unsolicited mentions
or engagement automation. Posting requires an approved developer app and an
OAuth 1.0a or OAuth 2.0 PKCE user token; app-only bearer tokens cannot post.

X currently documents pay-per-use pricing, including a higher write price for
content containing a URL. Configure a low spending limit before enabling the
environment and recheck [current pricing][x-pricing] at activation time.

## Activation gates

- Catalog tool and remote audit merged and green.
- Scheduled read-only discovery merged for every reviewed shard.
- macOS 27 candidate dispatch and ready-PR pilot merged, but no hosted candidate
  has exercised the costly path yet.
- The reusable generator passes static and live read-only contract checks.
- A scheduled macOS 15 run generated a second bounded backlog edge, pushed its
  immutable branch and tag, and opened a ready pull request as GitHub Actions.
  The exact branch merged without rewriting, proving automatic PR transport.
- Pull-request workflows created by `GITHUB_TOKEN` remain approval-gated until
  the scoped organization GitHub App is installed; this is separate from the
  now-proven branch and ready-PR transport.
- Organization GitHub App permissions reviewed and installation scoped.
- X account/app policy setup complete; environment secrets and spending cap set.
- A dry-run announcement prints exact JSON and creates no external state.

[reuse]: https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows
[trigger]: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow
[x-guidelines]: https://docs.x.com/developer-guidelines
[x-pricing]: https://docs.x.com/x-api/getting-started/pricing
