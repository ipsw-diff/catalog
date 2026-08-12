from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal, cast

from ipsw_diff_catalog.model import (
    CatalogError,
    JsonObject,
    parse_json_object,
    read_json_object,
)

if TYPE_CHECKING:
    from pathlib import Path

_IDENTIFIER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_VERSION = re.compile(r"[0-9]+(?:\.[0-9]+)*(?: [A-Za-z0-9]+)*")
_BUILD = re.compile(r"[A-Za-z0-9]+")
_DEVICE = re.compile(r"[A-Za-z0-9][A-Za-z0-9,._-]*")
_RELEASED = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
_TRACK_MAJOR = 27


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


def _string(value: object, context: str, pattern: re.Pattern[str]) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise CatalogError(f"{context} has an unsupported value")
    return value


def _integer(value: object, context: str) -> int:
    if type(value) is not int or value <= 0:
        raise CatalogError(f"{context} must be a positive integer")
    return value


def _boolean(value: object, context: str) -> bool:
    if type(value) is not bool:
        raise CatalogError(f"{context} must be a boolean")
    return value


def _major(version: str, context: str) -> int:
    match = re.match(r"([0-9]+)(?:\.|$)", version)
    if match is None:
        raise CatalogError(f"{context} has no numeric major")
    return int(match.group(1))


def _released(value: object, context: str) -> str:
    released = _string(value, context, _RELEASED)
    try:
        datetime.strptime(released, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError as error:
        raise CatalogError(f"{context} is not a valid UTC timestamp") from error
    return released


@dataclass(frozen=True)
class ReleaseMetadata:
    version: str
    build: str
    released: str
    beta: bool
    rc: bool

    @classmethod
    def from_object(cls, value: object, context: str) -> ReleaseMetadata:
        data = _object(value, context)
        _exact_keys(data, {"version", "build", "released", "beta", "rc"}, context)
        release = cls(
            version=_string(data["version"], f"{context}.version", _VERSION),
            build=_string(data["build"], f"{context}.build", _BUILD),
            released=_released(data["released"], f"{context}.released"),
            beta=_boolean(data["beta"], f"{context}.beta"),
            rc=_boolean(data["rc"], f"{context}.rc"),
        )
        if release.beta and release.rc:
            raise CatalogError(f"{context} cannot be both beta and RC")
        return release

    @property
    def released_at(self) -> datetime:
        return datetime.strptime(self.released, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)

    def to_object(self) -> JsonObject:
        return {
            "version": self.version,
            "build": self.build,
            "released": self.released,
            "beta": self.beta,
            "rc": self.rc,
        }


@dataclass(frozen=True)
class AppleDBRelease(ReleaseMetadata):
    platform: str

    @classmethod
    def from_json(cls, raw: str | bytes) -> AppleDBRelease:
        data = parse_json_object(raw, "AppleDB result")
        required = {"OS", "version", "build", "released"}
        allowed = required | {"beta", "rc"}
        actual = set(data)
        if not required <= actual or not actual <= allowed:
            raise CatalogError(
                "AppleDB result keys differ: "
                f"missing={sorted(required - actual)}, extra={sorted(actual - allowed)}"
            )
        normalized: JsonObject = {
            "version": data["version"],
            "build": data["build"],
            "released": data["released"],
            "beta": data.get("beta", False),
            "rc": data.get("rc", False),
        }
        release = ReleaseMetadata.from_object(normalized, "AppleDB result")
        return cls(
            version=release.version,
            build=release.build,
            released=release.released,
            beta=release.beta,
            rc=release.rc,
            platform=_string(data["OS"], "AppleDB result.OS", re.compile(r"[A-Za-z]+")),
        )

    @property
    def metadata(self) -> ReleaseMetadata:
        return ReleaseMetadata(
            version=self.version,
            build=self.build,
            released=self.released,
            beta=self.beta,
            rc=self.rc,
        )


@dataclass(frozen=True)
class TrackPolicy:
    identifier: str
    platform: str
    device: str
    major_version: int
    baseline: ReleaseMetadata

    @classmethod
    def from_object(cls, value: JsonObject) -> TrackPolicy:
        _exact_keys(
            value,
            {"schema_version", "id", "platform", "device", "major_version", "baseline"},
            "track policy",
        )
        if _integer(value["schema_version"], "track policy.schema_version") != 1:
            raise CatalogError("track policy.schema_version must be 1")
        policy = cls(
            identifier=_string(value["id"], "track policy.id", _IDENTIFIER),
            platform=_string(value["platform"], "track policy.platform", re.compile(r"[A-Za-z]+")),
            device=_string(value["device"], "track policy.device", _DEVICE),
            major_version=_integer(value["major_version"], "track policy.major_version"),
            baseline=ReleaseMetadata.from_object(value["baseline"], "track policy.baseline"),
        )
        if policy.platform != "iOS":
            raise CatalogError("track policy.platform must be exactly iOS")
        if policy.major_version != _TRACK_MAJOR:
            raise CatalogError("track policy.major_version must be exactly 27")
        if policy.identifier != "ios-27":
            raise CatalogError("track policy.id must be exactly ios-27")
        if _major(policy.baseline.version, "track policy.baseline.version") != _TRACK_MAJOR:
            raise CatalogError("track policy baseline version major must be exactly 27")
        return policy

    @classmethod
    def from_path(cls, path: Path) -> TrackPolicy:
        return cls.from_object(read_json_object(path))


@dataclass(frozen=True)
class DiscoveryDecision:
    track_id: str
    status: Literal["current", "candidate"]
    platform: str
    device: str
    major_version: int
    baseline: ReleaseMetadata
    latest: ReleaseMetadata

    def to_object(self) -> JsonObject:
        return {
            "schema_version": 1,
            "track_id": self.track_id,
            "status": self.status,
            "platform": self.platform,
            "device": self.device,
            "major_version": self.major_version,
            "baseline": self.baseline.to_object(),
            "latest": self.latest.to_object(),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_object(), ensure_ascii=False, separators=(",", ":"), sort_keys=True
        )


def _manifest_edge(path: Path, policy: TrackPolicy) -> tuple[str, str]:
    data = read_json_object(path)
    _exact_keys(
        data,
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
        str(path),
    )
    if data["schema_version"] != 1:
        raise CatalogError(f"{path} schema_version must be 1")
    if data["platform"] != policy.platform:
        raise CatalogError(f"{path} platform differs from track policy")
    if data["major_version"] != policy.major_version:
        raise CatalogError(f"{path} major_version differs from track policy")
    if data["device"] != policy.device:
        raise CatalogError(f"{path} device differs from track policy")

    builds: list[str] = []
    for name in ("from", "to"):
        release = _object(data[name], f"{path} {name}")
        _exact_keys(release, {"version", "build", "input"}, f"{path} {name}")
        version = _string(release["version"], f"{path} {name}.version", _VERSION)
        if _major(version, f"{path} {name}.version") != policy.major_version:
            raise CatalogError(f"{path} {name} version differs from track major")
        builds.append(_string(release["build"], f"{path} {name}.build", _BUILD))
    if builds[0] == builds[1]:
        raise CatalogError(f"{path} cannot diff a build against itself")
    return builds[0], builds[1]


def _manifest_edges(
    paths: list[Path],
    policy: TrackPolicy,
) -> tuple[tuple[str, str], ...]:
    edges: list[tuple[str, str]] = []
    from_builds: set[str] = set()
    to_builds: set[str] = set()
    for path in paths:
        previous, next_build = _manifest_edge(path, policy)
        if previous in from_builds:
            raise CatalogError(f"manifest chain branches from build {previous}")
        if next_build in to_builds:
            raise CatalogError(f"multiple manifests end at build {next_build}")
        from_builds.add(previous)
        to_builds.add(next_build)
        edges.append((previous, next_build))
    return tuple(edges)


def _known_builds(manifests_dir: Path, policy: TrackPolicy) -> frozenset[str]:
    try:
        paths = sorted(manifests_dir.glob("*.json"))
    except OSError as error:
        raise CatalogError(f"cannot list manifests in {manifests_dir}: {error}") from error
    if not paths:
        raise CatalogError(f"no manifests found in {manifests_dir}")

    edges = _manifest_edges(paths, policy)
    from_builds = {previous for previous, _next in edges}
    to_builds = {next_build for _previous, next_build in edges}
    predecessors = {next_build: previous for previous, next_build in edges}

    terminals = to_builds - from_builds
    if len(terminals) != 1:
        raise CatalogError(
            f"manifest chain must have one terminal build, found {sorted(terminals)}"
        )
    terminal = terminals.pop()
    if terminal != policy.baseline.build:
        raise CatalogError(
            f"terminal manifest build is {terminal}, not policy baseline {policy.baseline.build}"
        )
    visited_edges: set[str] = set()
    cursor = terminal
    while cursor in predecessors:
        if cursor in visited_edges:
            raise CatalogError("manifest chain contains a cycle")
        visited_edges.add(cursor)
        cursor = predecessors[cursor]
    if len(visited_edges) != len(paths):
        raise CatalogError("manifests do not form one connected chain")
    return frozenset(from_builds | to_builds)


def discover(
    policy: TrackPolicy,
    latest: AppleDBRelease,
    manifests_dir: Path,
) -> DiscoveryDecision:
    if latest.platform != policy.platform:
        raise CatalogError(
            f"AppleDB platform is {latest.platform}, expected exactly {policy.platform}"
        )
    if _major(latest.version, "AppleDB result.version") != policy.major_version:
        raise CatalogError(f"latest version major must be exactly {policy.major_version}")

    known_builds = _known_builds(manifests_dir, policy)
    if latest.build == policy.baseline.build:
        if latest.metadata != policy.baseline:
            raise CatalogError("latest metadata differs from the policy baseline")
        status: Literal["current", "candidate"] = "current"
    else:
        if latest.build in known_builds:
            raise CatalogError(
                f"latest build {latest.build} is already known but is not the baseline"
            )
        if latest.released_at <= policy.baseline.released_at:
            baseline_released = policy.baseline.released
            raise CatalogError(
                f"candidate release {latest.released} is not newer than baseline "
                f"{baseline_released}"
            )
        status = "candidate"

    return DiscoveryDecision(
        track_id=policy.identifier,
        status=status,
        platform=policy.platform,
        device=policy.device,
        major_version=policy.major_version,
        baseline=policy.baseline,
        latest=latest.metadata,
    )


def discover_live(
    policy_path: Path,
    manifests_dir: Path,
    ipsw_executable: str | Path = "ipsw",
) -> DiscoveryDecision:
    policy = TrackPolicy.from_path(policy_path)
    command = [
        os.fspath(ipsw_executable),
        "dl",
        "appledb",
        "--os",
        policy.platform,
        "--device",
        policy.device,
        "--version",
        f"{policy.major_version}.",
        "--show-latest",
        "--no-color",
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)  # noqa: S603
    except OSError as error:
        raise CatalogError(f"cannot run ipsw: {error}") from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or error.stdout.strip()
        suffix = f": {detail}" if detail else ""
        raise CatalogError(f"ipsw AppleDB query failed{suffix}") from error
    return discover(policy, AppleDBRelease.from_json(result.stdout), manifests_dir)
