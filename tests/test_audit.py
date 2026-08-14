from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ipsw_diff_catalog.audit import (
    _fetch_blobs,
    _fetch_commit,
    _initialize_remote,
    audit,
)
from ipsw_diff_catalog.git import blob_oid_at_path, run_git
from ipsw_diff_catalog.model import CatalogError
from ipsw_diff_catalog.verify import record
from tests.helpers import populate_destination

if TYPE_CHECKING:
    from pathlib import Path

    from tests.helpers import Repositories


def test_fetch_blobs_batches_required_partial_clone_objects(
    repositories: Repositories,
    tmp_path: Path,
) -> None:
    source = repositories.source
    run_git(source, "config", "uploadpack.allowFilter", "true")
    remote = tmp_path / "audit"
    _initialize_remote(remote, f"file://{source}")
    _fetch_commit(remote, repositories.spec.source.commit)
    readme_oid = blob_oid_at_path(
        remote,
        repositories.spec.source.commit,
        repositories.spec.source_entrypoint,
    )
    payload_oid = blob_oid_at_path(
        remote,
        repositories.spec.source.commit,
        "source-diff/nested/payload.md",
    )

    _fetch_blobs(remote, {readme_oid, payload_oid})
    run_git(remote, "remote", "remove", "origin")

    readme = run_git(remote, "cat-file", "blob", readme_oid)
    payload = run_git(remote, "cat-file", "blob", payload_oid)
    assert isinstance(readme, str)
    assert isinstance(payload, str)
    assert readme.startswith("# 1.0")
    assert payload == "payload\n"


def test_audit_rejects_catalog_and_spec_set_mismatch(
    repositories: Repositories,
    tmp_path: Path,
) -> None:
    entries = tmp_path / "entries"
    specs = tmp_path / "specs"
    specs.mkdir()
    destination_commit = populate_destination(repositories)
    record(
        repositories.spec,
        repositories.source,
        repositories.destination,
        destination_commit,
        entries,
    )
    (specs / "different-id.json").write_text(
        repositories.spec_path.read_text(encoding="utf-8").replace(
            repositories.spec.identifier,
            "different-id",
        ),
        encoding="utf-8",
    )
    with pytest.raises(CatalogError, match="catalog/spec id sets differ"):
        audit(entries, specs)
