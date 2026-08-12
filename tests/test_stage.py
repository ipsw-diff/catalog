from __future__ import annotations

import json
import shutil
from typing import TYPE_CHECKING

import pytest

from ipsw_diff_catalog.model import CatalogError
from ipsw_diff_catalog.stage import StageResult, stage, validate_staged
from tests.helpers import commit_all, git

if TYPE_CHECKING:
    from pathlib import Path

    from tests.helpers import Repositories

EXPECTED_FILE_COUNT = 3
EXPECTED_STAGED_PATH_COUNT = 4


def _stage(repositories: Repositories) -> StageResult:
    return stage(
        repositories.spec,
        repositories.source,
        repositories.destination,
        repositories.destination_base,
    )


def _validate(repositories: Repositories) -> StageResult:
    return validate_staged(
        repositories.spec,
        repositories.source,
        repositories.destination,
        repositories.destination_base,
    )


def _assert_clean(repositories: Repositories) -> None:
    assert git(repositories.destination, "status", "--porcelain=v1", "--untracked-files=all") == ""


def test_stage_reconstructs_exact_tree_and_stages_only_outputs(
    repositories: Repositories,
) -> None:
    result = _stage(repositories)
    assert result.base_commit == repositories.destination_base
    assert result.inventory.file_count == EXPECTED_FILE_COUNT
    assert result.staged_path_count == EXPECTED_STAGED_PATH_COUNT
    assert result.inventory.tree == git(repositories.source, "rev-parse", "HEAD:source-diff")

    repeated = _validate(repositories)
    assert repeated == result
    assert git(repositories.destination, "rev-parse", "HEAD") == repositories.destination_base
    assert sorted(
        git(repositories.destination, "diff", "--cached", "--name-only").splitlines()
    ) == [
        "diffs/source-diff/README.md",
        "diffs/source-diff/nested/payload.md",
        "diffs/source-diff/tool",
        "manifests/source-diff.json",
    ]


def test_stage_rejects_dirty_destination(repositories: Repositories) -> None:
    (repositories.destination / "unexpected.txt").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(CatalogError, match="destination worktree is not clean"):
        _stage(repositories)


@pytest.mark.parametrize("target", ["payload", "manifest"])
def test_stage_refuses_preexisting_targets(
    repositories: Repositories,
    target: str,
) -> None:
    if target == "payload":
        path = repositories.destination / repositories.spec.destination.payload_path
        path.mkdir(parents=True)
    else:
        path = repositories.destination / repositories.spec.destination.manifest_path
        path.parent.mkdir(parents=True)
        path.write_text("existing\n", encoding="utf-8")
    with pytest.raises(CatalogError, match="refusing to overwrite destination path"):
        _stage(repositories)
    if target == "payload":
        assert path.is_dir()
    else:
        assert path.read_text(encoding="utf-8") == "existing\n"


def test_stage_rejects_symlink_parent(
    repositories: Repositories,
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (repositories.destination / "diffs").symlink_to(outside, target_is_directory=True)
    with pytest.raises(CatalogError, match="destination parent is not a real directory"):
        _stage(repositories)
    assert list(outside.iterdir()) == []


def test_stage_rejects_destination_origin_mismatch(repositories: Repositories) -> None:
    git(repositories.destination, "remote", "set-url", "origin", "https://github.com/example/wrong")
    with pytest.raises(CatalogError, match="destination origin differs"):
        _stage(repositories)
    _assert_clean(repositories)


def test_validate_staged_rejects_payload_mutation(repositories: Repositories) -> None:
    _stage(repositories)
    payload = (
        repositories.destination / repositories.spec.destination.payload_path / "nested/payload.md"
    )
    payload.write_text("mutated\n", encoding="utf-8")
    git(repositories.destination, "add", "--", repositories.spec.destination.payload_path)
    with pytest.raises(CatalogError, match="staged payload inventory mismatch"):
        _validate(repositories)


def test_validate_staged_rejects_manifest_mutation(repositories: Repositories) -> None:
    _stage(repositories)
    manifest_path = repositories.destination / repositories.spec.destination.manifest_path
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["payload"]["logical_bytes"] += 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    git(repositories.destination, "add", "--", repositories.spec.destination.manifest_path)
    with pytest.raises(CatalogError, match="staged manifest differs"):
        _validate(repositories)


def test_validate_staged_rejects_extra_path(repositories: Repositories) -> None:
    _stage(repositories)
    extra = repositories.destination / "unexpected.txt"
    extra.write_text("extra\n", encoding="utf-8")
    git(repositories.destination, "add", "--", "unexpected.txt")
    with pytest.raises(CatalogError, match="staged path set differs"):
        _validate(repositories)


def test_failed_post_copy_validation_rolls_back(
    repositories: Repositories,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def mutate_copy(source: Path, destination: Path) -> None:
        shutil.copytree(
            source,
            destination,
            copy_function=shutil.copy2,
            dirs_exist_ok=True,
        )
        (destination / "nested/payload.md").write_text("mutated\n", encoding="utf-8")

    monkeypatch.setattr("ipsw_diff_catalog.stage._copy_payload", mutate_copy)
    with pytest.raises(CatalogError, match="staged payload inventory mismatch"):
        _stage(repositories)
    _assert_clean(repositories)
    assert not (repositories.destination / repositories.spec.destination.payload_path).exists()
    assert not (repositories.destination / repositories.spec.destination.manifest_path).exists()


def test_concurrent_manifest_is_preserved_on_rollback(
    repositories: Repositories,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = repositories.destination / repositories.spec.destination.manifest_path

    def collide_after_copy(source: Path, destination: Path) -> None:
        shutil.copytree(
            source,
            destination,
            copy_function=shutil.copy2,
            dirs_exist_ok=True,
        )
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text("concurrent\n", encoding="utf-8")

    monkeypatch.setattr("ipsw_diff_catalog.stage._copy_payload", collide_after_copy)
    with pytest.raises(CatalogError, match="refusing to overwrite destination path"):
        _stage(repositories)
    assert manifest.read_text(encoding="utf-8") == "concurrent\n"
    assert not (repositories.destination / repositories.spec.destination.payload_path).exists()


def test_stage_rejects_changed_destination_head(repositories: Repositories) -> None:
    (repositories.destination / "new-base.txt").write_text("new\n", encoding="utf-8")
    commit_all(repositories.destination, "move base")
    with pytest.raises(CatalogError, match="destination HEAD differs"):
        _stage(repositories)
