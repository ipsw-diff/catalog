from __future__ import annotations

import os
import shutil
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from ipsw_diff_catalog.git import (
    blob_at_path,
    ensure_repository,
    inventory,
    require_clean_worktree,
    resolve_commit,
    run_git,
    tree_entries,
)
from ipsw_diff_catalog.model import (
    CatalogError,
    MigrationSpec,
    TreeInventory,
    canonical_json,
    parse_json_object,
)
from ipsw_diff_catalog.verify import validate_source


@dataclass(frozen=True)
class StageResult:
    base_commit: str
    inventory: TreeInventory
    staged_path_count: int


@dataclass
class _StageTargets:
    payload: Path
    manifest: Path
    created_parents: list[Path] = field(default_factory=list)
    payload_owned: bool = False
    manifest_owned: bool = False
    index_touched: bool = False


_STATUS_PATH_OFFSET = 3
_PATH_SUMMARY_LIMIT = 10


def _require_origin(repo: Path, expected: str, context: str) -> None:
    output = run_git(repo, "remote", "get-url", "origin")
    assert isinstance(output, str)
    observed = output.strip()
    slug = expected.removeprefix("https://github.com/")
    accepted = {
        expected,
        f"{expected}.git",
        f"git@github.com:{slug}.git",
        f"ssh://git@github.com/{slug}.git",
    }
    if observed not in accepted:
        raise CatalogError(
            f"{context} origin differs: expected GitHub repository {expected}, got {observed!r}"
        )


def _require_base(repo: Path, revision: str) -> str:
    base = resolve_commit(repo, revision)
    output = run_git(repo, "rev-parse", "--verify", "HEAD^{commit}")
    assert isinstance(output, str)
    head = output.strip()
    if head != base:
        raise CatalogError(f"destination HEAD differs: expected {base}, got {head}")
    return base


def _target_path(repo: Path, relative: str) -> Path:
    return repo.joinpath(*PurePosixPath(relative).parts)


def _require_safe_absent_target(repo: Path, base: str, relative: str) -> Path:
    target = _target_path(repo, relative)
    current = repo
    for part in PurePosixPath(relative).parts[:-1]:
        current /= part
        if os.path.lexists(current) and (current.is_symlink() or not current.is_dir()):
            raise CatalogError(f"destination parent is not a real directory: {current}")
    if os.path.lexists(target):
        raise CatalogError(f"refusing to overwrite destination path: {target}")
    tracked = run_git(repo, "ls-tree", "-z", base, "--", relative, text=False)
    assert isinstance(tracked, bytes)
    if tracked:
        raise CatalogError(f"refusing to overwrite tracked destination path: {relative}")
    return target


def _ensure_parent_directories(
    repo: Path,
    relative: str,
    targets: _StageTargets,
) -> None:
    current = repo
    for part in PurePosixPath(relative).parts[:-1]:
        current /= part
        try:
            current.mkdir()
        except FileExistsError as error:
            if current.is_symlink() or not current.is_dir():
                raise CatalogError(
                    f"destination parent is not a real directory: {current}"
                ) from error
        except OSError as error:
            raise CatalogError(f"cannot create destination parent {current}: {error}") from error
        else:
            targets.created_parents.append(current)


def _expected_paths(spec: MigrationSpec, source_repo: Path) -> frozenset[str]:
    prefix = f"{spec.source.path}/"
    paths: set[str] = set()
    for entry in tree_entries(source_repo, spec.source.commit, spec.source.path):
        relative = entry.path.removeprefix(prefix)
        if not relative or relative == entry.path:
            raise CatalogError(f"source entry is outside the selected subtree: {entry.path}")
        paths.add(f"{spec.destination.payload_path}/{relative}")
    paths.add(spec.destination.manifest_path)
    return frozenset(paths)


def _archive_payload(
    spec: MigrationSpec,
    source_repo: Path,
    expected: TreeInventory,
    temporary_root: Path,
) -> Path:
    archive = temporary_root / "source.tar"
    extracted = temporary_root / "extracted"
    extracted.mkdir()
    run_git(
        source_repo,
        "archive",
        "--format=tar",
        f"--output={archive}",
        "--prefix=payload/",
        f"{spec.source.commit}:{spec.source.path}",
    )
    try:
        with tarfile.open(archive, mode="r:") as source_archive:
            source_archive.extractall(extracted, filter="data")
    except (OSError, tarfile.TarError) as error:
        raise CatalogError(f"cannot extract source archive: {error}") from error

    payload = extracted / "payload"
    if not payload.is_dir() or payload.is_symlink():
        raise CatalogError("source archive did not produce one real payload directory")
    if {path.name for path in extracted.iterdir()} != {"payload"}:
        raise CatalogError("source archive produced content outside its payload directory")

    run_git(extracted, "init", "--quiet", "--object-format=sha1")
    run_git(extracted, "config", "core.fileMode", "true")
    run_git(
        extracted,
        "-c",
        "core.autocrlf=false",
        "add",
        "--force",
        "--all",
        "--",
        "payload",
    )
    tree_output = run_git(extracted, "write-tree")
    assert isinstance(tree_output, str)
    observed = inventory(extracted, tree_output.strip(), "payload")
    if observed != expected:
        raise CatalogError(
            f"temporary extraction differs from source: expected={expected}, observed={observed}"
        )
    return payload


def _status_additions(repo: Path) -> frozenset[str]:
    output = run_git(
        repo,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        text=False,
    )
    assert isinstance(output, bytes)
    paths: set[str] = set()
    for record in output.split(b"\0"):
        if not record:
            continue
        if len(record) <= _STATUS_PATH_OFFSET or record[2:3] != b" ":
            raise CatalogError("cannot parse destination worktree status")
        try:
            path = record[_STATUS_PATH_OFFSET:].decode("utf-8")
        except UnicodeDecodeError as error:
            raise CatalogError("destination status contains a non-UTF-8 path") from error
        if record[:2] != b"A ":
            raise CatalogError(f"destination has a non-addition change: {record[:2]!r} {path}")
        paths.add(path)
    return frozenset(paths)


def _summarize_paths(paths: frozenset[str]) -> list[str]:
    ordered = sorted(paths)
    if len(ordered) <= _PATH_SUMMARY_LIMIT:
        return ordered
    return [
        *ordered[:_PATH_SUMMARY_LIMIT],
        f"... and {len(ordered) - _PATH_SUMMARY_LIMIT} more",
    ]


def _validate_staged(
    spec: MigrationSpec,
    destination_repo: Path,
    base: str,
    source_inventory: TreeInventory,
    expected_paths: frozenset[str],
) -> StageResult:
    actual_paths = _status_additions(destination_repo)
    if actual_paths != expected_paths:
        raise CatalogError(
            "staged path set differs: "
            f"missing={_summarize_paths(expected_paths - actual_paths)}, "
            f"extra={_summarize_paths(actual_paths - expected_paths)}"
        )
    tree_output = run_git(destination_repo, "write-tree")
    assert isinstance(tree_output, str)
    staged_root = tree_output.strip()
    staged_inventory = inventory(
        destination_repo,
        staged_root,
        spec.destination.payload_path,
    )
    if staged_inventory != source_inventory:
        raise CatalogError(
            "staged payload inventory mismatch: "
            f"source={source_inventory}, staged={staged_inventory}"
        )
    manifest_bytes = blob_at_path(
        destination_repo,
        staged_root,
        spec.destination.manifest_path,
    )
    manifest = parse_json_object(manifest_bytes, "staged manifest")
    if manifest != spec.manifest(source_inventory):
        raise CatalogError("staged manifest differs from measured source facts")
    blob_at_path(destination_repo, staged_root, spec.entrypoint)
    return StageResult(
        base_commit=base,
        inventory=staged_inventory,
        staged_path_count=len(actual_paths),
    )


def validate_staged(
    spec: MigrationSpec,
    source_repo: Path,
    destination_repo: Path,
    destination_base: str,
) -> StageResult:
    source = ensure_repository(source_repo)
    destination = ensure_repository(destination_repo)
    if source == destination:
        raise CatalogError("source and destination repositories must differ")
    _require_origin(source, spec.source.repository, "source")
    _require_origin(destination, spec.destination.repository, "destination")
    base = _require_base(destination, destination_base)
    source_inventory = validate_source(spec, source)
    expected_paths = _expected_paths(spec, source)
    return _validate_staged(spec, destination, base, source_inventory, expected_paths)


def _remove_exact_target(path: Path) -> None:
    if not os.path.lexists(path):
        return
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    shutil.rmtree(path)


def _reserve_payload(targets: _StageTargets) -> None:
    try:
        targets.payload.mkdir()
    except FileExistsError as error:
        raise CatalogError(f"refusing to overwrite destination path: {targets.payload}") from error
    except OSError as error:
        raise CatalogError(f"cannot reserve destination payload: {error}") from error
    targets.payload_owned = True


def _copy_payload(source: Path, destination: Path) -> None:
    try:
        shutil.copytree(
            source,
            destination,
            copy_function=shutil.copy2,
            dirs_exist_ok=True,
        )
    except OSError as error:
        raise CatalogError(f"cannot copy payload into destination: {error}") from error


def _write_manifest(targets: _StageTargets, content: str) -> None:
    try:
        stream = targets.manifest.open("x", encoding="utf-8", newline="\n")
    except FileExistsError as error:
        raise CatalogError(f"refusing to overwrite destination path: {targets.manifest}") from error
    except OSError as error:
        raise CatalogError(f"cannot create destination manifest: {error}") from error
    targets.manifest_owned = True
    try:
        with stream:
            stream.write(content)
    except OSError as error:
        raise CatalogError(f"cannot write destination manifest: {error}") from error


def _rollback(
    repo: Path,
    base: str,
    spec: MigrationSpec,
    targets: _StageTargets,
) -> None:
    if targets.index_touched:
        run_git(
            repo,
            "reset",
            "--quiet",
            base,
            "--",
            spec.destination.payload_path,
            spec.destination.manifest_path,
        )
    if targets.manifest_owned:
        _remove_exact_target(targets.manifest)
    if targets.payload_owned:
        _remove_exact_target(targets.payload)
    for path in sorted(
        set(targets.created_parents),
        key=lambda item: len(item.parts),
        reverse=True,
    ):
        try:
            path.rmdir()
        except FileNotFoundError:
            continue
        except OSError:
            pass
    staged = run_git(
        repo,
        "diff",
        "--cached",
        "--name-only",
        base,
        "--",
        spec.destination.payload_path,
        spec.destination.manifest_path,
    )
    assert isinstance(staged, str)
    if staged:
        raise CatalogError(f"rollback left staged destination paths:\n{staged.rstrip()}")


def stage(
    spec: MigrationSpec,
    source_repo: Path,
    destination_repo: Path,
    destination_base: str,
) -> StageResult:
    source = ensure_repository(source_repo)
    destination = ensure_repository(destination_repo)
    if source == destination:
        raise CatalogError("source and destination repositories must differ")
    _require_origin(source, spec.source.repository, "source")
    _require_origin(destination, spec.destination.repository, "destination")
    base = _require_base(destination, destination_base)
    payload = _require_safe_absent_target(
        destination,
        base,
        spec.destination.payload_path,
    )
    manifest = _require_safe_absent_target(
        destination,
        base,
        spec.destination.manifest_path,
    )
    require_clean_worktree(destination)
    targets = _StageTargets(
        payload=payload,
        manifest=manifest,
    )
    source_inventory = validate_source(spec, source)
    expected_paths = _expected_paths(spec, source)

    with tempfile.TemporaryDirectory(prefix="ipsw-diff-stage-") as raw_temporary:
        extracted = _archive_payload(spec, source, source_inventory, Path(raw_temporary))
        succeeded = False
        try:
            _ensure_parent_directories(
                destination,
                spec.destination.payload_path,
                targets,
            )
            _reserve_payload(targets)
            _copy_payload(extracted, payload)
            _ensure_parent_directories(
                destination,
                spec.destination.manifest_path,
                targets,
            )
            _write_manifest(targets, canonical_json(spec.manifest(source_inventory)))
            targets.index_touched = True
            run_git(
                destination,
                "add",
                "--force",
                "--",
                spec.destination.payload_path,
                spec.destination.manifest_path,
            )
            result = _validate_staged(
                spec,
                destination,
                base,
                source_inventory,
                expected_paths,
            )
            succeeded = True
            return result
        finally:
            if not succeeded:
                _rollback(
                    destination,
                    base,
                    spec,
                    targets,
                )
