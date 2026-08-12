from __future__ import annotations

import copy
import json
import shutil
from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

from ipsw_diff_catalog.model import CatalogError, MigrationSpec
from ipsw_diff_catalog.stage import stage_batch, validate_staged_batch
from tests.helpers import commit_all, git

if TYPE_CHECKING:
    from pathlib import Path

    from tests.helpers import Repositories

EXPECTED_PAYLOAD_COUNT = 2
EXPECTED_TRACKED_FILE_COUNT = 5
EXPECTED_STAGED_PATH_COUNT = 7


def _batch_specs(repositories: Repositories) -> tuple[MigrationSpec, MigrationSpec]:
    second_payload = repositories.source / "source-diff-2"
    second_payload.mkdir()
    (second_payload / "README.md").write_text(
        "# 1.1 (B1) .vs 1.2 (B2)\n\n"
        "## IPSWs\n\n"
        "- `Device1,1_1.1_B1_Restore.ipsw`\n"
        "- `Device1,1_1.2_B2_Restore.ipsw`\n\n"
        "## Data\n",
        encoding="utf-8",
    )
    (second_payload / "payload.md").write_text("second payload\n", encoding="utf-8")
    source_commit = commit_all(repositories.source, "second source payload")

    first_object = json.loads(repositories.spec_path.read_text(encoding="utf-8"))
    first_object["source"]["commit"] = source_commit
    second_object = copy.deepcopy(first_object)
    second_object["id"] = "ios-1.1-b1-b2"
    second_object["from"] = {
        "version": "1.1",
        "build": "B1",
        "input": "Device1,1_1.1_B1_Restore.ipsw",
    }
    second_object["to"] = {
        "version": "1.2",
        "build": "B2",
        "input": "Device1,1_1.2_B2_Restore.ipsw",
    }
    second_object["source"]["path"] = "source-diff-2"
    second_object["destination"]["payload_path"] = "diffs/source-diff-2"
    second_object["destination"]["manifest_path"] = "manifests/source-diff-2.json"
    return (
        MigrationSpec.from_object(first_object),
        MigrationSpec.from_object(second_object),
    )


def _assert_clean(repositories: Repositories) -> None:
    assert git(repositories.destination, "status", "--porcelain=v1", "--untracked-files=all") == ""


def _assert_batch_targets_absent(
    repositories: Repositories,
    specs: tuple[MigrationSpec, ...],
) -> None:
    for spec in specs:
        assert not (repositories.destination / spec.destination.payload_path).exists()
        assert not (repositories.destination / spec.destination.manifest_path).exists()


def test_stage_batch_stages_and_revalidates_one_atomic_tree(
    repositories: Repositories,
) -> None:
    first, second = _batch_specs(repositories)
    result = stage_batch(
        (second, first),
        repositories.source,
        repositories.destination,
        repositories.destination_base,
    )

    assert result.base_commit == repositories.destination_base
    assert result.staged_tree == git(repositories.destination, "write-tree")
    assert len(result.payloads) == EXPECTED_PAYLOAD_COUNT
    assert result.tracked_file_count == EXPECTED_TRACKED_FILE_COUNT
    assert result.staged_path_count == EXPECTED_STAGED_PATH_COUNT
    assert [payload.identifier for payload in result.payloads] == [
        first.identifier,
        second.identifier,
    ]
    assert (
        validate_staged_batch(
            (first, second),
            repositories.source,
            repositories.destination,
            repositories.destination_base,
        )
        == result
    )
    assert sorted(
        git(repositories.destination, "diff", "--cached", "--name-only").splitlines()
    ) == [
        "diffs/source-diff-2/README.md",
        "diffs/source-diff-2/payload.md",
        "diffs/source-diff/README.md",
        "diffs/source-diff/nested/payload.md",
        "diffs/source-diff/tool",
        "manifests/source-diff-2.json",
        "manifests/source-diff.json",
    ]


@pytest.mark.parametrize("count", [0, 1])
def test_stage_batch_requires_multiple_specs(
    repositories: Repositories,
    count: int,
) -> None:
    specs = _batch_specs(repositories)[:count]
    with pytest.raises(CatalogError, match="requires at least 2 specs"):
        stage_batch(
            specs,
            repositories.source,
            repositories.destination,
            repositories.destination_base,
        )
    _assert_clean(repositories)


def test_stage_batch_rejects_duplicate_specs(repositories: Repositories) -> None:
    first, _second = _batch_specs(repositories)
    with pytest.raises(CatalogError, match="unique ids"):
        stage_batch(
            (first, first),
            repositories.source,
            repositories.destination,
            repositories.destination_base,
        )
    _assert_clean(repositories)


def test_stage_batch_rejects_duplicate_source_paths(repositories: Repositories) -> None:
    first, second = _batch_specs(repositories)
    duplicate_source = replace(
        second,
        source=replace(second.source, path=first.source.path),
    )
    with pytest.raises(CatalogError, match="unique source paths"):
        stage_batch(
            (first, duplicate_source),
            repositories.source,
            repositories.destination,
            repositories.destination_base,
        )
    _assert_clean(repositories)


def test_stage_batch_rejects_different_source_repositories(
    repositories: Repositories,
) -> None:
    first, second = _batch_specs(repositories)
    mismatched = replace(
        second,
        source=replace(
            second.source,
            repository="https://github.com/example/other-source",
        ),
    )
    with pytest.raises(CatalogError, match="share one source repository"):
        stage_batch(
            (first, mismatched),
            repositories.source,
            repositories.destination,
            repositories.destination_base,
        )
    _assert_clean(repositories)


def test_stage_batch_rejects_different_source_commits(repositories: Repositories) -> None:
    first, second = _batch_specs(repositories)
    mismatched = replace(
        second,
        source=replace(second.source, commit=repositories.spec.source.commit),
    )
    with pytest.raises(CatalogError, match="share one source commit"):
        stage_batch(
            (first, mismatched),
            repositories.source,
            repositories.destination,
            repositories.destination_base,
        )
    _assert_clean(repositories)


def test_stage_batch_rejects_different_destinations(repositories: Repositories) -> None:
    first, second = _batch_specs(repositories)
    mismatched = replace(
        second,
        destination=replace(
            second.destination,
            repository="https://github.com/example/ios-2",
        ),
    )
    with pytest.raises(CatalogError, match="share one destination repository"):
        stage_batch(
            (first, mismatched),
            repositories.source,
            repositories.destination,
            repositories.destination_base,
        )
    _assert_clean(repositories)


def test_stage_batch_rejects_overlapping_targets(repositories: Repositories) -> None:
    first, second = _batch_specs(repositories)
    overlapping = replace(
        second,
        destination=replace(
            second.destination,
            payload_path=f"{first.destination.payload_path}/nested",
        ),
    )
    with pytest.raises(CatalogError, match="destination paths overlap"):
        stage_batch(
            (first, overlapping),
            repositories.source,
            repositories.destination,
            repositories.destination_base,
        )
    _assert_clean(repositories)


def test_later_payload_mutation_rolls_back_entire_batch(
    repositories: Repositories,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    specs = _batch_specs(repositories)
    copy_count = 0

    def mutate_second_copy(source: Path, destination: Path) -> None:
        nonlocal copy_count
        copy_count += 1
        shutil.copytree(
            source,
            destination,
            copy_function=shutil.copy2,
            dirs_exist_ok=True,
        )
        if copy_count == EXPECTED_PAYLOAD_COUNT:
            (destination / "payload.md").write_text("mutated\n", encoding="utf-8")

    monkeypatch.setattr("ipsw_diff_catalog.stage._copy_payload", mutate_second_copy)
    with pytest.raises(CatalogError, match="staged payload inventory mismatch"):
        stage_batch(
            specs,
            repositories.source,
            repositories.destination,
            repositories.destination_base,
        )
    _assert_clean(repositories)
    _assert_batch_targets_absent(repositories, specs)


def test_later_manifest_collision_is_preserved_and_batch_is_rolled_back(
    repositories: Repositories,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    specs = _batch_specs(repositories)
    collision = repositories.destination / specs[1].destination.manifest_path
    copy_count = 0

    def collide_during_second_copy(source: Path, destination: Path) -> None:
        nonlocal copy_count
        copy_count += 1
        shutil.copytree(
            source,
            destination,
            copy_function=shutil.copy2,
            dirs_exist_ok=True,
        )
        if copy_count == EXPECTED_PAYLOAD_COUNT:
            collision.write_text("concurrent\n", encoding="utf-8")

    monkeypatch.setattr("ipsw_diff_catalog.stage._copy_payload", collide_during_second_copy)
    with pytest.raises(CatalogError, match="refusing to overwrite destination path"):
        stage_batch(
            specs,
            repositories.source,
            repositories.destination,
            repositories.destination_base,
        )
    assert collision.read_text(encoding="utf-8") == "concurrent\n"
    assert not (repositories.destination / specs[0].destination.payload_path).exists()
    assert not (repositories.destination / specs[0].destination.manifest_path).exists()
    assert not (repositories.destination / specs[1].destination.payload_path).exists()
    assert git(repositories.destination, "diff", "--cached", "--name-only") == ""


def test_validate_staged_batch_rejects_extra_path(repositories: Repositories) -> None:
    specs = _batch_specs(repositories)
    stage_batch(
        specs,
        repositories.source,
        repositories.destination,
        repositories.destination_base,
    )
    extra = repositories.destination / "unexpected.txt"
    extra.write_text("extra\n", encoding="utf-8")
    git(repositories.destination, "add", "--", "unexpected.txt")
    with pytest.raises(CatalogError, match="staged path set differs"):
        validate_staged_batch(
            specs,
            repositories.source,
            repositories.destination,
            repositories.destination_base,
        )
