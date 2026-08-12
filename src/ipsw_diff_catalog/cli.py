from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ipsw_diff_catalog.audit import audit
from ipsw_diff_catalog.model import CatalogError, MigrationSpec
from ipsw_diff_catalog.render import render
from ipsw_diff_catalog.stage import stage, validate_staged
from ipsw_diff_catalog.verify import record, verify


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ipsw-diff-catalog",
        description="Integrity-first catalog tooling for ipsw-diff shards.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    verify_parser = commands.add_parser("verify", help="verify source and destination commits")
    _add_spec_and_repositories(verify_parser, destination=True)
    verify_parser.add_argument("--destination-revision", required=True)

    record_parser = commands.add_parser("record", help="verify and write one catalog entry")
    _add_spec_and_repositories(record_parser, destination=True)
    record_parser.add_argument("--destination-revision", required=True)
    record_parser.add_argument("--entries-dir", type=Path, default=Path("entries"))

    stage_parser = commands.add_parser(
        "stage",
        help="materialize and verify one source subtree in a clean shard worktree",
    )
    _add_spec_and_repositories(stage_parser, destination=True)
    stage_parser.add_argument("--destination-base", required=True)

    staged_parser = commands.add_parser(
        "validate-staged",
        help="re-verify a staged migration without modifying it",
    )
    _add_spec_and_repositories(staged_parser, destination=True)
    staged_parser.add_argument("--destination-base", required=True)

    render_parser = commands.add_parser("render", help="render deterministic catalog outputs")
    render_parser.add_argument("--entries-dir", type=Path, default=Path("entries"))
    render_parser.add_argument("--readme", type=Path, default=Path("README.md"))
    render_parser.add_argument("--catalog", type=Path, default=Path("catalog.json"))
    render_parser.add_argument("--check", action="store_true")

    audit_parser = commands.add_parser(
        "audit",
        help="fetch every immutable source and destination and re-run verification",
    )
    audit_parser.add_argument("--entries-dir", type=Path, default=Path("entries"))
    audit_parser.add_argument("--specs-dir", type=Path, default=Path("specs"))
    return parser


def _add_spec_and_repositories(parser: argparse.ArgumentParser, *, destination: bool) -> None:
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--source-repo", type=Path, required=True)
    if destination:
        parser.add_argument("--destination-repo", type=Path, required=True)


def _run(arguments: argparse.Namespace) -> None:
    if arguments.command == "audit":
        count = audit(arguments.entries_dir, arguments.specs_dir)
        print(f"Audited {count} catalog entr{'y' if count == 1 else 'ies'}")
        return
    if arguments.command == "render":
        render(arguments.entries_dir, arguments.readme, arguments.catalog, check=arguments.check)
        print(
            f"{'Checked' if arguments.check else 'Rendered'} "
            f"{arguments.readme} and {arguments.catalog}"
        )
        return

    spec = MigrationSpec.from_path(arguments.spec)
    if arguments.command == "verify":
        result = verify(
            spec,
            arguments.source_repo,
            arguments.destination_repo,
            arguments.destination_revision,
        )
        print(
            f"Verified {spec.identifier}: tree={result.source.tree} "
            f"files={result.source.file_count} bytes={result.source.logical_bytes} "
            f"destination_commit={result.destination_commit}"
        )
        return
    if arguments.command == "record":
        path = record(
            spec,
            arguments.source_repo,
            arguments.destination_repo,
            arguments.destination_revision,
            arguments.entries_dir,
        )
        print(f"Recorded {path}")
        return
    if arguments.command in {"stage", "validate-staged"}:
        operation = stage if arguments.command == "stage" else validate_staged
        result = operation(
            spec,
            arguments.source_repo,
            arguments.destination_repo,
            arguments.destination_base,
        )
        verb = "Staged" if arguments.command == "stage" else "Validated staged"
        print(
            f"{verb} {spec.identifier}: tree={result.inventory.tree} "
            f"files={result.inventory.file_count} bytes={result.inventory.logical_bytes} "
            f"paths={result.staged_path_count} base={result.base_commit}"
        )
        return
    raise CatalogError(f"unsupported command: {arguments.command}")


def main() -> None:
    try:
        _run(_parser().parse_args())
    except CatalogError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
