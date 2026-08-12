from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ipsw_diff_catalog.model import CatalogError, TreeIdentity, TreeInventory

_FULL_OID = re.compile(r"[0-9a-f]{40}")


@dataclass(frozen=True)
class TreeEntry:
    mode: str
    oid: str
    size: int
    path: str


def run_git(repo: Path, *arguments: str, text: bool = True) -> str | bytes:
    command = ["git", "-C", os.fspath(repo), *arguments]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=text)  # noqa: S603
    except (OSError, subprocess.CalledProcessError) as error:
        detail = ""
        if isinstance(error, subprocess.CalledProcessError):
            stderr = error.stderr
            detail = (
                stderr.strip()
                if isinstance(stderr, str)
                else stderr.decode(errors="replace").strip()
            )
        suffix = f": {detail}" if detail else ""
        raise CatalogError(f"git command failed ({' '.join(arguments)}){suffix}") from error
    return result.stdout


def ensure_repository(repo: Path) -> Path:
    resolved = repo.resolve()
    output = run_git(resolved, "rev-parse", "--show-toplevel")
    assert isinstance(output, str)
    top = Path(output.strip()).resolve()
    if top != resolved:
        raise CatalogError(f"{repo} is not the root of its Git worktree")
    object_format = run_git(resolved, "rev-parse", "--show-object-format")
    assert isinstance(object_format, str)
    if object_format.strip() != "sha1":
        raise CatalogError("only SHA-1 Git repositories are currently supported")
    return resolved


def resolve_commit(repo: Path, revision: str) -> str:
    if _FULL_OID.fullmatch(revision) is None:
        raise CatalogError("commit must be a full lowercase SHA-1 object ID")
    output = run_git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}")
    assert isinstance(output, str)
    return output.strip()


def require_clean_worktree(repo: Path) -> None:
    output = run_git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    assert isinstance(output, str)
    if output:
        raise CatalogError(f"destination worktree is not clean:\n{output.rstrip()}")


def require_origin(repo: Path, expected: str, context: str) -> None:
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


def _parse_tree_entries(
    output: bytes,
    context: str,
    prefix: str | None,
) -> tuple[TreeEntry, ...]:
    entries: list[TreeEntry] = []
    for raw in output.split(b"\0"):
        if not raw:
            continue
        try:
            metadata, raw_path = raw.split(b"\t", 1)
            mode, kind, oid, raw_size = metadata.decode("ascii").split()
            entry_path = raw_path.decode("utf-8")
            size = int(raw_size)
        except (UnicodeDecodeError, ValueError) as error:
            raise CatalogError(f"cannot parse Git tree entry for {context}") from error
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise CatalogError(f"unsupported Git entry for {context}: {mode} {kind} {entry_path}")
        if prefix is not None and not entry_path.startswith(prefix):
            raise CatalogError(f"Git returned an entry outside {context}: {entry_path}")
        entries.append(TreeEntry(mode=mode, oid=oid, size=size, path=entry_path))
    if not entries:
        raise CatalogError(f"no tracked files found for {context}")
    return tuple(entries)


def tracked_entries(repo: Path, revision: str) -> tuple[TreeEntry, ...]:
    output = run_git(repo, "ls-tree", "-r", "-z", "-l", revision, text=False)
    assert isinstance(output, bytes)
    return _parse_tree_entries(output, f"repository at {revision}", None)


def tree_entries(repo: Path, revision: str, path: str) -> tuple[TreeEntry, ...]:
    output = run_git(repo, "ls-tree", "-r", "-z", "-l", revision, "--", path, text=False)
    assert isinstance(output, bytes)
    return _parse_tree_entries(output, f"{path} at {revision}", f"{path}/")


def root_tree_oid(repo: Path, revision: str) -> str:
    output = run_git(repo, "rev-parse", "--verify", f"{revision}^{{tree}}")
    assert isinstance(output, str)
    oid = output.strip()
    if _FULL_OID.fullmatch(oid) is None:
        raise CatalogError(f"Git returned an invalid root tree object ID for {revision}")
    return oid


def tree_oid(repo: Path, revision: str, path: str) -> str:
    output = run_git(repo, "ls-tree", "-z", "-d", revision, "--", path, text=False)
    assert isinstance(output, bytes)
    records = [record for record in output.split(b"\0") if record]
    if len(records) != 1:
        raise CatalogError(f"expected one tree at {path}, found {len(records)}")
    try:
        metadata, raw_path = records[0].split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split()
        returned_path = raw_path.decode("utf-8")
    except (UnicodeDecodeError, ValueError) as error:
        raise CatalogError(f"cannot parse Git tree for {path}") from error
    if mode != "040000" or kind != "tree" or returned_path != path:
        raise CatalogError(f"{path} is not an exact Git tree at {revision}")
    return oid


def inventory(repo: Path, revision: str, path: str) -> TreeInventory:
    entries = tree_entries(repo, revision, path)
    return TreeInventory(
        tree=tree_oid(repo, revision, path),
        file_count=len(entries),
        logical_bytes=sum(entry.size for entry in entries),
        modes=frozenset(entry.mode for entry in entries),
    )


def identity(repo: Path, revision: str, path: str) -> TreeIdentity:
    output = run_git(repo, "ls-tree", "-r", "-z", revision, "--", path, text=False)
    assert isinstance(output, bytes)
    prefix = f"{path}/"
    count = 0
    modes: set[str] = set()
    for raw in output.split(b"\0"):
        if not raw:
            continue
        try:
            metadata, raw_path = raw.split(b"\t", 1)
            mode, kind, _oid = metadata.decode("ascii").split()
            entry_path = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as error:
            raise CatalogError(f"cannot parse Git tree entry below {path}") from error
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise CatalogError(f"unsupported Git entry below {path}: {mode} {kind} {entry_path}")
        if not entry_path.startswith(prefix):
            raise CatalogError(f"Git returned an entry outside {path}: {entry_path}")
        count += 1
        modes.add(mode)
    if count == 0:
        raise CatalogError(f"no tracked files found below {path} at {revision}")
    return TreeIdentity(
        tree=tree_oid(repo, revision, path),
        file_count=count,
        modes=frozenset(modes),
    )


def blob_at_path(repo: Path, revision: str, path: str) -> bytes:
    output = run_git(repo, "ls-tree", "-z", revision, "--", path, text=False)
    assert isinstance(output, bytes)
    records = [record for record in output.split(b"\0") if record]
    if len(records) != 1:
        raise CatalogError(f"expected one blob at {path}, found {len(records)}")
    try:
        metadata, raw_path = records[0].split(b"\t", 1)
        _mode, kind, oid = metadata.decode("ascii").split()
        returned_path = raw_path.decode("utf-8")
    except (UnicodeDecodeError, ValueError) as error:
        raise CatalogError(f"cannot parse Git blob for {path}") from error
    if kind != "blob" or returned_path != path:
        raise CatalogError(f"{path} is not an exact Git blob at {revision}")
    data = run_git(repo, "cat-file", "blob", oid, text=False)
    assert isinstance(data, bytes)
    return data
