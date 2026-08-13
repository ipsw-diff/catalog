from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from ipsw_diff_catalog.model import CatalogEntry, CatalogError, JsonObject
from ipsw_diff_catalog.release_registry import (
    ReleaseKey,
    ReleaseLabel,
    load_release_labels,
)
from ipsw_diff_catalog.render import load_entries, render, render_readme
from ipsw_diff_catalog.verify import record
from tests.helpers import populate_destination

if TYPE_CHECKING:
    from tests.helpers import Repositories

_EXPECTED_REAL_ENTRIES = 134
_EXPECTED_REAL_RELEASES = 148
_EXPECTED_REAL_BETAS = 80
_EXPECTED_REAL_RCS = 17
_EXPECTED_REAL_FINAL_RELEASES = 51


def _record_fixture(repositories: Repositories, entries: Path) -> None:
    commit = populate_destination(repositories)
    record(
        repositories.spec,
        repositories.source,
        repositories.destination,
        commit,
        entries,
    )


def _entry(  # noqa: PLR0913 - compact catalog-fixture builder
    identifier: str,
    platform: str,
    major: int,
    previous: tuple[str, str],
    following: tuple[str, str],
    *,
    device: str = "Device1,1",
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
        "device": device,
        "from": {
            "version": previous_version,
            "build": previous_build,
            "input": f"{device}_{previous_version}_{previous_build}_Restore.ipsw",
        },
        "to": {
            "version": next_version,
            "build": next_build,
            "input": f"{device}_{next_version}_{next_build}_Restore.ipsw",
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


def _labels(
    entries: tuple[CatalogEntry, ...],
    overrides: dict[ReleaseKey, str] | None = None,
) -> dict[ReleaseKey, ReleaseLabel]:
    labels: dict[ReleaseKey, ReleaseLabel] = {}
    for entry in entries:
        for release in (entry.previous, entry.next):
            key = (entry.platform, release.build)
            display_version = overrides.get(key, release.version) if overrides else release.version
            channel = (
                "beta"
                if " beta" in display_version
                else "rc"
                if " RC" in display_version
                else "release"
            )
            labels[key] = ReleaseLabel(
                platform=entry.platform,
                build=release.build,
                display_version=display_version,
                channel=channel,
                source_path=(
                    f"osFiles/iPadOS/fixture/{release.build}.json"
                    if entry.platform == "iOS" and entry.device.startswith("iPad")
                    else f"osFiles/{entry.platform}/fixture/{release.build}.json"
                ),
            )
    return labels


def _registry_object(entries: tuple[CatalogEntry, ...]) -> JsonObject:
    releases: list[JsonObject] = []
    for (platform, build), label in sorted(_labels(entries).items()):
        releases.append(
            {
                "platform": platform,
                "build": build,
                "display_version": label.display_version,
                "channel": "release",
                "beta": False,
                "rc": False,
                "released": "2026-08-10",
                "source_path": label.source_path,
            }
        )
    return {
        "schema_version": 1,
        "source": {
            "repository": "https://github.com/littlebyteorg/appledb",
            "commit": "d" * 40,
        },
        "releases": releases,
    }


def _write_registry(path: Path, entries: tuple[CatalogEntry, ...]) -> None:
    path.write_text(json.dumps(_registry_object(entries)), encoding="utf-8")


def test_render_is_deterministic_and_check_detects_stale_output(
    repositories: Repositories,
    tmp_path: Path,
) -> None:
    entries = tmp_path / "entries"
    _record_fixture(repositories, entries)
    readme = tmp_path / "README.md"
    catalog = tmp_path / "catalog.json"
    loaded = load_entries(entries)
    registry = tmp_path / "releases.json"
    _write_registry(registry, loaded)
    render(entries, registry, readme, catalog, check=False)
    first_readme = readme.read_bytes()
    first_catalog = catalog.read_bytes()
    render(entries, registry, readme, catalog, check=True)
    render(entries, registry, readme, catalog, check=False)
    assert readme.read_bytes() == first_readme
    assert catalog.read_bytes() == first_catalog

    readme.write_text("stale\n", encoding="utf-8")
    with pytest.raises(CatalogError, match="generated file is stale"):
        render(entries, registry, readme, catalog, check=True)


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


def test_readme_uses_vertical_latest_lists_and_flat_version_groups() -> None:
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
    entries = (
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
    overrides = {
        ("iOS", "24A5305a"): "27.0 beta 5",
        ("iOS", "24A5306a"): "27.0 beta 6",
        ("macOS", "26A5378n"): "27.0 beta 3",
        ("macOS", "26A5388g"): "27.0 beta 4",
    }
    readme = render_readme(entries, _labels(entries, overrides))

    latest = readme.split("## Latest diffs\n", maxsplit=1)[1].split(
        "## Browse all diffs\n", maxsplit=1
    )[0]
    assert "### iOS 27" in latest
    assert "### macOS 27" in latest
    assert "| iOS 27 | macOS 27 |" not in latest
    assert latest.index("diffs/ios-27-5/") < latest.index("diffs/ios-27-4/")
    assert "[27.0 beta 6 (`24A5306a`)](" in latest
    assert "← 27.0 beta 5 (`24A5305a`)" in latest
    assert "[27.0 beta 4 (`26A5388g`)](" in latest
    expected_latest_ios = 3
    assert latest.count("diffs/ios-27-") == expected_latest_ios
    assert "diffs/ios-27-2/" not in latest
    assert "diffs/ios-27-2/" in readme
    assert "diffs/ios-26-old/" not in latest
    expected_groups = 3
    assert readme.count("<details>") == expected_groups
    assert readme.count("</details>") == expected_groups
    ios_27_summary = "<summary><strong>iOS 27</strong> · 6 diffs</summary>"
    assert "### iOS\n\n<details>" in readme
    assert "### macOS\n\n<details>" in readme
    assert ios_27_summary in readme
    assert "<summary><strong>macOS 27</strong> · 1 diff</summary>" in readme
    assert "<summary><strong>iOS 26</strong> · 1 diff</summary>" in readme
    assert readme.index("<summary><strong>iOS 27</strong>") < readme.index(
        "<summary><strong>iOS 26</strong>"
    )
    assert readme.count("| Device | Comparison | Integrity |") == expected_groups
    assert "[27.0 beta 5 (24A5305a) → 27.0 beta 6 (24A5306a)]" in readme


def test_release_registry_rejects_missing_unexpected_and_duplicate_endpoints(
    tmp_path: Path,
) -> None:
    entries = (_entry("ios-27-one", "iOS", 27, ("27.0", "A1"), ("27.0", "A2")),)
    registry_path = tmp_path / "releases.json"

    missing = _registry_object(entries)
    missing_releases = missing["releases"]
    assert isinstance(missing_releases, list)
    missing_releases.pop()
    registry_path.write_text(json.dumps(missing), encoding="utf-8")
    with pytest.raises(CatalogError, match="coverage differs: missing"):
        load_release_labels(registry_path, entries)

    unexpected = _registry_object(entries)
    unexpected_releases = unexpected["releases"]
    assert isinstance(unexpected_releases, list)
    extra = dict(unexpected_releases[0])
    extra["build"] = "A3"
    extra["source_path"] = "osFiles/iOS/fixture/A3.json"
    unexpected_releases.append(extra)
    registry_path.write_text(json.dumps(unexpected), encoding="utf-8")
    with pytest.raises(CatalogError, match=r"unexpected=.*A3"):
        load_release_labels(registry_path, entries)

    duplicate = _registry_object(entries)
    duplicate_releases = duplicate["releases"]
    assert isinstance(duplicate_releases, list)
    duplicate_releases.append(dict(duplicate_releases[0]))
    registry_path.write_text(json.dumps(duplicate), encoding="utf-8")
    with pytest.raises(CatalogError, match="duplicate release registry endpoint"):
        load_release_labels(registry_path, entries)


def test_release_registry_rejects_version_and_channel_conflicts(tmp_path: Path) -> None:
    entries = (_entry("ios-27-one", "iOS", 27, ("27.0", "A1"), ("27.0", "A2")),)
    registry_path = tmp_path / "releases.json"

    wrong_version = _registry_object(entries)
    wrong_releases = wrong_version["releases"]
    assert isinstance(wrong_releases, list)
    wrong_releases[0]["display_version"] = "28.0"
    registry_path.write_text(json.dumps(wrong_version), encoding="utf-8")
    with pytest.raises(CatalogError, match=r"expected base 27\.0"):
        load_release_labels(registry_path, entries)

    wrong_channel = _registry_object(entries)
    channel_releases = wrong_channel["releases"]
    assert isinstance(channel_releases, list)
    channel_releases[0]["channel"] = "beta"
    channel_releases[0]["beta"] = True
    registry_path.write_text(json.dumps(wrong_channel), encoding="utf-8")
    with pytest.raises(CatalogError, match="qualifier conflicts with channel"):
        load_release_labels(registry_path, entries)

    escaped_path = _registry_object(entries)
    escaped_releases = escaped_path["releases"]
    assert isinstance(escaped_releases, list)
    escaped_releases[0]["source_path"] = "osFiles/iOS/../iOS/A1.json"
    registry_path.write_text(json.dumps(escaped_path), encoding="utf-8")
    with pytest.raises(CatalogError, match=r"must identify A1\.json below osFiles/iOS"):
        load_release_labels(registry_path, entries)


def test_release_registry_requires_device_selected_appledb_root(tmp_path: Path) -> None:
    registry_path = tmp_path / "releases.json"

    ipad_entries = (
        _entry(
            "ios-17-ipad",
            "iOS",
            17,
            ("17.7.5", "A1"),
            ("17.7.6", "A2"),
            device="iPad",
        ),
    )
    ipad_registry = _registry_object(ipad_entries)
    registry_path.write_text(json.dumps(ipad_registry), encoding="utf-8")
    labels = load_release_labels(registry_path, ipad_entries)
    assert labels[("iOS", "A1")].source_path.startswith("osFiles/iPadOS/")

    ipad_releases = ipad_registry["releases"]
    assert isinstance(ipad_releases, list)
    ipad_releases[0]["source_path"] = "osFiles/iOS/fixture/A1.json"
    registry_path.write_text(json.dumps(ipad_registry), encoding="utf-8")
    with pytest.raises(CatalogError, match=r"source path must be below osFiles/iPadOS"):
        load_release_labels(registry_path, ipad_entries)

    iphone_entries = (_entry("ios-17-iphone", "iOS", 17, ("17.7.5", "A1"), ("17.7.6", "A2")),)
    iphone_registry = _registry_object(iphone_entries)
    iphone_releases = iphone_registry["releases"]
    assert isinstance(iphone_releases, list)
    iphone_releases[0]["source_path"] = "osFiles/iPadOS/fixture/A1.json"
    registry_path.write_text(json.dumps(iphone_registry), encoding="utf-8")
    with pytest.raises(CatalogError, match=r"source path must be below osFiles/iOS"):
        load_release_labels(registry_path, iphone_entries)


def test_checked_in_release_registry_exactly_covers_the_real_catalog() -> None:
    entries = load_entries(Path("entries"))
    labels = load_release_labels(Path("metadata/releases.json"), entries)

    assert len(entries) == _EXPECTED_REAL_ENTRIES
    assert len(labels) == _EXPECTED_REAL_RELEASES
    assert sum(label.channel == "beta" for label in labels.values()) == _EXPECTED_REAL_BETAS
    assert sum(label.channel == "rc" for label in labels.values()) == _EXPECTED_REAL_RCS
    assert (
        sum(label.channel == "release" for label in labels.values())
        == _EXPECTED_REAL_FINAL_RELEASES
    )
