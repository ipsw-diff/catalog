from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

from ipsw_diff_catalog.git import (
    blob_at_path,
    ensure_repository,
    require_origin,
    resolve_commit,
    run_git,
    tree_entries,
)
from ipsw_diff_catalog.model import (
    CatalogEntry,
    CatalogError,
    JsonObject,
    MigrationSpec,
    canonical_json,
    parse_json_object,
    read_json_object,
)
from ipsw_diff_catalog.verify import verify

_FULL_OID = re.compile(r"[0-9a-f]{40}")
_WORKFLOW_RUN = re.compile(r"https://github\.com/[^/]+/[^/]+/actions/runs/[0-9]+")
_PROVENANCE_KEYS = {
    "schema_version",
    "catalog_commit",
    "source_commit",
    "source_tag",
    "workflow_run",
    "workflow_commit",
    "generator",
    "signatures",
    "discovery",
    "inputs",
}


@dataclass(frozen=True)
class ReconciliationResult:
    destination_commit: str
    manifest_count: int
    recorded_count: int
    reconciled_count: int


@dataclass(frozen=True)
class _Output:
    path: Path
    content: str


def _object(value: object, context: str) -> JsonObject:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise CatalogError(f"{context} must be an object")
    return cast("JsonObject", value)


def _string(value: object, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise CatalogError(f"{context} must be a non-empty string")
    return value


def _exact_keys(value: JsonObject, expected: set[str], context: str) -> None:
    actual = set(value)
    if actual != expected:
        raise CatalogError(
            f"{context} keys differ: "
            f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
        )


def _spec_from_manifest(manifest: JsonObject, manifest_path: str) -> MigrationSpec:
    _exact_keys(
        manifest,
        {
            "schema_version",
            "id",
            "platform",
            "major_version",
            "device",
            "from",
            "to",
            "payload",
            "source",
        },
        f"generated manifest {manifest_path}",
    )
    payload = _object(manifest["payload"], f"{manifest_path}.payload")
    _exact_keys(
        payload,
        {"path", "entrypoint", "tracked_file_count", "logical_bytes", "git_tree"},
        f"{manifest_path}.payload",
    )
    source = _object(manifest["source"], f"{manifest_path}.source")
    repository = _string(source.get("repository"), f"{manifest_path}.source.repository")
    spec: JsonObject = {
        "schema_version": manifest["schema_version"],
        "id": manifest["id"],
        "platform": manifest["platform"],
        "major_version": manifest["major_version"],
        "device": manifest["device"],
        "from": manifest["from"],
        "to": manifest["to"],
        "source": source,
        "destination": {
            "repository": repository,
            "payload_path": payload["path"],
            "entrypoint": payload["entrypoint"],
            "manifest_path": manifest_path,
        },
    }
    return MigrationSpec.from_object(spec)


def _validate_provenance(repo: Path, commit: str, spec: MigrationSpec) -> None:
    path = f"provenance/{spec.source.path}.json"
    provenance = parse_json_object(blob_at_path(repo, commit, path), path)
    _exact_keys(provenance, _PROVENANCE_KEYS, path)
    if type(provenance["schema_version"]) is not int or provenance["schema_version"] != 1:
        raise CatalogError(f"{path}.schema_version must be 1")
    source_commit = _string(provenance["source_commit"], f"{path}.source_commit")
    if source_commit != spec.source.commit:
        raise CatalogError(f"{path}.source_commit differs from generated manifest")
    source_tag = _string(provenance["source_tag"], f"{path}.source_tag")
    expected_tag = f"payload/{spec.source.path}"
    if source_tag != expected_tag:
        raise CatalogError(f"{path}.source_tag must be {expected_tag}")
    for field in ("catalog_commit", "workflow_commit"):
        oid = _string(provenance[field], f"{path}.{field}")
        if _FULL_OID.fullmatch(oid) is None:
            raise CatalogError(f"{path}.{field} must be a full lowercase SHA-1 object ID")
    workflow_run = _string(provenance["workflow_run"], f"{path}.workflow_run")
    expected_prefix = f"{spec.source.repository}/actions/runs/"
    if (
        not workflow_run.startswith(expected_prefix)
        or _WORKFLOW_RUN.fullmatch(workflow_run) is None
    ):
        raise CatalogError(f"{path}.workflow_run must identify the source repository")
    generator = _object(provenance["generator"], f"{path}.generator")
    _exact_keys(generator, {"name", "version"}, f"{path}.generator")
    if generator["name"] != "ipsw":
        raise CatalogError(f"{path}.generator.name must be ipsw")
    _string(generator["version"], f"{path}.generator.version")

    output = run_git(repo, "rev-parse", "--verify", f"refs/tags/{source_tag}^{{commit}}")
    assert isinstance(output, str)
    if output.strip() != spec.source.commit:
        raise CatalogError(f"{path}.source_tag does not resolve to source_commit")


def _existing_entries(entries_dir: Path) -> tuple[CatalogEntry, ...]:
    entries: list[CatalogEntry] = []
    identifiers: set[str] = set()
    for path in sorted(entries_dir.glob("*.json")):
        entry = CatalogEntry.from_object(read_json_object(path))
        if path.stem != entry.identifier:
            raise CatalogError(
                f"catalog entry filename must match id: {path.name} != {entry.identifier}.json"
            )
        if entry.identifier in identifiers:
            raise CatalogError(f"duplicate catalog id: {entry.identifier}")
        identifiers.add(entry.identifier)
        entries.append(entry)
    return tuple(entries)


def _manifest_paths(repo: Path, commit: str) -> tuple[str, ...]:
    paths: list[str] = []
    for entry in tree_entries(repo, commit, "manifests"):
        path = PurePosixPath(entry.path)
        if (
            path.is_absolute()
            or str(path) != entry.path
            or path.parts[0] != "manifests"
            or path.suffix != ".json"
        ):
            raise CatalogError(f"unsupported generated manifest path: {entry.path}")
        paths.append(entry.path)
    return tuple(sorted(paths))


def _preflight(outputs: tuple[_Output, ...]) -> None:
    paths: set[Path] = set()
    for output in outputs:
        if output.path in paths:
            raise CatalogError(f"duplicate reconciliation output: {output.path}")
        paths.add(output.path)
        if output.path.exists():
            try:
                observed = output.path.read_text(encoding="utf-8")
            except OSError as error:
                raise CatalogError(
                    f"cannot read reconciliation output {output.path}: {error}"
                ) from error
            if observed != output.content:
                raise CatalogError(f"refusing to overwrite differing output {output.path}")


def reconcile(
    shard_repo: Path,
    destination_revision: str,
    specs_dir: Path,
    entries_dir: Path,
) -> ReconciliationResult:
    repo = ensure_repository(shard_repo)
    destination_commit = resolve_commit(repo, destination_revision)
    if destination_commit != destination_revision:
        raise CatalogError("destination revision did not resolve to itself")

    recorded = _existing_entries(entries_dir)
    recorded_ids = {entry.identifier for entry in recorded}
    manifests = _manifest_paths(repo, destination_commit)
    seen_ids: set[str] = set()
    outputs: list[_Output] = []

    for manifest_path in manifests:
        manifest = parse_json_object(
            blob_at_path(repo, destination_commit, manifest_path),
            manifest_path,
        )
        identifier = _string(manifest.get("id"), f"{manifest_path}.id")
        if identifier in seen_ids:
            raise CatalogError(f"duplicate generated manifest id: {identifier}")
        seen_ids.add(identifier)
        if identifier in recorded_ids:
            continue

        spec = _spec_from_manifest(manifest, manifest_path)
        require_origin(repo, spec.source.repository, "generated shard")
        _validate_provenance(repo, destination_commit, spec)
        verified = verify(spec, repo, repo, destination_commit)
        outputs.extend(
            (
                _Output(
                    specs_dir / f"{spec.identifier}.json",
                    canonical_json(spec.to_object()),
                ),
                _Output(
                    entries_dir / f"{spec.identifier}.json",
                    canonical_json(
                        spec.catalog_entry(verified.source, verified.destination_commit)
                    ),
                ),
            )
        )

    if len(seen_ids) != len(manifests):
        raise CatalogError("generated manifest classification is incomplete")
    _preflight(tuple(outputs))
    for output in outputs:
        output.path.parent.mkdir(parents=True, exist_ok=True)
        output.path.write_text(output.content, encoding="utf-8")

    return ReconciliationResult(
        destination_commit=destination_commit,
        manifest_count=len(manifests),
        recorded_count=len(manifests) - len(outputs) // 2,
        reconciled_count=len(outputs) // 2,
    )
