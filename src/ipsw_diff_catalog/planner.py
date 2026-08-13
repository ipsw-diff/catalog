from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from ipsw_diff_catalog.model import (
    CatalogError,
    JsonObject,
    MigrationSpec,
    canonical_json,
    read_json_object,
)

if TYPE_CHECKING:
    from pathlib import Path

_DEVICE_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9,.-]*")
_GITHUB_REPOSITORY = re.compile(
    r"https://github\.com/[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*"
)
_VERSION_MAJOR = re.compile(r"([0-9]+)")


def _object(value: object, context: str) -> JsonObject:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise CatalogError(f"{context} must be an object")
    return cast("JsonObject", value)


def _array(value: object, context: str) -> list[object]:
    if not isinstance(value, list):
        raise CatalogError(f"{context} must be an array")
    return cast("list[object]", value)


def _string(value: object, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise CatalogError(f"{context} must be a non-empty string")
    return value


def _positive_integer(value: object, context: str) -> int:
    if type(value) is not int or value <= 0:
        raise CatalogError(f"{context} must be a positive integer")
    return value


def _exact_keys(value: JsonObject, expected: set[str], context: str) -> None:
    actual = set(value)
    if actual != expected:
        raise CatalogError(
            f"{context} keys differ: missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )


@dataclass(frozen=True)
class _SourcePolicy:
    repository: str
    commit: str

    @classmethod
    def from_object(cls, value: object) -> _SourcePolicy:
        data = _object(value, "planning policy.source")
        _exact_keys(data, {"repository", "commit"}, "planning policy.source")
        return cls(
            repository=_string(data["repository"], "planning policy.source.repository"),
            commit=_string(data["commit"], "planning policy.source.commit"),
        )


@dataclass(frozen=True)
class _ExcludedPath:
    path: str
    reason: str

    @classmethod
    def from_object(cls, value: object, index: int) -> _ExcludedPath:
        context = f"planning policy.selection.excluded_source_paths[{index}]"
        data = _object(value, context)
        _exact_keys(data, {"path", "reason"}, context)
        return cls(
            path=_string(data["path"], f"{context}.path"),
            reason=_string(data["reason"], f"{context}.reason"),
        )


def _sorted_unique_strings(value: object, context: str) -> tuple[str, ...]:
    items = tuple(_string(item, f"{context}[]") for item in _array(value, context))
    if items != tuple(sorted(items)):
        raise CatalogError(f"{context} must be sorted")
    if len(items) != len(set(items)):
        raise CatalogError(f"{context} must be unique")
    return items


def _excluded_paths(value: object) -> tuple[_ExcludedPath, ...]:
    context = "planning policy.selection.excluded_source_paths"
    excluded = tuple(
        _ExcludedPath.from_object(item, index) for index, item in enumerate(_array(value, context))
    )
    paths = tuple(item.path for item in excluded)
    if paths != tuple(sorted(paths)):
        raise CatalogError(f"{context} must be sorted by path")
    if len(paths) != len(set(paths)):
        raise CatalogError(f"{context} must be unique")
    return excluded


@dataclass(frozen=True)
class _SelectionPolicy:
    classification: str
    destination_major: int
    expected_source_paths: tuple[str, ...]
    excluded_source_paths: tuple[_ExcludedPath, ...]
    device_qualified_identifier_paths: tuple[str, ...]

    @classmethod
    def from_object(cls, value: object) -> _SelectionPolicy:
        data = _object(value, "planning policy.selection")
        required = {"classification", "destination_major", "expected_source_paths"}
        optional = {"excluded_source_paths", "device_qualified_identifier_paths"}
        actual = set(data)
        if not required.issubset(actual) or not actual.issubset(required | optional):
            raise CatalogError(
                "planning policy.selection keys differ: "
                f"missing={sorted(required - actual)}, "
                f"extra={sorted(actual - required - optional)}"
            )
        paths = _sorted_unique_strings(
            data["expected_source_paths"],
            "planning policy.selection.expected_source_paths",
        )
        if not paths:
            raise CatalogError("planning policy expected_source_paths must not be empty")
        excluded = _excluded_paths(data.get("excluded_source_paths", []))
        excluded_paths = tuple(item.path for item in excluded)
        if set(paths) & set(excluded_paths):
            raise CatalogError("planning policy selected and excluded source paths overlap")
        qualified = _sorted_unique_strings(
            data.get("device_qualified_identifier_paths", []),
            "planning policy.selection.device_qualified_identifier_paths",
        )
        unexpected_qualified = set(qualified) - set(paths)
        if unexpected_qualified:
            raise CatalogError(
                "planning policy device-qualified identifier paths are not selected: "
                f"{sorted(unexpected_qualified)}"
            )
        return cls(
            classification=_string(
                data["classification"],
                "planning policy.selection.classification",
            ),
            destination_major=_positive_integer(
                data["destination_major"],
                "planning policy.selection.destination_major",
            ),
            expected_source_paths=paths,
            excluded_source_paths=excluded,
            device_qualified_identifier_paths=qualified,
        )


@dataclass(frozen=True)
class _Route:
    input_device_prefix: str
    platform: str
    repository: str

    @classmethod
    def from_object(cls, value: object, index: int) -> _Route:
        context = f"planning policy.routes[{index}]"
        data = _object(value, context)
        _exact_keys(data, {"input_device_prefix", "platform", "repository"}, context)
        prefix = _string(data["input_device_prefix"], f"{context}.input_device_prefix")
        if _DEVICE_TOKEN.fullmatch(prefix) is None:
            raise CatalogError(f"{context}.input_device_prefix has an unsupported format")
        return cls(
            input_device_prefix=prefix,
            platform=_string(data["platform"], f"{context}.platform"),
            repository=_string(data["repository"], f"{context}.repository"),
        )


@dataclass(frozen=True)
class _PlanningPolicy:
    source: _SourcePolicy
    selection: _SelectionPolicy
    routes: tuple[_Route, ...]

    @classmethod
    def from_path(cls, path: Path) -> _PlanningPolicy:
        data = read_json_object(path)
        _exact_keys(data, {"schema_version", "source", "selection", "routes"}, "planning policy")
        if _positive_integer(data["schema_version"], "planning policy.schema_version") != 1:
            raise CatalogError("planning policy.schema_version must be 1")
        routes = tuple(
            _Route.from_object(item, index)
            for index, item in enumerate(_array(data["routes"], "planning policy.routes"))
        )
        if not routes:
            raise CatalogError("planning policy.routes must not be empty")
        policy = cls(
            source=_SourcePolicy.from_object(data["source"]),
            selection=_SelectionPolicy.from_object(data["selection"]),
            routes=routes,
        )
        policy._validate_routes()
        return policy

    def _validate_routes(self) -> None:
        prefixes = tuple(route.input_device_prefix for route in self.routes)
        if len(prefixes) != len(set(prefixes)):
            raise CatalogError("planning policy route prefixes must be unique")
        for route in self.routes:
            if route.platform not in {"iOS", "macOS"}:
                raise CatalogError("planning policy route platform must be exactly iOS or macOS")
            if _GITHUB_REPOSITORY.fullmatch(route.repository) is None:
                raise CatalogError("planning policy route repository must be a GitHub URL")
            expected_name = f"{route.platform.lower()}-{self.selection.destination_major}"
            if not route.repository.endswith(f"/{expected_name}"):
                raise CatalogError(
                    f"planning policy route repository must route to {expected_name}"
                )


@dataclass(frozen=True)
class PlanResult:
    output: Path
    specification_count: int
    checked: bool


def _major(version: str, context: str) -> int:
    match = _VERSION_MAJOR.match(version)
    if match is None:
        raise CatalogError(f"{context} does not begin with a numeric major")
    return int(match.group(1))


def _release(value: object, context: str) -> JsonObject:
    data = _object(value, context)
    _exact_keys(data, {"version", "build", "input"}, context)
    return {
        "version": _string(data["version"], f"{context}.version"),
        "build": _string(data["build"], f"{context}.build"),
        "input": _string(data["input"], f"{context}.input"),
    }


def _device(input_name: str, context: str) -> str:
    token, separator, _remainder = input_name.partition("_")
    if not separator or _DEVICE_TOKEN.fullmatch(token) is None:
        raise CatalogError(f"{context} does not begin with a valid device token")
    return token


def _selected_payloads(census: JsonObject, policy: _PlanningPolicy) -> tuple[JsonObject, ...]:
    source = _object(census.get("source"), "census.source")
    repository = _string(source.get("repository"), "census.source.repository")
    commit = _string(source.get("commit"), "census.source.commit")
    if (repository, commit) != (policy.source.repository, policy.source.commit):
        raise CatalogError("planning policy source differs from census source")

    selected: list[JsonObject] = []
    for index, value in enumerate(_array(census.get("payloads"), "census.payloads")):
        payload = _object(value, f"census.payloads[{index}]")
        if payload.get("classification") != policy.selection.classification:
            continue
        readme = _object(payload.get("readme"), f"census.payloads[{index}].readme")
        next_release = _release(readme.get("to"), f"census.payloads[{index}].readme.to")
        version = _string(next_release["version"], f"census.payloads[{index}].readme.to.version")
        if (
            _major(version, f"census.payloads[{index}].readme.to.version")
            == policy.selection.destination_major
        ):
            selected.append(payload)

    selected.sort(key=lambda payload: _string(payload.get("path"), "census payload.path"))
    observed_paths = tuple(
        _string(payload.get("path"), "census payload.path") for payload in selected
    )
    excluded_paths = tuple(item.path for item in policy.selection.excluded_source_paths)
    reviewed_paths = tuple(sorted((*policy.selection.expected_source_paths, *excluded_paths)))
    if observed_paths != reviewed_paths:
        expected = set(reviewed_paths)
        observed = set(observed_paths)
        raise CatalogError(
            "selected census paths differ from reviewed allowlist: "
            f"missing={sorted(expected - observed)}, extra={sorted(observed - expected)}"
        )
    excluded = set(excluded_paths)
    return tuple(
        payload
        for payload in selected
        if _string(payload.get("path"), "census payload.path") not in excluded
    )


def _specification(
    payload: JsonObject,
    policy: _PlanningPolicy,
    *,
    qualify_device: bool,
) -> MigrationSpec:
    path = _string(payload.get("path"), "census payload.path")
    readme = _object(payload.get("readme"), f"census payload {path}.readme")
    previous = _release(readme.get("from"), f"census payload {path}.readme.from")
    next_release = _release(readme.get("to"), f"census payload {path}.readme.to")
    previous_input = _string(previous["input"], f"census payload {path} from input")
    next_input = _string(next_release["input"], f"census payload {path} to input")
    previous_device = _device(previous_input, f"census payload {path} from input")
    next_device = _device(next_input, f"census payload {path} to input")
    if previous_device != next_device:
        raise CatalogError(
            f"census payload {path} input devices differ: from={previous_device}, to={next_device}"
        )
    routes = tuple(
        route for route in policy.routes if next_device.startswith(route.input_device_prefix)
    )
    if len(routes) != 1:
        raise CatalogError(f"census payload {path} must match exactly one route, got {len(routes)}")
    route = routes[0]
    identifier = (
        f"{route.platform.lower()}-{next_release['version']}-"
        f"{previous['build']}-{next_release['build']}"
    )
    if qualify_device:
        identifier = f"{identifier}-{next_device}"
    return MigrationSpec.from_object(
        {
            "schema_version": 1,
            "id": identifier,
            "platform": route.platform,
            "major_version": policy.selection.destination_major,
            "device": next_device,
            "from": previous,
            "to": next_release,
            "source": {
                "repository": policy.source.repository,
                "commit": policy.source.commit,
                "path": path,
            },
            "destination": {
                "repository": route.repository,
                "payload_path": f"diffs/{path}",
                "manifest_path": f"manifests/{path}.json",
            },
        }
    )


def _read_existing(path: Path, context: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise CatalogError(f"cannot read {context} {path}: {error}") from error


def _preflight_output(
    planned: dict[Path, str],
    policy: _PlanningPolicy,
    output: Path,
    *,
    check: bool,
) -> None:
    for path, content in planned.items():
        if not path.exists():
            if check:
                raise CatalogError(f"cannot read planned specification {path}: file is missing")
            continue
        observed = _read_existing(path, "planned specification")
        if observed != content:
            verb = (
                "planned specification differs"
                if check
                else "refusing to overwrite differing specification"
            )
            raise CatalogError(f"{verb}: {path}")

    repositories = {route.repository for route in policy.routes}
    existing_scope: set[Path] = set()
    for path in output.glob("*.json"):
        try:
            specification = MigrationSpec.from_path(path)
        except CatalogError as error:
            raise CatalogError(f"cannot classify existing specification {path}: {error}") from error
        if (
            specification.source.repository == policy.source.repository
            and specification.source.commit == policy.source.commit
            and specification.major_version == policy.selection.destination_major
            and specification.destination.repository in repositories
        ):
            existing_scope.add(path)
    extras = existing_scope - set(planned)
    if extras:
        raise CatalogError(
            "planned specification scope contains unexpected files: "
            f"{sorted(str(path) for path in extras)}"
        )


def plan(policy_path: Path, census_path: Path, output: Path, *, check: bool) -> PlanResult:
    policy = _PlanningPolicy.from_path(policy_path)
    census = read_json_object(census_path)
    payloads = _selected_payloads(census, policy)
    base_specifications = tuple(
        _specification(payload, policy, qualify_device=False) for payload in payloads
    )
    identifier_counts = {
        identifier: sum(spec.identifier == identifier for spec in base_specifications)
        for identifier in {spec.identifier for spec in base_specifications}
    }
    colliding_paths = {
        _string(payload.get("path"), "census payload.path")
        for payload, specification in zip(payloads, base_specifications, strict=True)
        if identifier_counts[specification.identifier] > 1
    }
    unnecessary_qualified = (
        set(policy.selection.device_qualified_identifier_paths) - colliding_paths
    )
    if unnecessary_qualified:
        raise CatalogError(
            "planning policy device-qualified paths do not resolve a collision: "
            f"{sorted(unnecessary_qualified)}"
        )
    qualified_paths = set(policy.selection.device_qualified_identifier_paths)
    specifications = tuple(
        _specification(
            payload,
            policy,
            qualify_device=_string(payload.get("path"), "census payload.path") in qualified_paths,
        )
        for payload in payloads
    )
    identifiers = tuple(spec.identifier for spec in specifications)
    if len(identifiers) != len(set(identifiers)):
        raise CatalogError("planned specification identifiers must be unique")
    planned = {
        output / f"{specification.identifier}.json": canonical_json(specification.to_object())
        for specification in specifications
    }
    _preflight_output(planned, policy, output, check=check)
    if not check:
        try:
            output.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise CatalogError(f"cannot create specification output {output}: {error}") from error
        for path, content in planned.items():
            if path.exists():
                continue
            try:
                path.write_text(content, encoding="utf-8")
            except OSError as error:
                raise CatalogError(f"cannot write planned specification {path}: {error}") from error
    return PlanResult(
        output=output,
        specification_count=len(specifications),
        checked=check,
    )
