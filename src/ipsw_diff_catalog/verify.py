from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ipsw_diff_catalog.git import (
    blob_at_path,
    ensure_repository,
    identity,
    inventory,
    resolve_commit,
)
from ipsw_diff_catalog.model import (
    CatalogError,
    MigrationSpec,
    TreeIdentity,
    TreeInventory,
    canonical_json,
    parse_json_object,
)
from ipsw_diff_catalog.source import parse_source_readme

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class Verification:
    source: TreeInventory
    destination: TreeInventory
    destination_commit: str


def _validate_source_entrypoint(spec: MigrationSpec, repo: Path, commit: str) -> None:
    entrypoint_path = spec.source_entrypoint
    try:
        report = blob_at_path(repo, commit, entrypoint_path).decode("utf-8")
    except UnicodeDecodeError as error:
        raise CatalogError(f"source entrypoint is not UTF-8: {entrypoint_path}") from error
    _validate_report(spec, report)


def validate_source(spec: MigrationSpec, source_repo: Path) -> TreeInventory:
    repo = ensure_repository(source_repo)
    resolved = resolve_commit(repo, spec.source.commit)
    if resolved != spec.source.commit:
        raise CatalogError("source.commit did not resolve to itself")
    measured = inventory(repo, resolved, spec.source.path)
    _validate_source_entrypoint(spec, repo, resolved)
    return measured


def validate_source_identity(spec: MigrationSpec, source_repo: Path) -> TreeIdentity:
    repo = ensure_repository(source_repo)
    resolved = resolve_commit(repo, spec.source.commit)
    if resolved != spec.source.commit:
        raise CatalogError("source.commit did not resolve to itself")
    measured = identity(repo, resolved, spec.source.path)
    _validate_source_entrypoint(spec, repo, resolved)
    return measured


def _validate_report(spec: MigrationSpec, report: str) -> None:
    parsed = parse_source_readme(report)
    observed_title = (
        parsed.previous.version,
        parsed.previous.build,
        parsed.next.version,
        parsed.next.build,
    )
    expected_title = (
        spec.previous.version,
        spec.previous.build,
        spec.next.version,
        spec.next.build,
    )
    if observed_title != expected_title:
        raise CatalogError(
            f"source report title mismatch: expected '# {spec.title}', "
            f"got '# {parsed.previous.version} ({parsed.previous.build}) .vs "
            f"{parsed.next.version} ({parsed.next.build})'"
        )
    observed_inputs = (parsed.previous.input_name, parsed.next.input_name)
    expected_inputs = (spec.previous.input_name, spec.next.input_name)
    if observed_inputs != expected_inputs:
        raise CatalogError(
            f"source report inputs differ: expected={expected_inputs!r}, "
            f"observed={observed_inputs!r}"
        )


def verify(
    spec: MigrationSpec,
    source_repo: Path,
    destination_repo: Path,
    destination_revision: str,
) -> Verification:
    source = validate_source(spec, source_repo)
    destination_path = ensure_repository(destination_repo)
    destination_commit = resolve_commit(destination_path, destination_revision)
    destination = inventory(destination_path, destination_commit, spec.destination.payload_path)
    if destination != source:
        raise CatalogError(
            f"payload inventory mismatch: source={source}, destination={destination}"
        )
    raw_manifest = blob_at_path(
        destination_path,
        destination_commit,
        spec.destination.manifest_path,
    )
    observed_manifest = parse_json_object(raw_manifest, "destination manifest")
    expected_manifest = spec.manifest(source)
    if observed_manifest != expected_manifest:
        raise CatalogError("destination manifest differs from measured source facts")
    blob_at_path(destination_path, destination_commit, spec.entrypoint)
    return Verification(
        source=source,
        destination=destination,
        destination_commit=destination_commit,
    )


def record(
    spec: MigrationSpec,
    source_repo: Path,
    destination_repo: Path,
    destination_revision: str,
    entries_dir: Path,
) -> Path:
    result = verify(spec, source_repo, destination_repo, destination_revision)
    entry = spec.catalog_entry(result.source, result.destination_commit)
    entries_dir.mkdir(parents=True, exist_ok=True)
    path = entries_dir / f"{spec.identifier}.json"
    content = canonical_json(entry)
    if path.exists():
        if path.read_text(encoding="utf-8") != content:
            raise CatalogError(f"refusing to overwrite differing catalog entry {path}")
        return path
    path.write_text(content, encoding="utf-8")
    return path


def materialize_manifest(
    spec: MigrationSpec,
    source_repo: Path,
    output: Path,
    *,
    check: bool,
) -> TreeInventory:
    inventory = validate_source(spec, source_repo)
    content = canonical_json(spec.manifest(inventory))
    if check:
        if not output.is_file():
            raise CatalogError(f"manifest does not exist: {output}")
        if output.read_text(encoding="utf-8") != content:
            raise CatalogError(f"manifest differs from measured source facts: {output}")
        return inventory
    if output.exists():
        if output.is_file() and output.read_text(encoding="utf-8") == content:
            return inventory
        raise CatalogError(f"refusing to overwrite differing manifest {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return inventory
