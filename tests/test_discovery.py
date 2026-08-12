from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from ipsw_diff_catalog.discovery import (
    AppleDBRelease,
    TrackPolicy,
    discover,
    discover_live,
)
from ipsw_diff_catalog.model import CatalogError, JsonObject

if TYPE_CHECKING:
    from pathlib import Path


def _policy_object() -> JsonObject:
    return {
        "schema_version": 1,
        "id": "ios-27",
        "platform": "iOS",
        "device": "iPhone18,1",
        "major_version": 27,
        "baseline": {
            "version": "27.0 beta 5",
            "build": "24A5408d",
            "released": "2026-08-10T00:00:00Z",
            "beta": True,
            "rc": False,
        },
    }


def _manifest_object(
    previous_build: str = "24A5390f",
    next_build: str = "24A5408d",
) -> JsonObject:
    return {
        "schema_version": 1,
        "id": f"ios-27.0-{previous_build}-{next_build}",
        "platform": "iOS",
        "major_version": 27,
        "device": "iPhone18,1",
        "from": {
            "version": "27.0",
            "build": previous_build,
            "input": f"iPhone18,1_27.0_{previous_build}_Restore.ipsw",
        },
        "to": {
            "version": "27.0",
            "build": next_build,
            "input": f"iPhone18,1_27.0_{next_build}_Restore.ipsw",
        },
        "payload": {
            "path": "diffs/example",
            "entrypoint": "diffs/example/README.md",
            "tracked_file_count": 1,
            "logical_bytes": 1,
            "git_tree": "0" * 40,
        },
        "source": {
            "repository": "https://github.com/example/source",
            "commit": "0" * 40,
            "path": "example",
        },
    }


def _write_track(tmp_path: Path) -> tuple[Path, Path]:
    policy_path = tmp_path / "track.json"
    policy_path.write_text(json.dumps(_policy_object()), encoding="utf-8")
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    (manifests_dir / "baseline.json").write_text(
        json.dumps(_manifest_object()),
        encoding="utf-8",
    )
    return policy_path, manifests_dir


def _latest(
    *,
    version: str = "27.0 beta 5",
    build: str = "24A5408d",
    released: str = "2026-08-10T00:00:00Z",
) -> AppleDBRelease:
    return AppleDBRelease.from_json(
        json.dumps(
            {
                "OS": "iOS",
                "version": version,
                "build": build,
                "beta": True,
                "released": released,
            }
        )
    )


def test_discover_reports_current_baseline(tmp_path: Path) -> None:
    policy_path, manifests_dir = _write_track(tmp_path)

    decision = discover(TrackPolicy.from_path(policy_path), _latest(), manifests_dir)

    assert decision.to_object() == {
        "schema_version": 1,
        "track_id": "ios-27",
        "status": "current",
        "platform": "iOS",
        "device": "iPhone18,1",
        "major_version": 27,
        "baseline": {
            "version": "27.0 beta 5",
            "build": "24A5408d",
            "released": "2026-08-10T00:00:00Z",
            "beta": True,
            "rc": False,
        },
        "latest": {
            "version": "27.0 beta 5",
            "build": "24A5408d",
            "released": "2026-08-10T00:00:00Z",
            "beta": True,
            "rc": False,
        },
    }


def test_discover_reports_same_major_forward_candidate(tmp_path: Path) -> None:
    policy_path, manifests_dir = _write_track(tmp_path)

    decision = discover(
        TrackPolicy.from_path(policy_path),
        _latest(
            version="27.0 beta 6",
            build="24A5412a",
            released="2026-08-17T00:00:00Z",
        ),
        manifests_dir,
    )

    assert decision.status == "candidate"
    assert decision.latest.build == "24A5412a"


def test_discover_rejects_wrong_major(tmp_path: Path) -> None:
    policy_path, manifests_dir = _write_track(tmp_path)

    with pytest.raises(CatalogError, match="latest version major must be exactly 27"):
        discover(
            TrackPolicy.from_path(policy_path),
            _latest(version="28.0 beta", build="25A100", released="2027-06-01T00:00:00Z"),
            manifests_dir,
        )


def test_discover_rejects_wrong_platform(tmp_path: Path) -> None:
    policy_path, manifests_dir = _write_track(tmp_path)
    latest = _latest()
    wrong_platform = AppleDBRelease(
        version=latest.version,
        build=latest.build,
        released=latest.released,
        beta=latest.beta,
        rc=latest.rc,
        platform="macOS",
    )

    with pytest.raises(CatalogError, match="expected exactly iOS"):
        discover(TrackPolicy.from_path(policy_path), wrong_platform, manifests_dir)


def test_discover_rejects_backward_release(tmp_path: Path) -> None:
    policy_path, manifests_dir = _write_track(tmp_path)

    with pytest.raises(CatalogError, match="older than baseline"):
        discover(
            TrackPolicy.from_path(policy_path),
            _latest(build="24A5399z", released="2026-08-09T00:00:00Z"),
            manifests_dir,
        )


def test_discover_rejects_policy_baseline_that_is_not_terminal(tmp_path: Path) -> None:
    policy_path, manifests_dir = _write_track(tmp_path)
    (manifests_dir / "later.json").write_text(
        json.dumps(_manifest_object("24A5408d", "24A5412a")),
        encoding="utf-8",
    )

    with pytest.raises(CatalogError, match="terminal manifest build is 24A5412a"):
        discover(TrackPolicy.from_path(policy_path), _latest(), manifests_dir)


def test_discover_rejects_disconnected_manifest_cycle(tmp_path: Path) -> None:
    policy_path, manifests_dir = _write_track(tmp_path)
    (manifests_dir / "cycle-a.json").write_text(
        json.dumps(_manifest_object("24A5300a", "24A5301a")),
        encoding="utf-8",
    )
    (manifests_dir / "cycle-b.json").write_text(
        json.dumps(_manifest_object("24A5301a", "24A5300a")),
        encoding="utf-8",
    )

    with pytest.raises(CatalogError, match="one connected chain"):
        discover(TrackPolicy.from_path(policy_path), _latest(), manifests_dir)


@pytest.mark.parametrize(
    "raw",
    [
        '{"OS":"iOS","version":"27.0","build":"A1","released":"2026-08-10T00:00:00Z","extra":true}',
        '{"OS":"iOS","version":"27.0","build":"A1","build":"A2","released":"2026-08-10T00:00:00Z"}',
        '[{"OS":"iOS"}]',
    ],
)
def test_appledb_result_rejects_ambiguous_shape(raw: str) -> None:
    with pytest.raises(CatalogError):
        AppleDBRelease.from_json(raw)


def test_policy_is_exactly_ios_27() -> None:
    policy = _policy_object()
    policy["platform"] = "macOS"

    with pytest.raises(CatalogError, match="platform must be exactly iOS"):
        TrackPolicy.from_object(policy)


def test_live_query_passes_only_the_reviewed_selector(tmp_path: Path) -> None:
    policy_path, manifests_dir = _write_track(tmp_path)
    fake_ipsw = tmp_path / "ipsw"
    latest = json.dumps(
        {
            "OS": "iOS",
            "version": "27.0 beta 5",
            "build": "24A5408d",
            "beta": True,
            "released": "2026-08-10T00:00:00Z",
        },
        separators=(",", ":"),
    )
    fake_ipsw.write_text(
        "#!/bin/sh\n"
        'test "$#" -eq 10 || exit 64\n'
        'test "$1" = dl || exit 65\n'
        'test "$2" = appledb || exit 66\n'
        'test "$3" = --os || exit 67\n'
        'test "$4" = iOS || exit 68\n'
        'test "$5" = --device || exit 69\n'
        'test "$6" = iPhone18,1 || exit 70\n'
        'test "$7" = --version || exit 71\n'
        'test "$8" = 27. || exit 72\n'
        'test "$9" = --show-latest || exit 73\n'
        'test "${10}" = --no-color || exit 74\n'
        f"printf '%s\\n' '{latest}'\n",
        encoding="utf-8",
    )
    fake_ipsw.chmod(0o755)

    decision = discover_live(policy_path, manifests_dir, fake_ipsw)

    assert decision.status == "current"
