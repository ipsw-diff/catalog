from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ipsw_diff_catalog.model import canonical_json
from ipsw_diff_catalog.verify import validate_source

if TYPE_CHECKING:
    from pathlib import Path

    from ipsw_diff_catalog.model import MigrationSpec


def git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(  # noqa: S603
        ["git", "-C", os.fspath(repo), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def init_repo(path: Path) -> None:
    path.mkdir()
    subprocess.run(  # noqa: S603
        ["git", "init", "--quiet", "--object-format=sha1", os.fspath(path)],
        check=True,
        capture_output=True,
    )
    git(path, "config", "user.name", "Test User")
    git(path, "config", "user.email", "test@example.invalid")
    # Test fixtures must never invoke the user's signing agent or keychain.
    git(path, "config", "commit.gpgSign", "false")
    git(path, "config", "tag.gpgSign", "false")


def commit_all(repo: Path, message: str) -> str:
    git(repo, "add", "--all")
    git(repo, "-c", "commit.gpgSign=false", "commit", "--quiet", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def populate_destination(repositories: Repositories) -> str:
    inventory = validate_source(repositories.spec, repositories.source)
    source = repositories.source / repositories.spec.source.path
    payload = repositories.destination / repositories.spec.destination.payload_path
    payload.parent.mkdir(parents=True)
    shutil.copytree(source, payload, copy_function=shutil.copy2)
    manifest = repositories.destination / repositories.spec.destination.manifest_path
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        canonical_json(repositories.spec.manifest(inventory)),
        encoding="utf-8",
    )
    return commit_all(repositories.destination, "populate destination")


@dataclass(frozen=True)
class Repositories:
    source: Path
    destination: Path
    spec: MigrationSpec
    spec_path: Path
    destination_base: str
