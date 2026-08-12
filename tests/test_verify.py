from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from ipsw_diff_catalog.model import CatalogError, MigrationSpec
from ipsw_diff_catalog.verify import record, validate_source, verify
from tests.helpers import commit_all, git, populate_destination

if TYPE_CHECKING:
    from pathlib import Path

    from tests.helpers import Repositories

EXPECTED_FILE_COUNT = 3
EXPECTED_LOGICAL_BYTES = 138


def test_verify_and_record_round_trip(repositories: Repositories, tmp_path: Path) -> None:
    destination_commit = populate_destination(repositories)
    result = verify(
        repositories.spec,
        repositories.source,
        repositories.destination,
        destination_commit,
    )
    assert result.source == result.destination
    assert result.destination_commit == destination_commit
    assert result.source.file_count == EXPECTED_FILE_COUNT
    assert result.source.logical_bytes == EXPECTED_LOGICAL_BYTES
    assert result.source.tree == git(repositories.source, "rev-parse", "HEAD:source-diff")

    entry_path = record(
        repositories.spec,
        repositories.source,
        repositories.destination,
        destination_commit,
        tmp_path / "entries",
    )
    entry = json.loads(entry_path.read_text(encoding="utf-8"))
    assert entry["destination"]["commit"] == destination_commit
    assert entry["integrity"]["git_tree"] == result.source.tree


def test_readme_metadata_mismatch_fails(repositories: Repositories) -> None:
    value = json.loads(repositories.spec_path.read_text(encoding="utf-8"))
    value["from"]["version"] = "9.9"
    spec = MigrationSpec.from_object(value)
    with pytest.raises(CatalogError, match="README title mismatch"):
        validate_source(spec, repositories.source)


def test_mutable_destination_revision_is_rejected(repositories: Repositories) -> None:
    populate_destination(repositories)
    with pytest.raises(CatalogError, match="full lowercase SHA-1"):
        verify(
            repositories.spec,
            repositories.source,
            repositories.destination,
            "HEAD",
        )


def test_payload_mutation_breaks_verification(repositories: Repositories) -> None:
    populate_destination(repositories)
    payload = (
        repositories.destination / repositories.spec.destination.payload_path / "nested/payload.md"
    )
    payload.write_text("mutated\n", encoding="utf-8")
    destination_commit = commit_all(repositories.destination, "mutate payload")
    with pytest.raises(CatalogError, match="payload inventory mismatch"):
        verify(
            repositories.spec,
            repositories.source,
            repositories.destination,
            destination_commit,
        )


def test_manifest_mutation_breaks_verification(repositories: Repositories) -> None:
    populate_destination(repositories)
    manifest_path = repositories.destination / repositories.spec.destination.manifest_path
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["payload"]["logical_bytes"] += 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    destination_commit = commit_all(repositories.destination, "mutate manifest")
    with pytest.raises(CatalogError, match="manifest differs"):
        verify(
            repositories.spec,
            repositories.source,
            repositories.destination,
            destination_commit,
        )


def test_record_never_overwrites_different_entry(
    repositories: Repositories,
    tmp_path: Path,
) -> None:
    destination_commit = populate_destination(repositories)
    entries = tmp_path / "entries"
    path = entries / f"{repositories.spec.identifier}.json"
    entries.mkdir()
    path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(CatalogError, match="refusing to overwrite"):
        record(
            repositories.spec,
            repositories.source,
            repositories.destination,
            destination_commit,
            entries,
        )
