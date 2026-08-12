# Automation design

Automation is intentionally downstream of the integrity model. Detection,
generation, catalog publication, and external announcements are separate state
transitions with separate permissions and observable success oracles.

The first catalog PR contains the immutable verifier and remote audit. Its
stacked mechanical-copier follow-up adds `stage` and `validate-staged` commands.
They materialize one explicit spec into a clean shard worktree, leave the exact
outputs staged for review, and never commit, push, delete, or select a payload.
No additional legacy payload moves until that follow-up merges with temporary
extraction, reconstructed-tree equality, overwrite refusal, rollback, and
mutation evidence green.

## Planned tracks

| Track | Repository | Exact AppleDB selector | Allowed version | Status |
| --- | --- | --- | --- | --- |
| iOS 27 | `ipsw-diff/ios-27` | `os=iOS`, `device=iPhone18,1` | numeric major exactly `27` | Pilot merged; scheduler not enabled |
| macOS 27 | `ipsw-diff/macos-27` | `os=macOS`, `device=Mac17,6` | numeric major exactly `27` | Repository and pilot still required |

The selectors come from the existing production workflow. They remain explicit
reviewed policy; directory names, build prefixes, and AppleDB result ordering
are not allowed to assign platform or major-version semantics.

## Shard workflow contract

Each shard will contain a small caller workflow and a machine-readable track
policy. It will call a reusable workflow from the catalog at an immutable commit
SHA, as recommended by [GitHub's reusable-workflow documentation][reuse].

The reusable workflow must:

1. Query AppleDB using only the exact platform and device in the shard policy.
2. Parse the returned version and require its numeric major to equal the exact
   allowed major before downloading anything. Manual inputs pass the same gate.
3. Compare only with the last merged baseline from the same track. A first build
   or a new major records no cross-major diff automatically.
4. Reject an already-known build, backward release date, open automation branch,
   existing payload path, ambiguous AppleDB result, or missing input checksum.
5. Pin and record the `ipsw` version, both IPSW names and SHA-256 hashes, AppleDB
   metadata, workflow run URL, generated tree ID, file count, byte total, and
   modes in a versioned generation manifest.
6. Push a deterministic `automation/TRACK/BUILD` branch and open a pull request;
   never push to `main`, merge, advance the baseline, update the catalog, or
   announce from the generation job.
7. Run mutation-tested shard CI over the generated payload and manifest. The
   baseline advances only in the same reviewed PR as the verified diff.

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
- One generated-diff dry run reproduces locally with recorded input hashes.
- `ios-27` branch protection requires verifier CI and review.
- `macos-27` gets its own exact-tree pilot before its scheduler is enabled.
- Organization GitHub App permissions reviewed and installation scoped.
- X account/app policy setup complete; environment secrets and spending cap set.
- A dry-run announcement prints exact JSON and creates no external state.

[reuse]: https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows
[trigger]: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow
[x-guidelines]: https://docs.x.com/developer-guidelines
[x-pricing]: https://docs.x.com/x-api/getting-started/pricing
