from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ipsw_diff_catalog.model import CatalogEntry, CatalogError, JsonObject
from ipsw_diff_catalog.render import load_entries, render, render_readme
from ipsw_diff_catalog.verify import record
from tests.helpers import populate_destination

if TYPE_CHECKING:
    from pathlib import Path

    from tests.helpers import Repositories


def _record_fixture(repositories: Repositories, entries: Path) -> None:
    commit = populate_destination(repositories)
    record(
        repositories.spec,
        repositories.source,
        repositories.destination,
        commit,
        entries,
    )


def _entry(
    identifier: str,
    platform: str,
    major: int,
    previous: tuple[str, str],
    following: tuple[str, str],
) -> CatalogEntry:
    previous_version, previous_build = previous
    next_version, next_build = following
    repository_name = platform.lower()
    payload_path = f"diffs/{identifier}"
    value: JsonObject = {
        "schema_version": 1,
        "id": identifier,
        "platform": platform,
        "major_version": major,
        "device": "Device1,1",
        "from": {
            "version": previous_version,
            "build": previous_build,
            "input": f"Device1,1_{previous_version}_{previous_build}_Restore.ipsw",
        },
        "to": {
            "version": next_version,
            "build": next_build,
            "input": f"Device1,1_{next_version}_{next_build}_Restore.ipsw",
        },
        "source": {
            "repository": "https://github.com/example/source",
            "commit": "a" * 40,
            "path": identifier,
        },
        "destination": {
            "repository": f"https://github.com/example/{repository_name}-{major}",
            "commit": "b" * 40,
            "payload_path": payload_path,
            "entrypoint": f"{payload_path}/README.md",
            "manifest_path": f"manifests/{identifier}.json",
        },
        "integrity": {
            "git_tree": "c" * 40,
            "tracked_file_count": 1,
            "logical_bytes": 1,
        },
    }
    return CatalogEntry.from_object(value)


def test_render_is_deterministic_and_check_detects_stale_output(
    repositories: Repositories,
    tmp_path: Path,
) -> None:
    entries = tmp_path / "entries"
    _record_fixture(repositories, entries)
    readme = tmp_path / "README.md"
    catalog = tmp_path / "catalog.json"
    render(entries, readme, catalog, check=False)
    first_readme = readme.read_bytes()
    first_catalog = catalog.read_bytes()
    render(entries, readme, catalog, check=True)
    render(entries, readme, catalog, check=False)
    assert readme.read_bytes() == first_readme
    assert catalog.read_bytes() == first_catalog

    readme.write_text("stale\n", encoding="utf-8")
    with pytest.raises(CatalogError, match="generated file is stale"):
        render(entries, readme, catalog, check=True)


def test_mismatched_entry_filename_is_rejected(
    repositories: Repositories,
    tmp_path: Path,
) -> None:
    entries = tmp_path / "entries"
    _record_fixture(repositories, entries)
    original = next(entries.glob("*.json"))
    (entries / "duplicate.json").write_bytes(original.read_bytes())
    with pytest.raises(CatalogError, match="filename must match id"):
        load_entries(entries)


def test_readme_puts_both_latest_platforms_first_and_collapses_all_groups() -> None:
    ios_entries = tuple(
        _entry(
            f"ios-27-{index}",
            "iOS",
            27,
            ("27.0", f"24A{5300 + index}a"),
            ("27.0", f"24A{5301 + index}a"),
        )
        for index in range(6)
    )
    readme = render_readme(
        (
            *ios_entries,
            _entry("ios-26-old", "iOS", 26, ("26.5", "23F77"), ("26.6", "23G5028e")),
            _entry(
                "macos-27-new",
                "macOS",
                27,
                ("27.0", "26A5378n"),
                ("27.0", "26A5388g"),
            ),
        )
    )

    latest = readme.split("## Latest diffs\n", maxsplit=1)[1].split(
        "## Browse all diffs\n", maxsplit=1
    )[0]
    assert "| iOS 27 | macOS 27 |" in latest
    assert latest.index("diffs/ios-27-5/") < latest.index("diffs/ios-27-4/")
    assert "diffs/ios-27-0/" not in latest
    assert "diffs/ios-27-0/" in readme
    assert "diffs/ios-26-old/" not in latest
    expected_groups = 5
    assert readme.count("<details>") == expected_groups
    assert readme.count("</details>") == expected_groups
    ios_summary = "<summary><strong>iOS</strong> · 7 diffs</summary>"
    ios_27_summary = "<summary><strong>iOS 27</strong> · 6 diffs</summary>"
    assert ios_summary in readme
    assert "<summary><strong>macOS</strong> · 1 diff</summary>" in readme
    assert readme.index("<summary><strong>iOS</strong>") < readme.index(
        "<summary><strong>macOS</strong>"
    )
    assert f"{ios_summary}\n\n<details>\n{ios_27_summary}" in readme
    assert ios_27_summary in readme
    assert "<summary><strong>macOS 27</strong> · 1 diff</summary>" in readme
    assert "<summary><strong>iOS 26</strong> · 1 diff</summary>" in readme
    assert readme.index("<summary><strong>iOS 27</strong>") < readme.index(
        "<summary><strong>iOS 26</strong>"
    )
    expected_tables = 3
    assert readme.count("| Device | Comparison | Integrity |") == expected_tables
