from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path, PurePosixPath
from typing import cast

from ipsw_diff_catalog.model import CatalogEntry, CatalogError, JsonObject, read_json_object

_APPLEDB_REPOSITORY = "https://github.com/littlebyteorg/appledb"
_FULL_OID = re.compile(r"[0-9a-f]{40}")
_BUILD = re.compile(r"[A-Za-z0-9]+")
_BASE_VERSION = re.compile(r"[0-9]+(?:\.[0-9]+)*")
_BETA_QUALIFIER = re.compile(r"beta(?: [1-9][0-9]*)?")
_RC_QUALIFIER = re.compile(r"RC(?: [1-9][0-9]*)?")
_PLATFORMS = {"iOS", "macOS"}
_CHANNELS = {"beta", "rc", "release"}

ReleaseKey = tuple[str, str]


@dataclass(frozen=True)
class ReleaseLabel:
    platform: str
    build: str
    display_version: str
    channel: str


def _exact_keys(value: JsonObject, expected: set[str], context: str) -> None:
    actual = set(value)
    if actual != expected:
        raise CatalogError(
            f"{context} keys differ: missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )


def _object(value: object, context: str) -> JsonObject:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise CatalogError(f"{context} must be an object")
    return cast("JsonObject", value)


def _array(value: object, context: str) -> list[object]:
    if not isinstance(value, list):
        raise CatalogError(f"{context} must be an array")
    return value


def _string(value: object, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise CatalogError(f"{context} must be a non-empty string")
    return value


def _boolean(value: object, context: str) -> bool:
    if type(value) is not bool:
        raise CatalogError(f"{context} must be a boolean")
    return value


def _validate_source(value: object) -> None:
    source = _object(value, "release registry source")
    _exact_keys(source, {"repository", "commit"}, "release registry source")
    repository = _string(source["repository"], "release registry source.repository")
    if repository != _APPLEDB_REPOSITORY:
        raise CatalogError("release registry source.repository differs from AppleDB")
    commit = _string(source["commit"], "release registry source.commit")
    if _FULL_OID.fullmatch(commit) is None:
        raise CatalogError("release registry source.commit must be a full lowercase SHA-1")


def _validate_released(value: object, context: str) -> None:
    released = _string(value, context)
    try:
        if "T" in released:
            datetime.fromisoformat(released)
        else:
            date.fromisoformat(released)
    except ValueError as error:
        raise CatalogError(f"{context} must be an ISO 8601 date or timestamp") from error


def _validate_source_path(value: object, platform: str, build: str, context: str) -> None:
    raw = _string(value, context)
    source_path = PurePosixPath(raw)
    root = PurePosixPath("osFiles", platform)
    if (
        source_path.is_absolute()
        or str(source_path) != raw
        or ".." in source_path.parts
        or source_path.name != f"{build}.json"
        or not source_path.is_relative_to(root)
    ):
        raise CatalogError(f"{context} must identify {build}.json below {root}")


def _release_label(value: object, index: int) -> ReleaseLabel:
    context = f"release registry releases[{index}]"
    record = _object(value, context)
    _exact_keys(
        record,
        {
            "platform",
            "build",
            "display_version",
            "channel",
            "beta",
            "rc",
            "released",
            "source_path",
        },
        context,
    )
    platform = _string(record["platform"], f"{context}.platform")
    if platform not in _PLATFORMS:
        raise CatalogError(f"{context}.platform must be iOS or macOS")
    build = _string(record["build"], f"{context}.build")
    if _BUILD.fullmatch(build) is None:
        raise CatalogError(f"{context}.build has an unsupported format")
    display_version = _string(record["display_version"], f"{context}.display_version")
    base_version, separator, raw_qualifier = display_version.partition(" ")
    if _BASE_VERSION.fullmatch(base_version) is None:
        raise CatalogError(f"{context}.display_version has an unsupported base version")
    channel = _string(record["channel"], f"{context}.channel")
    if channel not in _CHANNELS:
        raise CatalogError(f"{context}.channel must be beta, rc, or release")
    beta = _boolean(record["beta"], f"{context}.beta")
    rc = _boolean(record["rc"], f"{context}.rc")
    expected_channel = "beta" if beta else "rc" if rc else "release"
    if (beta and rc) or channel != expected_channel:
        raise CatalogError(f"{context} channel and flags conflict")
    qualifier = raw_qualifier if separator else None
    expected_qualifier = _BETA_QUALIFIER if beta else _RC_QUALIFIER if rc else None
    if expected_qualifier is None:
        if qualifier is not None:
            raise CatalogError(f"{context}.display_version qualifier conflicts with channel")
    elif qualifier is None or expected_qualifier.fullmatch(qualifier) is None:
        raise CatalogError(f"{context}.display_version qualifier conflicts with channel")
    _validate_released(record["released"], f"{context}.released")
    _validate_source_path(record["source_path"], platform, build, f"{context}.source_path")
    return ReleaseLabel(
        platform=platform,
        build=build,
        display_version=display_version,
        channel=channel,
    )


def _required_endpoints(entries: tuple[CatalogEntry, ...]) -> dict[ReleaseKey, str]:
    required: dict[ReleaseKey, str] = {}
    for entry in entries:
        for release in (entry.previous, entry.next):
            key = (entry.platform, release.build)
            observed = required.get(key)
            if observed is not None and observed != release.version:
                raise CatalogError(
                    f"catalog endpoint {entry.platform} {release.build} has conflicting "
                    f"versions: {observed} and {release.version}"
                )
            required[key] = release.version
    return required


def load_release_labels(
    registry_path: Path,
    entries: tuple[CatalogEntry, ...],
) -> dict[ReleaseKey, ReleaseLabel]:
    registry = read_json_object(registry_path)
    _exact_keys(registry, {"schema_version", "source", "releases"}, "release registry")
    if type(registry["schema_version"]) is not int or registry["schema_version"] != 1:
        raise CatalogError("release registry schema_version must be 1")
    _validate_source(registry["source"])
    releases = _array(registry["releases"], "release registry releases")
    labels: dict[ReleaseKey, ReleaseLabel] = {}
    for index, value in enumerate(releases):
        label = _release_label(value, index)
        key = (label.platform, label.build)
        if key in labels:
            raise CatalogError(
                f"duplicate release registry endpoint: {label.platform} {label.build}"
            )
        labels[key] = label

    required = _required_endpoints(entries)
    missing = sorted(set(required) - set(labels))
    unexpected = sorted(set(labels) - set(required))
    if missing or unexpected:
        raise CatalogError(
            f"release registry coverage differs: missing={missing}, unexpected={unexpected}"
        )
    for key, expected_version in required.items():
        display_version = labels[key].display_version
        base_version = display_version.partition(" ")[0]
        if base_version != expected_version:
            platform, build = key
            raise CatalogError(
                f"release registry {platform} {build} differs: expected base "
                f"{expected_version}, got {display_version}"
            )
    return labels
