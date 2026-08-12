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
    require_origin,
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


@dataclass(frozen=True)
class StagedPayload:
    identifier: str
    inventory: TreeInventory


@dataclass(frozen=True)
class BatchStageResult:
    base_commit: str
    staged_tree: str
    payloads: tuple[StagedPayload, ...]
    staged_path_count: int

    @property
    def tracked_file_count(self) -> int:
        return sum(payload.inventory.file_count for payload in self.payloads)

    @property
    def logical_bytes(self) -> int:
        return sum(payload.inventory.logical_bytes for payload in self.payloads)


@dataclass
class _StageTargets:
    payload: Path
    manifest: Path
    created_parents: list[Path] = field(default_factory=list)
    payload_owned: bool = False
    manifest_owned: bool = False
    index_touched: bool = False


@dataclass(frozen=True)
class _StageFacts:
    spec: MigrationSpec
    inventory: TreeInventory
    expected_paths: frozenset[str]


@dataclass
class _StageItem:
    facts: _StageFacts
    targets: _StageTargets


@dataclass(frozen=True)
class _StageContext:
    specs: tuple[MigrationSpec, ...]
    source: Path
    destination: Path
    base: str


_STATUS_PATH_OFFSET = 3
_PATH_SUMMARY_LIMIT = 10


def _paths_overlap(first: str, second: str) -> bool:
    return first == second or first.startswith(f"{second}/") or second.startswith(f"{first}/")


def _require_unique(values: tuple[str, ...], label: str) -> None:
    if len(values) != len(set(values)):
        raise CatalogError(f"batch specs must have unique {label}")


def _ordered_specs(
    specs: tuple[MigrationSpec, ...],
    *,
    minimum_count: int,
) -> tuple[MigrationSpec, ...]:
    if len(specs) < minimum_count:
        raise CatalogError(f"batch staging requires at least {minimum_count} specs")
    ordered = tuple(sorted(specs, key=lambda spec: spec.identifier))
    _require_unique(tuple(spec.identifier for spec in ordered), "ids")
    _require_unique(tuple(spec.source.path for spec in ordered), "source paths")
    if len({spec.source.repository for spec in ordered}) != 1:
        raise CatalogError("batch specs must share one source repository")
    if len({spec.source.commit for spec in ordered}) != 1:
        raise CatalogError("batch specs must share one source commit")
    if len({spec.destination.repository for spec in ordered}) != 1:
        raise CatalogError("batch specs must share one destination repository")

    targets = [
        (path, spec.identifier)
        for spec in ordered
        for path in (spec.destination.payload_path, spec.destination.manifest_path)
    ]
    for index, (first, first_identifier) in enumerate(targets):
        for second, second_identifier in targets[index + 1 :]:
            if _paths_overlap(first, second):
                raise CatalogError(
                    "batch destination paths overlap: "
                    f"{first_identifier}:{first} and {second_identifier}:{second}"
                )
    return ordered


def _require_base(repo: Path, revision: str) -> str:
    base = resolve_commit(repo, revision)
    output = run_git(repo, "rev-parse", "--verify", "HEAD^{commit}")
    assert isinstance(output, str)
    head = output.strip()
    if head != base:
        raise CatalogError(f"destination HEAD differs: expected {base}, got {head}")
    return base


def _stage_context(
    specs: tuple[MigrationSpec, ...],
    source_repo: Path,
    destination_repo: Path,
    destination_base: str,
    *,
    minimum_count: int,
) -> _StageContext:
    ordered = _ordered_specs(specs, minimum_count=minimum_count)
    source = ensure_repository(source_repo)
    destination = ensure_repository(destination_repo)
    if source == destination:
        raise CatalogError("source and destination repositories must differ")
    require_origin(source, ordered[0].source.repository, "source")
    require_origin(destination, ordered[0].destination.repository, "destination")
    base = _require_base(destination, destination_base)
    return _StageContext(
        specs=ordered,
        source=source,
        destination=destination,
        base=base,
    )


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


def _load_facts(context: _StageContext) -> tuple[_StageFacts, ...]:
    return tuple(
        _StageFacts(
            spec=spec,
            inventory=validate_source(spec, context.source),
            expected_paths=_expected_paths(spec, context.source),
        )
        for spec in context.specs
    )


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


def _expected_batch_paths(facts: tuple[_StageFacts, ...]) -> frozenset[str]:
    expected = frozenset(path for item in facts for path in item.expected_paths)
    expected_count = sum(len(item.expected_paths) for item in facts)
    if len(expected) != expected_count:
        raise CatalogError("batch expected path sets overlap")
    return expected


def _validate_staged_facts(
    facts: tuple[_StageFacts, ...],
    destination_repo: Path,
    base: str,
    expected_paths: frozenset[str],
) -> BatchStageResult:
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
    payloads: list[StagedPayload] = []
    for item in facts:
        spec = item.spec
        staged_inventory = inventory(
            destination_repo,
            staged_root,
            spec.destination.payload_path,
        )
        if staged_inventory != item.inventory:
            raise CatalogError(
                f"staged payload inventory mismatch for {spec.identifier}: "
                f"source={item.inventory}, staged={staged_inventory}"
            )
        manifest_bytes = blob_at_path(
            destination_repo,
            staged_root,
            spec.destination.manifest_path,
        )
        manifest = parse_json_object(manifest_bytes, f"staged manifest for {spec.identifier}")
        if manifest != spec.manifest(item.inventory):
            raise CatalogError(
                f"staged manifest differs from measured source facts for {spec.identifier}"
            )
        blob_at_path(destination_repo, staged_root, spec.entrypoint)
        payloads.append(StagedPayload(identifier=spec.identifier, inventory=staged_inventory))
    return BatchStageResult(
        base_commit=base,
        staged_tree=staged_root,
        payloads=tuple(payloads),
        staged_path_count=len(actual_paths),
    )


def _validate_specs(
    specs: tuple[MigrationSpec, ...],
    source_repo: Path,
    destination_repo: Path,
    destination_base: str,
    *,
    minimum_count: int,
) -> BatchStageResult:
    context = _stage_context(
        specs,
        source_repo,
        destination_repo,
        destination_base,
        minimum_count=minimum_count,
    )
    facts = _load_facts(context)
    return _validate_staged_facts(
        facts,
        context.destination,
        context.base,
        _expected_batch_paths(facts),
    )


def _single_result(result: BatchStageResult) -> StageResult:
    if len(result.payloads) != 1:
        raise CatalogError("internal single-stage result has multiple payloads")
    return StageResult(
        base_commit=result.base_commit,
        inventory=result.payloads[0].inventory,
        staged_path_count=result.staged_path_count,
    )


def validate_staged(
    spec: MigrationSpec,
    source_repo: Path,
    destination_repo: Path,
    destination_base: str,
) -> StageResult:
    result = _validate_specs(
        (spec,),
        source_repo,
        destination_repo,
        destination_base,
        minimum_count=1,
    )
    return _single_result(result)


def validate_staged_batch(
    specs: tuple[MigrationSpec, ...],
    source_repo: Path,
    destination_repo: Path,
    destination_base: str,
) -> BatchStageResult:
    return _validate_specs(
        specs,
        source_repo,
        destination_repo,
        destination_base,
        minimum_count=2,
    )


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


def _preflight_targets(context: _StageContext) -> tuple[_StageTargets, ...]:
    targets: list[_StageTargets] = []
    for spec in context.specs:
        payload = _require_safe_absent_target(
            context.destination,
            context.base,
            spec.destination.payload_path,
        )
        manifest = _require_safe_absent_target(
            context.destination,
            context.base,
            spec.destination.manifest_path,
        )
        targets.append(_StageTargets(payload=payload, manifest=manifest))
    return tuple(targets)


def _materialize_item(
    item: _StageItem,
    source: Path,
    destination: Path,
) -> None:
    spec = item.facts.spec
    targets = item.targets
    with tempfile.TemporaryDirectory(prefix="ipsw-diff-stage-") as raw_temporary:
        extracted = _archive_payload(
            spec,
            source,
            item.facts.inventory,
            Path(raw_temporary),
        )
        _ensure_parent_directories(destination, spec.destination.payload_path, targets)
        _reserve_payload(targets)
        _copy_payload(extracted, targets.payload)
        _ensure_parent_directories(destination, spec.destination.manifest_path, targets)
        _write_manifest(targets, canonical_json(spec.manifest(item.facts.inventory)))
        targets.index_touched = True
        run_git(
            destination,
            "add",
            "--force",
            "--",
            spec.destination.payload_path,
            spec.destination.manifest_path,
        )


def _rollback_items(
    repo: Path,
    base: str,
    items: tuple[_StageItem, ...],
) -> None:
    target_paths = tuple(
        path
        for item in items
        for path in (
            item.facts.spec.destination.payload_path,
            item.facts.spec.destination.manifest_path,
        )
    )
    if any(item.targets.index_touched for item in items):
        run_git(repo, "reset", "--quiet", base, "--", *target_paths)
    for item in reversed(items):
        if item.targets.manifest_owned:
            _remove_exact_target(item.targets.manifest)
        if item.targets.payload_owned:
            _remove_exact_target(item.targets.payload)
    created_parents = {path for item in items for path in item.targets.created_parents}
    for path in sorted(
        created_parents,
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
        *target_paths,
    )
    assert isinstance(staged, str)
    if staged:
        raise CatalogError(f"rollback left staged destination paths:\n{staged.rstrip()}")


def _stage_specs(
    specs: tuple[MigrationSpec, ...],
    source_repo: Path,
    destination_repo: Path,
    destination_base: str,
    *,
    minimum_count: int,
) -> BatchStageResult:
    context = _stage_context(
        specs,
        source_repo,
        destination_repo,
        destination_base,
        minimum_count=minimum_count,
    )
    targets = _preflight_targets(context)
    require_clean_worktree(context.destination)
    facts = _load_facts(context)
    expected_paths = _expected_batch_paths(facts)
    items = tuple(
        _StageItem(facts=item, targets=target) for item, target in zip(facts, targets, strict=True)
    )
    succeeded = False
    try:
        for item in items:
            _materialize_item(item, context.source, context.destination)
        result = _validate_staged_facts(
            facts,
            context.destination,
            context.base,
            expected_paths,
        )
        succeeded = True
        return result
    finally:
        if not succeeded:
            _rollback_items(context.destination, context.base, items)


def stage(
    spec: MigrationSpec,
    source_repo: Path,
    destination_repo: Path,
    destination_base: str,
) -> StageResult:
    result = _stage_specs(
        (spec,),
        source_repo,
        destination_repo,
        destination_base,
        minimum_count=1,
    )
    return _single_result(result)


def stage_batch(
    specs: tuple[MigrationSpec, ...],
    source_repo: Path,
    destination_repo: Path,
    destination_base: str,
) -> BatchStageResult:
    return _stage_specs(
        specs,
        source_repo,
        destination_repo,
        destination_base,
        minimum_count=2,
    )
