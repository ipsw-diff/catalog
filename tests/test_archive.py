from __future__ import annotations

import json
from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

from ipsw_diff_catalog.archive import archive_readme, load_archive_specs, render_archive
from ipsw_diff_catalog.model import CatalogError

if TYPE_CHECKING:
    from pathlib import Path

    from tests.helpers import Repositories


def test_archive_readme_is_deterministic_and_check_detects_stale_output(
    repositories: Repositories,
    tmp_path: Path,
) -> None:
    specs = tmp_path / "specs"
    specs.mkdir()
    spec_path = specs / f"{repositories.spec.identifier}.json"
    spec_path.write_bytes(repositories.spec_path.read_bytes())
    output = tmp_path / "README.md"

    count = render_archive(
        specs,
        repositories.spec.destination.repository,
        output,
        check=False,
    )

    assert count == 1
    first = output.read_bytes()
    assert output.read_text(encoding="utf-8") == archive_readme((repositories.spec,))
    render_archive(
        specs,
        repositories.spec.destination.repository,
        output,
        check=True,
    )
    render_archive(
        specs,
        repositories.spec.destination.repository,
        output,
        check=False,
    )
    assert output.read_bytes() == first

    output.write_text("stale\n", encoding="utf-8")
    with pytest.raises(CatalogError, match="archive README is stale"):
        render_archive(
            specs,
            repositories.spec.destination.repository,
            output,
            check=True,
        )


def test_archive_rejects_missing_destination_route(
    repositories: Repositories,
    tmp_path: Path,
) -> None:
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / f"{repositories.spec.identifier}.json").write_bytes(
        repositories.spec_path.read_bytes()
    )

    with pytest.raises(CatalogError, match="no migration specs route"):
        load_archive_specs(specs, "https://github.com/example/macos-1")


def test_archive_sorts_by_device_then_immutable_source_path(
    repositories: Repositories,
    tmp_path: Path,
) -> None:
    specs = tmp_path / "specs"
    specs.mkdir()
    original = json.loads(repositories.spec_path.read_text(encoding="utf-8"))
    original_id = str(original["id"])
    (specs / f"{original_id}.json").write_text(json.dumps(original), encoding="utf-8")
    earlier = json.loads(repositories.spec_path.read_text(encoding="utf-8"))
    earlier["id"] = "ios-1.0-a0-a1"
    earlier["source"]["path"] = "aaa-source-diff"
    earlier["destination"]["payload_path"] = "diffs/aaa-source-diff"
    earlier["destination"]["manifest_path"] = "manifests/aaa-source-diff.json"
    (specs / "ios-1.0-a0-a1.json").write_text(json.dumps(earlier), encoding="utf-8")

    loaded = load_archive_specs(specs, repositories.spec.destination.repository)

    assert [spec.source.path for spec in loaded] == ["aaa-source-diff", "source-diff"]
    rendered = archive_readme(loaded)
    assert "no linear\nrelease sequence is implied" in rendered


def test_archive_rejects_mismatched_spec_filename(
    repositories: Repositories,
    tmp_path: Path,
) -> None:
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "wrong.json").write_bytes(repositories.spec_path.read_bytes())

    with pytest.raises(CatalogError, match="filename must match id"):
        load_archive_specs(specs, repositories.spec.destination.repository)


def test_archive_readme_rejects_mixed_platforms(repositories: Repositories) -> None:
    mixed = replace(
        repositories.spec,
        identifier="macos-1.0-a1-a2",
        platform="macOS",
    )

    with pytest.raises(CatalogError, match="share one platform"):
        archive_readme((repositories.spec, mixed))


def test_archive_accepts_multiple_immutable_source_commits(
    repositories: Repositories,
) -> None:
    later = replace(
        repositories.spec,
        identifier="ios-1.0-a2-a3",
        source=replace(
            repositories.spec.source,
            commit="d" * 40,
            path="later-source-diff",
        ),
        destination=replace(
            repositories.spec.destination,
            payload_path="diffs/later-source-diff",
            entrypoint="diffs/later-source-diff/README.md",
            manifest_path="manifests/later-source-diff.json",
        ),
    )

    rendered = archive_readme((repositories.spec, later))

    assert "diffs/source-diff/README.md" in rendered
    assert "diffs/later-source-diff/README.md" in rendered


def test_archive_accepts_multiple_immutable_source_repositories(
    repositories: Repositories,
    tmp_path: Path,
) -> None:
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / f"{repositories.spec.identifier}.json").write_text(
        json.dumps(repositories.spec.to_object()),
        encoding="utf-8",
    )
    later = replace(
        repositories.spec,
        identifier="ios-1.0-a2-a3",
        source=replace(
            repositories.spec.source,
            repository="https://github.com/ipsw-diff/ios-1",
            commit="d" * 40,
            path="later-source-diff",
        ),
        destination=replace(
            repositories.spec.destination,
            payload_path="diffs/later-source-diff",
            entrypoint="diffs/later-source-diff/README.md",
            manifest_path="manifests/later-source-diff.json",
        ),
    )
    (specs / f"{later.identifier}.json").write_text(
        json.dumps(later.to_object()),
        encoding="utf-8",
    )

    loaded = load_archive_specs(specs, repositories.spec.destination.repository)
    rendered = archive_readme(loaded)

    assert "diffs/source-diff/README.md" in rendered
    assert "diffs/later-source-diff/README.md" in rendered
    assert "immutable source and Git tree identity" in rendered


def test_archive_links_explicit_toc_entrypoint(repositories: Repositories) -> None:
    toc = replace(
        repositories.spec,
        destination=replace(
            repositories.spec.destination,
            entrypoint="diffs/source-diff/TOC.md",
        ),
    )

    rendered = archive_readme((toc,))

    assert "diffs/source-diff/TOC.md" in rendered
    assert "diffs/source-diff/README.md" not in rendered


def test_archive_rejects_duplicate_source_and_destination_path(
    repositories: Repositories,
    tmp_path: Path,
) -> None:
    specs = tmp_path / "specs"
    specs.mkdir()
    original = json.loads(repositories.spec_path.read_text(encoding="utf-8"))
    first_id = str(original["id"])
    (specs / f"{first_id}.json").write_text(json.dumps(original), encoding="utf-8")
    duplicate = dict(original)
    duplicate["id"] = "ios-1.0-a1-a3"
    duplicate["to"] = {
        "version": "1.0",
        "build": "A3",
        "input": "Device1,1_1.0_A3_Restore.ipsw",
    }
    (specs / "ios-1.0-a1-a3.json").write_text(json.dumps(duplicate), encoding="utf-8")

    with pytest.raises(CatalogError, match="source path"):
        load_archive_specs(specs, repositories.spec.destination.repository)
