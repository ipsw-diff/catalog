from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from ipsw_diff_catalog.model import CatalogError, JsonObject, MigrationSpec, canonical_json
from ipsw_diff_catalog.reconcile import reconcile
from ipsw_diff_catalog.verify import validate_source
from tests.helpers import commit_all, git, init_repo

if TYPE_CHECKING:
    from pathlib import Path

    from ipsw_diff_catalog.model import TreeInventory


@dataclass(frozen=True)
class GeneratedShard:
    repo: Path
    spec: MigrationSpec
    source_commit: str
    destination_commit: str
    inventory: TreeInventory


def _provenance(spec: MigrationSpec) -> JsonObject:
    return {
        "schema_version": 1,
        "catalog_commit": "c" * 40,
        "source_commit": spec.source.commit,
        "source_tag": f"payload/{spec.source.path}",
        "workflow_run": f"{spec.source.repository}/actions/runs/1234",
        "workflow_commit": "d" * 40,
        "generator": {"name": "ipsw", "version": "Version: test"},
        "signatures": {
            "repository": "https://github.com/example/signatures",
            "commit": "e" * 40,
        },
        "discovery": {},
        "inputs": [],
    }


@pytest.fixture
def generated_shard(tmp_path: Path) -> GeneratedShard:
    repo = tmp_path / "shard"
    init_repo(repo)
    repository = "https://github.com/example/ios-1"
    git(repo, "remote", "add", "origin", f"{repository}.git")

    payload = repo / "source-diff"
    payload.mkdir()
    (payload / "README.md").write_text(
        "# 1.0 (A1) .vs 1.1 (A2)\n\n"
        "## Inputs\n\n"
        "- `Device1,1_1.0_A1_Restore.ipsw`\n"
        "- `Device1,1_1.1_A2_Restore.ipsw`\n",
        encoding="utf-8",
    )
    (payload / "data.md").write_text("payload\n", encoding="utf-8")
    source_commit = commit_all(repo, "source payload")

    spec = MigrationSpec.from_object(
        {
            "schema_version": 1,
            "id": "ios-1.1-a1-a2",
            "platform": "iOS",
            "major_version": 1,
            "device": "Device1,1",
            "from": {
                "version": "1.0",
                "build": "A1",
                "input": "Device1,1_1.0_A1_Restore.ipsw",
            },
            "to": {
                "version": "1.1",
                "build": "A2",
                "input": "Device1,1_1.1_A2_Restore.ipsw",
            },
            "source": {
                "repository": repository,
                "commit": source_commit,
                "path": "source-diff",
            },
            "destination": {
                "repository": repository,
                "payload_path": "diffs/source-diff",
                "manifest_path": "manifests/source-diff.json",
            },
        }
    )
    inventory = validate_source(spec, repo)
    git(repo, "tag", f"payload/{spec.source.path}", source_commit)

    (repo / "diffs").mkdir()
    payload.rename(repo / spec.destination.payload_path)
    manifest = repo / spec.destination.manifest_path
    manifest.parent.mkdir()
    manifest.write_text(canonical_json(spec.manifest(inventory)), encoding="utf-8")
    provenance = repo / "provenance" / f"{spec.source.path}.json"
    provenance.parent.mkdir()
    provenance.write_text(canonical_json(_provenance(spec)), encoding="utf-8")
    destination_commit = commit_all(repo, "publish payload")

    return GeneratedShard(
        repo=repo,
        spec=spec,
        source_commit=source_commit,
        destination_commit=destination_commit,
        inventory=inventory,
    )


def test_reconcile_writes_verified_spec_and_entry(
    generated_shard: GeneratedShard,
    tmp_path: Path,
) -> None:
    specs = tmp_path / "specs"
    entries = tmp_path / "entries"

    result = reconcile(
        generated_shard.repo,
        generated_shard.destination_commit,
        specs,
        entries,
    )

    assert result.destination_commit == generated_shard.destination_commit
    assert result.manifest_count == 1
    assert result.recorded_count == 0
    assert result.reconciled_count == 1
    assert (specs / f"{generated_shard.spec.identifier}.json").read_text(
        encoding="utf-8"
    ) == canonical_json(generated_shard.spec.to_object())
    assert (entries / f"{generated_shard.spec.identifier}.json").read_text(
        encoding="utf-8"
    ) == canonical_json(
        generated_shard.spec.catalog_entry(
            generated_shard.inventory,
            generated_shard.destination_commit,
        )
    )


def test_reconcile_is_a_no_op_for_recorded_manifest(
    generated_shard: GeneratedShard,
    tmp_path: Path,
) -> None:
    specs = tmp_path / "specs"
    entries = tmp_path / "entries"
    reconcile(generated_shard.repo, generated_shard.destination_commit, specs, entries)

    result = reconcile(
        generated_shard.repo,
        generated_shard.destination_commit,
        specs,
        entries,
    )

    assert result.manifest_count == 1
    assert result.recorded_count == 1
    assert result.reconciled_count == 0


def test_reconcile_does_not_rederive_recorded_legacy_manifest(
    generated_shard: GeneratedShard,
    tmp_path: Path,
) -> None:
    specs = tmp_path / "specs"
    entries = tmp_path / "entries"
    reconcile(generated_shard.repo, generated_shard.destination_commit, specs, entries)
    manifest = generated_shard.repo / generated_shard.spec.destination.manifest_path
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["source"]["repository"] = "https://github.com/example/legacy-source"
    manifest.write_text(canonical_json(value), encoding="utf-8")
    destination_commit = commit_all(generated_shard.repo, "legacy source route")

    result = reconcile(generated_shard.repo, destination_commit, specs, entries)

    assert result.recorded_count == 1
    assert result.reconciled_count == 0


def test_reconcile_classifies_recorded_nested_manifest(
    generated_shard: GeneratedShard,
    tmp_path: Path,
) -> None:
    specs = tmp_path / "specs"
    entries = tmp_path / "entries"
    reconcile(generated_shard.repo, generated_shard.destination_commit, specs, entries)
    old_path = generated_shard.spec.destination.manifest_path
    nested_path = f"manifests/{generated_shard.spec.device}/{generated_shard.spec.source.path}.json"
    (generated_shard.repo / "manifests" / generated_shard.spec.device).mkdir()
    git(generated_shard.repo, "mv", old_path, nested_path)
    destination_commit = commit_all(generated_shard.repo, "nest recorded manifest")

    result = reconcile(generated_shard.repo, destination_commit, specs, entries)

    assert result.manifest_count == 1
    assert result.recorded_count == 1
    assert result.reconciled_count == 0


def test_reconcile_rejects_abbreviated_destination_revision(
    generated_shard: GeneratedShard,
    tmp_path: Path,
) -> None:
    with pytest.raises(CatalogError, match="full lowercase SHA-1"):
        reconcile(
            generated_shard.repo,
            generated_shard.destination_commit[:12],
            tmp_path / "specs",
            tmp_path / "entries",
        )


def test_reconcile_rejects_mutated_provenance_before_writing(
    generated_shard: GeneratedShard,
    tmp_path: Path,
) -> None:
    path = generated_shard.repo / "provenance" / f"{generated_shard.spec.source.path}.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    value["source_commit"] = "f" * 40
    path.write_text(canonical_json(value), encoding="utf-8")
    destination_commit = commit_all(generated_shard.repo, "mutate provenance")
    specs = tmp_path / "specs"
    entries = tmp_path / "entries"

    with pytest.raises(CatalogError, match="source_commit differs"):
        reconcile(generated_shard.repo, destination_commit, specs, entries)

    assert not specs.exists()
    assert not entries.exists()


def test_reconcile_rejects_boolean_provenance_schema(
    generated_shard: GeneratedShard,
    tmp_path: Path,
) -> None:
    path = generated_shard.repo / "provenance" / f"{generated_shard.spec.source.path}.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    value["schema_version"] = True
    path.write_text(canonical_json(value), encoding="utf-8")
    destination_commit = commit_all(generated_shard.repo, "mutate schema")

    with pytest.raises(CatalogError, match="schema_version must be 1"):
        reconcile(
            generated_shard.repo,
            destination_commit,
            tmp_path / "specs",
            tmp_path / "entries",
        )


def test_reconcile_rejects_missing_source_tag(
    generated_shard: GeneratedShard,
    tmp_path: Path,
) -> None:
    git(generated_shard.repo, "tag", "--delete", f"payload/{generated_shard.spec.source.path}")

    with pytest.raises(CatalogError, match="git command failed"):
        reconcile(
            generated_shard.repo,
            generated_shard.destination_commit,
            tmp_path / "specs",
            tmp_path / "entries",
        )


def test_reconcile_rejects_origin_mismatch(
    generated_shard: GeneratedShard,
    tmp_path: Path,
) -> None:
    git(
        generated_shard.repo,
        "remote",
        "set-url",
        "origin",
        "https://github.com/example/not-the-shard.git",
    )

    with pytest.raises(CatalogError, match="origin differs"):
        reconcile(
            generated_shard.repo,
            generated_shard.destination_commit,
            tmp_path / "specs",
            tmp_path / "entries",
        )


def test_reconcile_rejects_payload_mutation(
    generated_shard: GeneratedShard,
    tmp_path: Path,
) -> None:
    payload = generated_shard.repo / generated_shard.spec.destination.payload_path / "data.md"
    payload.write_text("mutated\n", encoding="utf-8")
    destination_commit = commit_all(generated_shard.repo, "mutate payload")

    with pytest.raises(CatalogError, match="payload inventory mismatch"):
        reconcile(
            generated_shard.repo,
            destination_commit,
            tmp_path / "specs",
            tmp_path / "entries",
        )


def test_reconcile_preflights_output_collision_before_writing(
    generated_shard: GeneratedShard,
    tmp_path: Path,
) -> None:
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / f"{generated_shard.spec.identifier}.json").write_text(
        "different\n",
        encoding="utf-8",
    )
    entries = tmp_path / "entries"

    with pytest.raises(CatalogError, match="refusing to overwrite differing output"):
        reconcile(
            generated_shard.repo,
            generated_shard.destination_commit,
            specs,
            entries,
        )

    assert not entries.exists()
