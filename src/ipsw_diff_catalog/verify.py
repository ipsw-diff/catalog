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

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class Verification:
    source: TreeInventory
    destination: TreeInventory
    destination_commit: str


def _validate_source_readme(spec: MigrationSpec, repo: Path, commit: str) -> None:
    readme_path = f"{spec.source.path}/README.md"
    try:
        readme = blob_at_path(repo, commit, readme_path).decode("utf-8")
    except UnicodeDecodeError as error:
        raise CatalogError(f"source README is not UTF-8: {readme_path}") from error
    _validate_readme(spec, readme)


def validate_source(spec: MigrationSpec, source_repo: Path) -> TreeInventory:
    repo = ensure_repository(source_repo)
    resolved = resolve_commit(repo, spec.source.commit)
    if resolved != spec.source.commit:
        raise CatalogError("source.commit did not resolve to itself")
    measured = inventory(repo, resolved, spec.source.path)
    _validate_source_readme(spec, repo, resolved)
    return measured


def validate_source_identity(spec: MigrationSpec, source_repo: Path) -> TreeIdentity:
    repo = ensure_repository(source_repo)
    resolved = resolve_commit(repo, spec.source.commit)
    if resolved != spec.source.commit:
        raise CatalogError("source.commit did not resolve to itself")
    measured = identity(repo, resolved, spec.source.path)
    _validate_source_readme(spec, repo, resolved)
    return measured


def _validate_readme(spec: MigrationSpec, readme: str) -> None:
    lines = readme.splitlines()
    if not lines or lines[0] != f"# {spec.title}":
        actual = lines[0] if lines else "<empty>"
        raise CatalogError(
            f"source README title mismatch: expected '# {spec.title}', got {actual!r}"
        )
    headings = [index for index, line in enumerate(lines) if line == "## Inputs"]
    if len(headings) != 1:
        raise CatalogError(
            f"source README must have exactly one '## Inputs' section; found {len(headings)}"
        )
    start = headings[0] + 1
    section: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line:
            section.append(line)
    expected = [
        f"- `{spec.previous.input_name}`",
        f"- `{spec.next.input_name}`",
    ]
    if section != expected:
        raise CatalogError(
            f"source README inputs differ: expected={expected!r}, observed={section!r}"
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
