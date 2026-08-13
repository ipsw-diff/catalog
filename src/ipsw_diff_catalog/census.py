from __future__ import annotations

import os
import re
import tempfile
from collections import Counter
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

from ipsw_diff_catalog.git import (
    TreeEntry,
    blob_at_path,
    ensure_repository,
    require_origin,
    resolve_commit,
    root_tree_oid,
    tracked_entries,
    tree_oid,
)
from ipsw_diff_catalog.model import CatalogError, JsonObject, canonical_json, read_json_object
from ipsw_diff_catalog.source import SourceReadmeError, parse_source_readme

_FULL_OID = re.compile(r"[0-9a-f]{40}")
_GITHUB_REPOSITORY = re.compile(
    r"https://github\.com/[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*"
)
_PATH_PART = re.compile(r"(?:[A-Za-z0-9]|\.[A-Za-z0-9])[A-Za-z0-9,._+@-]*")
_PATH_SUMMARY_LIMIT = 10
_ENTRYPOINT_NAMES = ("README.md", "TOC.md")


@dataclass(frozen=True)
class CensusPolicy:
    repository: str
    commit: str
    payload_roots: tuple[str, ...]
    excluded_roots: tuple[str, ...]
    excluded_files: tuple[str, ...]

    @classmethod
    def from_path(cls, path: Path) -> CensusPolicy:
        data = read_json_object(path)
        _exact_keys(
            data,
            {
                "schema_version",
                "source",
                "payload_roots",
                "excluded_roots",
                "excluded_files",
            },
            "census policy",
        )
        if type(data["schema_version"]) is not int or data["schema_version"] != 1:
            raise CatalogError("census policy schema_version must be 1")
        source = _object(data["source"], "census policy source")
        _exact_keys(source, {"repository", "commit"}, "census policy source")
        repository = _repository(source["repository"], "census policy source.repository")
        commit = _full_oid(source["commit"], "census policy source.commit")
        payload_roots = _path_list(data["payload_roots"], "payload_roots", required=True)
        excluded_roots = _path_list(data["excluded_roots"], "excluded_roots")
        excluded_files = _path_list(data["excluded_files"], "excluded_files")
        _require_disjoint_policy(payload_roots, excluded_roots, excluded_files)
        return cls(
            repository=repository,
            commit=commit,
            payload_roots=payload_roots,
            excluded_roots=excluded_roots,
            excluded_files=excluded_files,
        )


@dataclass(frozen=True)
class CensusResult:
    output: Path
    checked: bool
    payload_count: int
    ordinary_count: int
    blocked_count: int
    tracked_file_count: int
    logical_bytes: int


@dataclass
class _Partition:
    payloads: dict[str, list[TreeEntry]]
    excluded_roots: dict[str, list[TreeEntry]]
    excluded_files: dict[str, TreeEntry]
    unclassified: list[str]
    multiply_classified: list[str]


def _exact_keys(value: JsonObject, expected: set[str], context: str) -> None:
    actual = set(value)
    if actual != expected:
        raise CatalogError(
            f"{context} keys differ: "
            f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
        )


def _object(value: object, context: str) -> JsonObject:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise CatalogError(f"{context} must be an object")
    return cast("JsonObject", value)


def _repository(value: object, context: str) -> str:
    if not isinstance(value, str) or _GITHUB_REPOSITORY.fullmatch(value) is None:
        raise CatalogError(f"{context} must be an https://github.com/OWNER/REPOSITORY URL")
    return value.removesuffix(".git")


def _full_oid(value: object, context: str) -> str:
    if not isinstance(value, str) or _FULL_OID.fullmatch(value) is None:
        raise CatalogError(f"{context} must be a full lowercase SHA-1 object ID")
    return value


def _relative_path(value: object, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise CatalogError(f"{context} must be a non-empty string")
    path = PurePosixPath(value)
    if path.is_absolute() or str(path) != value or not path.parts:
        raise CatalogError(f"{context} must be a normalized relative POSIX path")
    if any(_PATH_PART.fullmatch(part) is None for part in path.parts):
        raise CatalogError(f"{context} contains an unsupported path component")
    return value


def _path_list(value: object, context: str, *, required: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise CatalogError(f"census policy {context} must be an array")
    paths = tuple(
        _relative_path(item, f"census policy {context}[{index}]")
        for index, item in enumerate(value)
    )
    if required and not paths:
        raise CatalogError(f"census policy {context} must not be empty")
    if len(paths) != len(set(paths)):
        raise CatalogError(f"census policy {context} must contain unique paths")
    if paths != tuple(sorted(paths)):
        raise CatalogError(f"census policy {context} must be sorted")
    return paths


def _paths_overlap(first: str, second: str) -> bool:
    return first == second or first.startswith(f"{second}/") or second.startswith(f"{first}/")


def _require_disjoint_policy(
    payload_roots: tuple[str, ...],
    excluded_roots: tuple[str, ...],
    excluded_files: tuple[str, ...],
) -> None:
    labelled = [
        *((path, "payload root") for path in payload_roots),
        *((path, "excluded root") for path in excluded_roots),
        *((path, "excluded file") for path in excluded_files),
    ]
    for index, (first, first_kind) in enumerate(labelled):
        for second, second_kind in labelled[index + 1 :]:
            if _paths_overlap(first, second):
                raise CatalogError(
                    "census policy paths overlap: "
                    f"{first_kind} {first!r} and {second_kind} {second!r}"
                )


def _ancestors(path: str) -> tuple[str, ...]:
    parts = PurePosixPath(path).parts
    return tuple("/".join(parts[:index]) for index in range(1, len(parts)))


def _summarize(paths: list[str]) -> list[str]:
    ordered = sorted(paths)
    if len(ordered) <= _PATH_SUMMARY_LIMIT:
        return ordered
    return [
        *ordered[:_PATH_SUMMARY_LIMIT],
        f"... and {len(ordered) - _PATH_SUMMARY_LIMIT} more",
    ]


def _entry_matches(
    path: str,
    payload_roots: set[str],
    excluded_roots: set[str],
    excluded_files: set[str],
) -> list[tuple[str, str]]:
    matches: list[tuple[str, str]] = []
    for ancestor in _ancestors(path):
        if ancestor in payload_roots:
            matches.append(("payload", ancestor))
        if ancestor in excluded_roots:
            matches.append(("excluded-root", ancestor))
    if path in excluded_files:
        matches.append(("excluded-file", path))
    return matches


def _require_complete_partition(
    partition: _Partition,
    policy: CensusPolicy,
) -> None:
    if partition.unclassified:
        raise CatalogError(
            "tracked files are not classified by census policy: "
            f"{_summarize(partition.unclassified)!r}"
        )
    if partition.multiply_classified:
        raise CatalogError(
            "tracked files are classified more than once by census policy: "
            f"{_summarize(partition.multiply_classified)!r}"
        )
    missing_payloads = [path for path, values in partition.payloads.items() if not values]
    missing_roots = [path for path, values in partition.excluded_roots.items() if not values]
    missing_files = [path for path in policy.excluded_files if path not in partition.excluded_files]
    if missing_payloads or missing_roots or missing_files:
        raise CatalogError(
            "census policy paths do not resolve to tracked objects: "
            f"payload_roots={missing_payloads}, excluded_roots={missing_roots}, "
            f"excluded_files={missing_files}"
        )


def _partition_entries(
    entries: tuple[TreeEntry, ...],
    policy: CensusPolicy,
) -> _Partition:
    partition = _Partition(
        payloads={path: [] for path in policy.payload_roots},
        excluded_roots={path: [] for path in policy.excluded_roots},
        excluded_files={},
        unclassified=[],
        multiply_classified=[],
    )
    payload_set = set(policy.payload_roots)
    excluded_root_set = set(policy.excluded_roots)
    excluded_file_set = set(policy.excluded_files)

    for entry in entries:
        matches = _entry_matches(
            entry.path,
            payload_set,
            excluded_root_set,
            excluded_file_set,
        )
        if not matches:
            partition.unclassified.append(entry.path)
            continue
        if len(matches) != 1:
            partition.multiply_classified.append(entry.path)
            continue
        kind, selected = matches[0]
        if kind == "payload":
            partition.payloads[selected].append(entry)
        elif kind == "excluded-root":
            partition.excluded_roots[selected].append(entry)
        else:
            partition.excluded_files[selected] = entry

    _require_complete_partition(partition, policy)
    return partition


def _tree_integrity(repo: Path, commit: str, path: str, entries: list[TreeEntry]) -> JsonObject:
    return {
        "git_tree": tree_oid(repo, commit, path),
        "tracked_file_count": len(entries),
        "logical_bytes": sum(entry.size for entry in entries),
        "modes": sorted({entry.mode for entry in entries}),
    }


def _payload_record(
    repo: Path,
    commit: str,
    path: str,
    entries: list[TreeEntry],
) -> JsonObject:
    entry_paths = {entry.path for entry in entries}
    entrypoint = next(
        (name for name in _ENTRYPOINT_NAMES if f"{path}/{name}" in entry_paths),
        None,
    )
    if entrypoint is None:
        classification = "blocked"
        reason: JsonObject | None = {
            "code": "missing-entrypoint",
            "detail": "payload has no tracked README.md or TOC.md",
        }
        readme: JsonObject | None = None
    else:
        readme_path = f"{path}/{entrypoint}"
        try:
            raw_readme = blob_at_path(repo, commit, readme_path).decode("utf-8")
        except UnicodeDecodeError:
            classification = "blocked"
            reason = {
                "code": "unsupported-readme",
                "detail": f"payload {entrypoint} is not UTF-8",
            }
            readme = None
        else:
            try:
                parsed = parse_source_readme(raw_readme)
            except SourceReadmeError as error:
                classification = "blocked"
                reason = {"code": error.code, "detail": error.detail}
                readme = None
            else:
                classification = "ordinary-two-ipsw"
                reason = None
                readme = parsed.to_object()
    return {
        "path": path,
        "classification": classification,
        "reason": reason,
        "entrypoint": entrypoint,
        "readme": readme,
        "integrity": _tree_integrity(repo, commit, path, entries),
    }


def _exclusion_records(
    repo: Path,
    commit: str,
    excluded_roots: dict[str, list[TreeEntry]],
    excluded_files: dict[str, TreeEntry],
) -> list[JsonObject]:
    records: list[JsonObject] = []
    for path, entries in excluded_roots.items():
        records.append(
            {
                "path": path,
                "kind": "tree",
                "integrity": _tree_integrity(repo, commit, path, entries),
            }
        )
    for path, entry in excluded_files.items():
        records.append(
            {
                "path": path,
                "kind": "file",
                "integrity": {
                    "git_blob": entry.oid,
                    "tracked_file_count": 1,
                    "logical_bytes": entry.size,
                    "modes": [entry.mode],
                },
            }
        )
    return sorted(records, key=lambda record: cast("str", record["path"]))


def _build_census(policy: CensusPolicy, repo: Path) -> JsonObject:
    entries = tracked_entries(repo, policy.commit)
    partition = _partition_entries(entries, policy)
    payloads = [
        _payload_record(repo, policy.commit, path, partition.payloads[path])
        for path in policy.payload_roots
    ]
    exclusions = _exclusion_records(
        repo,
        policy.commit,
        partition.excluded_roots,
        partition.excluded_files,
    )
    ordinary_count = sum(payload["classification"] == "ordinary-two-ipsw" for payload in payloads)
    blocked_count = len(payloads) - ordinary_count
    blocked_by_reason = Counter(
        cast("JsonObject", payload["reason"])["code"]
        for payload in payloads
        if payload["reason"] is not None
    )
    payload_file_count = sum(len(values) for values in partition.payloads.values())
    payload_bytes = sum(entry.size for values in partition.payloads.values() for entry in values)
    excluded_entries = [
        *(entry for values in partition.excluded_roots.values() for entry in values),
        *partition.excluded_files.values(),
    ]
    excluded_file_count = len(excluded_entries)
    excluded_bytes = sum(entry.size for entry in excluded_entries)
    tracked_file_count = len(entries)
    logical_bytes = sum(entry.size for entry in entries)
    if payload_file_count + excluded_file_count != tracked_file_count:
        raise CatalogError("census tracked-file reconciliation failed")
    if payload_bytes + excluded_bytes != logical_bytes:
        raise CatalogError("census logical-byte reconciliation failed")
    return {
        "schema_version": 1,
        "source": {
            "repository": policy.repository,
            "commit": policy.commit,
            "git_tree": root_tree_oid(repo, policy.commit),
        },
        "summary": {
            "payload_count": len(payloads),
            "ordinary_two_ipsw_count": ordinary_count,
            "blocked_count": blocked_count,
            "blocked_by_reason": dict(sorted(blocked_by_reason.items())),
        },
        "coverage": {
            "payloads": {
                "tracked_file_count": payload_file_count,
                "logical_bytes": payload_bytes,
            },
            "excluded": {
                "tracked_file_count": excluded_file_count,
                "logical_bytes": excluded_bytes,
            },
            "total": {
                "tracked_file_count": tracked_file_count,
                "logical_bytes": logical_bytes,
            },
        },
        "exclusions": exclusions,
        "payloads": payloads,
    }


def _output_path(source_repo: Path, policy_path: Path, output: Path) -> Path:
    resolved = output.resolve()
    if resolved == source_repo or resolved.is_relative_to(source_repo):
        raise CatalogError("census output must be outside the source repository")
    if resolved == policy_path.resolve():
        raise CatalogError("census output must differ from its policy file")
    if output.is_symlink():
        raise CatalogError("census output must not be a symbolic link")
    return resolved


def _write_atomic(path: Path, content: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, raw_temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    except OSError as error:
        raise CatalogError(f"cannot prepare census output {path}: {error}") from error
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            os.fchmod(stream.fileno(), 0o644)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    except OSError as error:
        with suppress(OSError):
            temporary.unlink(missing_ok=True)
        raise CatalogError(f"cannot write census output {path}: {error}") from error


def census(
    policy_path: Path,
    source_repo: Path,
    output: Path,
    *,
    check: bool = False,
) -> CensusResult:
    policy = CensusPolicy.from_path(policy_path)
    repo = ensure_repository(source_repo)
    require_origin(repo, policy.repository, "source")
    resolved_commit = resolve_commit(repo, policy.commit)
    if resolved_commit != policy.commit:
        raise CatalogError("census source commit did not resolve to itself")
    destination = _output_path(repo, policy_path, output)
    data = _build_census(policy, repo)
    content = canonical_json(data)
    if check:
        try:
            observed = destination.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise CatalogError(f"cannot read census output {destination}: {error}") from error
        if observed != content:
            raise CatalogError(f"census output differs: {destination}")
    else:
        _write_atomic(destination, content)
    summary = cast("JsonObject", data["summary"])
    coverage = cast("JsonObject", data["coverage"])
    total = cast("JsonObject", coverage["total"])
    return CensusResult(
        output=destination,
        checked=check,
        payload_count=cast("int", summary["payload_count"]),
        ordinary_count=cast("int", summary["ordinary_two_ipsw_count"]),
        blocked_count=cast("int", summary["blocked_count"]),
        tracked_file_count=cast("int", total["tracked_file_count"]),
        logical_bytes=cast("int", total["logical_bytes"]),
    )
