from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from ipsw_diff_catalog.model import JsonObject, MigrationSpec
from tests.helpers import Repositories, commit_all, git, init_repo

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def repositories(tmp_path: Path) -> Repositories:
    source = tmp_path / "source"
    init_repo(source)
    git(source, "remote", "add", "origin", "https://github.com/example/source.git")
    source_payload = source / "source-diff"
    source_payload.mkdir()
    (source_payload / "README.md").write_text(
        "# 1.0 (A1) .vs 1.1 (A2)\n\n"
        "## Inputs\n\n"
        "- `Device1,1_1.0_A1_Restore.ipsw`\n"
        "- `Device1,1_1.1_A2_Restore.ipsw`\n\n"
        "## Data\n",
        encoding="utf-8",
    )
    nested = source_payload / "nested"
    nested.mkdir()
    (nested / "payload.md").write_bytes(b"payload\n")
    executable = source_payload / "tool"
    executable.write_bytes(b"#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    source_commit = commit_all(source, "source")

    destination = tmp_path / "destination"
    init_repo(destination)
    git(destination, "remote", "add", "origin", "https://github.com/example/ios-1.git")
    (destination / "README.md").write_text("# shard\n", encoding="utf-8")
    destination_base = commit_all(destination, "bootstrap")

    spec_object: JsonObject = {
        "schema_version": 1,
        "id": "ios-1.0-a1-a2",
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
            "repository": "https://github.com/example/source",
            "commit": source_commit,
            "path": "source-diff",
        },
        "destination": {
            "repository": "https://github.com/example/ios-1",
            "payload_path": "diffs/source-diff",
            "manifest_path": "manifests/source-diff.json",
        },
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec_object), encoding="utf-8")
    return Repositories(
        source=source,
        destination=destination,
        spec=MigrationSpec.from_object(spec_object),
        spec_path=spec_path,
        destination_base=destination_base,
    )
