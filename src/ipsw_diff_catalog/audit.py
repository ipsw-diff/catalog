from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from ipsw_diff_catalog.git import blob_at_path, identity, resolve_commit, run_git
from ipsw_diff_catalog.model import (
    CatalogError,
    MigrationSpec,
    TreeInventory,
    parse_json_object,
)
from ipsw_diff_catalog.render import load_entries
from ipsw_diff_catalog.verify import validate_source_identity


def _load_specs(specs_dir: Path) -> dict[str, MigrationSpec]:
    paths = sorted(specs_dir.glob("*.json"))
    if not paths:
        raise CatalogError(f"no migration specifications found in {specs_dir}")
    specs: dict[str, MigrationSpec] = {}
    for path in paths:
        spec = MigrationSpec.from_path(path)
        if path.stem != spec.identifier:
            raise CatalogError(
                f"migration spec filename must match id: {path.name} != {spec.identifier}.json"
            )
        if spec.identifier in specs:
            raise CatalogError(f"duplicate migration specification id: {spec.identifier}")
        specs[spec.identifier] = spec
    return specs


def _initialize_remote(path: Path, repository: str) -> None:
    path.mkdir()
    try:
        subprocess.run(  # noqa: S603
            ["git", "init", "--quiet", "--object-format=sha1", os.fspath(path)],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise CatalogError(f"cannot initialize audit repository for {repository}") from error
    run_git(path, "remote", "add", "origin", repository)
    run_git(path, "config", "remote.origin.promisor", "true")
    run_git(path, "config", "remote.origin.partialCloneFilter", "blob:none")


def _fetch_commit(path: Path, commit: str) -> None:
    try:
        run_git(path, "cat-file", "-e", f"{commit}^{{commit}}")
    except CatalogError:
        run_git(
            path,
            "-c",
            "protocol.version=2",
            "fetch",
            "--quiet",
            "--depth=1",
            "--filter=blob:none",
            "origin",
            commit,
        )


def audit(entries_dir: Path, specs_dir: Path) -> int:
    entries = load_entries(entries_dir)
    specs = _load_specs(specs_dir)
    entry_ids = {entry.identifier for entry in entries}
    spec_ids = set(specs)
    if entry_ids != spec_ids:
        raise CatalogError(
            f"catalog/spec id sets differ: entry_only={sorted(entry_ids - spec_ids)}, "
            f"spec_only={sorted(spec_ids - entry_ids)}"
        )

    with tempfile.TemporaryDirectory(prefix="ipsw-diff-audit-") as raw_temp:
        root = Path(raw_temp)
        repositories: dict[str, Path] = {}

        def repository(url: str) -> Path:
            existing = repositories.get(url)
            if existing is not None:
                return existing
            path = root / f"repo-{len(repositories)}"
            _initialize_remote(path, url)
            repositories[url] = path
            return path

        for entry in entries:
            spec = specs[entry.identifier]
            source_repo = repository(spec.source.repository)
            destination_repo = repository(entry.destination_repository)
            _fetch_commit(source_repo, spec.source.commit)
            _fetch_commit(destination_repo, entry.destination_commit)
            source = validate_source_identity(spec, source_repo)
            destination_commit = resolve_commit(destination_repo, entry.destination_commit)
            destination = identity(
                destination_repo,
                destination_commit,
                spec.destination.payload_path,
            )
            if source != destination:
                raise CatalogError(
                    f"remote payload identity mismatch: source={source}, destination={destination}"
                )
            measured = TreeInventory(
                tree=source.tree,
                file_count=source.file_count,
                logical_bytes=entry.inventory.logical_bytes,
                modes=source.modes,
            )
            manifest_bytes = blob_at_path(
                destination_repo,
                destination_commit,
                spec.destination.manifest_path,
            )
            manifest = parse_json_object(manifest_bytes, "destination manifest")
            if manifest != spec.manifest(measured):
                raise CatalogError(
                    f"remote manifest differs from verified facts: {entry.identifier}"
                )
            blob_at_path(destination_repo, destination_commit, spec.entrypoint)
            expected = spec.catalog_entry(measured, destination_commit)
            if entry.data != expected:
                raise CatalogError(f"catalog entry differs from verified facts: {entry.identifier}")
    return len(entries)
