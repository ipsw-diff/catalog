from __future__ import annotations

import json
from dataclasses import dataclass
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


@dataclass(frozen=True)
class _TrackFixture:
    identifier: str
    platform: str
    device: str
    baseline_version: str
    baseline_build: str
    baseline_released: str
    input_prefix: str


_IOS_TRACK = _TrackFixture(
    identifier="ios-27",
    platform="iOS",
    device="iPhone18,1",
    baseline_version="27.0 beta 5",
    baseline_build="24A5408d",
    baseline_released="2026-08-10T00:00:00Z",
    input_prefix="iPhone18,1",
)
_MACOS_TRACK = _TrackFixture(
    identifier="macos-27",
    platform="macOS",
    device="Mac17,6",
    baseline_version="27.0 beta 4",
    baseline_build="26A5388g",
    baseline_released="2026-07-20T00:00:00Z",
    input_prefix="UniversalMac",
)


def _policy_object(track: _TrackFixture = _IOS_TRACK) -> JsonObject:
    return {
        "schema_version": 1,
        "id": track.identifier,
        "platform": track.platform,
        "device": track.device,
        "major_version": 27,
        "baseline": {
            "version": track.baseline_version,
            "build": track.baseline_build,
            "released": track.baseline_released,
            "beta": True,
            "rc": False,
        },
    }


def _manifest_object(
    previous_build: str = "24A5390f",
    next_build: str = "24A5408d",
    *,
    track: _TrackFixture = _IOS_TRACK,
) -> JsonObject:
    return {
        "schema_version": 1,
        "id": f"{track.identifier}.0-{previous_build}-{next_build}",
        "platform": track.platform,
        "major_version": 27,
        "device": track.device,
        "from": {
            "version": "27.0",
            "build": previous_build,
            "input": f"{track.input_prefix}_27.0_{previous_build}_Restore.ipsw",
        },
        "to": {
            "version": "27.0",
            "build": next_build,
            "input": f"{track.input_prefix}_27.0_{next_build}_Restore.ipsw",
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


def _write_track(
    tmp_path: Path,
    *,
    policy: JsonObject | None = None,
    manifest: JsonObject | None = None,
) -> tuple[Path, Path]:
    policy_path = tmp_path / "track.json"
    policy_path.write_text(
        json.dumps(policy if policy is not None else _policy_object()),
        encoding="utf-8",
    )
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    (manifests_dir / "baseline.json").write_text(
        json.dumps(manifest if manifest is not None else _manifest_object()),
        encoding="utf-8",
    )
    return policy_path, manifests_dir


def _latest(
    *,
    platform: str = "iOS",
    version: str = "27.0 beta 5",
    build: str = "24A5408d",
    released: str = "2026-08-10T00:00:00Z",
) -> AppleDBRelease:
    return AppleDBRelease.from_json(
        json.dumps(
            {
                "OS": platform,
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


def test_discover_accepts_boundary_manifest_routed_by_destination_major(
    tmp_path: Path,
) -> None:
    manifest = _manifest_object("23F77", "24A5408d")
    manifest["from"] = {
        "version": "26.5",
        "build": "23F77",
        "input": "iPhone18,1_26.5_23F77_Restore.ipsw",
    }
    policy_path, manifests_dir = _write_track(tmp_path, manifest=manifest)

    decision = discover(TrackPolicy.from_path(policy_path), _latest(), manifests_dir)

    assert decision.status == "current"


def test_discover_rejects_manifest_destination_outside_track_major(tmp_path: Path) -> None:
    manifest = _manifest_object()
    manifest["to"] = {
        "version": "26.5",
        "build": "24A5408d",
        "input": "iPhone18,1_26.5_24A5408d_Restore.ipsw",
    }
    policy_path, manifests_dir = _write_track(tmp_path, manifest=manifest)

    with pytest.raises(CatalogError, match="to version differs from track major"):
        discover(TrackPolicy.from_path(policy_path), _latest(), manifests_dir)


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

    with pytest.raises(CatalogError, match="not newer than baseline"):
        discover(
            TrackPolicy.from_path(policy_path),
            _latest(build="24A5399z", released="2026-08-09T00:00:00Z"),
            manifests_dir,
        )


def test_discover_rejects_different_build_on_same_date(tmp_path: Path) -> None:
    policy_path, manifests_dir = _write_track(tmp_path)

    with pytest.raises(CatalogError, match="not newer than baseline"):
        discover(
            TrackPolicy.from_path(policy_path),
            _latest(build="24A5409a"),
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


@pytest.mark.parametrize(
    "policy",
    [
        _policy_object(),
        _policy_object(_MACOS_TRACK),
    ],
)
def test_policy_accepts_only_reviewed_tracks(policy: JsonObject) -> None:
    assert TrackPolicy.from_object(policy).identifier == policy["id"]


@pytest.mark.parametrize(
    ("identifier", "platform", "major_version"),
    [
        ("ios-27", "macOS", 27),
        ("macos-27", "iOS", 27),
        ("ios-28", "iOS", 28),
    ],
)
def test_policy_rejects_unsupported_track_tuples(
    identifier: str,
    platform: str,
    major_version: int,
) -> None:
    policy = _policy_object()
    policy["id"] = identifier
    policy["platform"] = platform
    policy["major_version"] = major_version

    with pytest.raises(CatalogError, match="track policy must be exactly"):
        TrackPolicy.from_object(policy)


def test_discover_reports_macos_forward_candidate(tmp_path: Path) -> None:
    policy = _policy_object(_MACOS_TRACK)
    manifest = _manifest_object(
        "26A5378n",
        "26A5388g",
        track=_MACOS_TRACK,
    )
    policy_path, manifests_dir = _write_track(
        tmp_path,
        policy=policy,
        manifest=manifest,
    )

    decision = discover(
        TrackPolicy.from_path(policy_path),
        _latest(
            platform="macOS",
            version="27.0 beta 5",
            build="26A5406e",
            released="2026-08-10T00:00:00Z",
        ),
        manifests_dir,
    )

    assert decision.to_object() == {
        "schema_version": 1,
        "track_id": "macos-27",
        "status": "candidate",
        "platform": "macOS",
        "device": "Mac17,6",
        "major_version": 27,
        "baseline": {
            "version": "27.0 beta 4",
            "build": "26A5388g",
            "released": "2026-07-20T00:00:00Z",
            "beta": True,
            "rc": False,
        },
        "latest": {
            "version": "27.0 beta 5",
            "build": "26A5406e",
            "released": "2026-08-10T00:00:00Z",
            "beta": True,
            "rc": False,
        },
    }


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


def test_live_query_passes_only_the_reviewed_macos_selector(tmp_path: Path) -> None:
    policy = _policy_object(_MACOS_TRACK)
    manifest = _manifest_object(
        "26A5378n",
        "26A5388g",
        track=_MACOS_TRACK,
    )
    policy_path, manifests_dir = _write_track(
        tmp_path,
        policy=policy,
        manifest=manifest,
    )
    fake_ipsw = tmp_path / "ipsw"
    latest = json.dumps(
        {
            "OS": "macOS",
            "version": "27.0 beta 5",
            "build": "26A5406e",
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
        'test "$4" = macOS || exit 68\n'
        'test "$5" = --device || exit 69\n'
        'test "$6" = Mac17,6 || exit 70\n'
        'test "$7" = --version || exit 71\n'
        'test "$8" = 27. || exit 72\n'
        'test "$9" = --show-latest || exit 73\n'
        'test "${10}" = --no-color || exit 74\n'
        f"printf '%s\\n' '{latest}'\n",
        encoding="utf-8",
    )
    fake_ipsw.chmod(0o755)

    decision = discover_live(policy_path, manifests_dir, fake_ipsw)

    assert decision.status == "candidate"
