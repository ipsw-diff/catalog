#!/usr/bin/env bash
set -euo pipefail
shopt -s inherit_errexit

if [[ $# -ne 3 ]]; then
  echo "usage: $0 REGISTRY INVENTORY SHARD_ROOT" >&2
  exit 2
fi

registry=$1
inventory=$2
shard_root=$3

if [[ ! -d entries || ! -d specs ]]; then
  echo "reconciliation must run from the catalog root" >&2
  exit 1
fi

fetch_blob_oids() {
  local repository_path=$1
  local object_ids=$2
  if [[ -z "$object_ids" ]]; then
    return
  fi
  printf '%s\n' "$object_ids" | sort --unique | git -C "$repository_path" \
    -c fetch.negotiationAlgorithm=noop fetch \
    --quiet origin \
    --no-tags \
    --no-write-fetch-head \
    --recurse-submodules=no \
    --filter=blob:none \
    --stdin
}

jq --exit-status '
  type == "object" and
  (keys | sort) == ["schema_version", "shards"] and
  .schema_version == 1 and
  (.shards | type == "array" and length == 10) and
  all(.shards[];
    type == "object" and
    (keys | sort) == ["branch", "id", "repository"] and
    (.id | test("^(ios|macos)-(12|15|16|17|18|26|27)$")) and
    .repository == ("https://github.com/ipsw-diffs/" + .id) and
    .branch == "main") and
  ([.shards[].id] | sort) == [
    "ios-12", "ios-15", "ios-16", "ios-17", "ios-18", "ios-26", "ios-27",
    "macos-15", "macos-26", "macos-27"
  ] and
  ([.shards[].repository] | unique | length) == 10
' "$registry" >/dev/null

jq --exit-status --slurpfile registry "$registry" '
  type == "array" and
  length == 10 and
  all(.[];
    type == "object" and
    (keys | sort) == ["branch", "commit", "id", "repository"] and
    (.commit | test("^[0-9a-f]{40}$"))) and
  map({branch, id, repository}) ==
    ($registry[0].shards | map({branch, id, repository})) and
  ([.[].commit] | length) == 10
' "$inventory" >/dev/null

if [[ -e "$shard_root" ]]; then
  echo "shard root already exists: $shard_root" >&2
  exit 1
fi
mkdir -p "$shard_root"

while IFS=$'\t' read -r id repository branch commit; do
  target="$shard_root/$id"
  git init --quiet --object-format=sha1 "$target"
  git -C "$target" remote add origin "$repository"
  git -C "$target" config remote.origin.promisor true
  git -C "$target" config remote.origin.partialCloneFilter blob:none
  git -C "$target" -c protocol.version=2 fetch \
    --quiet --no-tags --depth=1 --filter=blob:none origin "$commit"
  observed=$(git -C "$target" rev-parse FETCH_HEAD)
  if [[ "$observed" != "$commit" ]]; then
    echo "$id resolved to $observed instead of $commit" >&2
    exit 1
  fi
  if git -C "$target" ls-remote --exit-code --tags origin \
    'refs/tags/payload/*' >/dev/null 2>&1; then
    git -C "$target" -c protocol.version=2 fetch \
      --quiet --no-tags --filter=blob:none origin \
      'refs/tags/payload/*:refs/tags/payload/*'
  fi

  manifest_oids=$(git -C "$target" ls-tree -r "$commit" -- manifests | \
    awk '$2 == "blob" {print $3}')
  fetch_blob_oids "$target" "$manifest_oids"

  payload_oids=$(
    while IFS= read -r -d '' manifest_path; do
      manifest=$(git -C "$target" show "$commit:$manifest_path")
      identifier=$(jq --exit-status --raw-output '.id | strings | select(length > 0)' \
        <<< "$manifest")
      if [[ ! -f "entries/$identifier.json" ]]; then
        source_commit=$(jq --exit-status --raw-output '.source.commit' <<< "$manifest")
        source_path=$(jq --exit-status --raw-output '.source.path' <<< "$manifest")
        destination_path=$(jq --exit-status --raw-output '.payload.path' <<< "$manifest")
        [[ "$source_commit" =~ ^[0-9a-f]{40}$ ]]
        git -C "$target" ls-tree -r "$source_commit" -- "$source_path" | \
          awk '$2 == "blob" {print $3}'
        git -C "$target" ls-tree -r "$commit" -- "$destination_path" | \
          awk '$2 == "blob" {print $3}'
      fi
    done < <(git -C "$target" ls-tree -r -z --name-only "$commit" -- manifests)
  )
  fetch_blob_oids "$target" "$payload_oids"

  uv run ipsw-diff-catalog reconcile \
    --shard-repo "$target" \
    --destination-revision "$commit" \
    --specs-dir specs \
    --entries-dir entries
  printf 'reconciled %s %s at %s\n' "$id" "$branch" "$commit"
done < <(jq --raw-output '.[] | [.id, .repository, .branch, .commit] | @tsv' "$inventory")
