from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from ipsw_diff_catalog.cli import _parser
from ipsw_diff_catalog.model import CatalogError
from ipsw_diff_catalog.planner import plan

if TYPE_CHECKING:
    from pathlib import Path

_SOURCE_REPOSITORY = "https://github.com/example/legacy"
_SOURCE_COMMIT = "a" * 40
_EXPECTED_SPECIFICATION_COUNT = 2


def _release(device: str, version: str, build: str) -> dict[str, object]:
    return {
        "version": version,
        "build": build,
        "input": f"{device}_{version}_{build}_Restore.ipsw",
    }


def _payload(
    path: str,
    device: str,
    previous_build: str,
    next_build: str,
) -> dict[str, object]:
    return {
        "classification": "ordinary-two-ipsw",
        "entrypoint": "README.md",
        "integrity": {
            "git_tree": "b" * 40,
            "logical_bytes": 1,
            "modes": ["100644"],
            "tracked_file_count": 1,
        },
        "path": path,
        "readme": {
            "from": _release(device, "26.0", previous_build),
            "input_section": "IPSWs",
            "to": _release(device, "26.0", next_build),
        },
        "reason": None,
    }


def _write_inputs(
    root: Path,
    *,
    payloads: list[dict[str, object]] | None = None,
) -> tuple[Path, Path, Path]:
    census_path = root / "census.json"
    policy_path = root / "policy.json"
    output = root / "specs"
    rows = payloads or [
        _payload("ios-row", "iPhone18,1", "A1", "A2"),
        _payload("macos-row", "UniversalMac", "B1", "B2"),
    ]
    paths = sorted(str(row["path"]) for row in rows)
    census_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source": {
                    "repository": _SOURCE_REPOSITORY,
                    "commit": _SOURCE_COMMIT,
                    "git_tree": "c" * 40,
                },
                "payloads": rows,
            }
        ),
        encoding="utf-8",
    )
    policy_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source": {
                    "repository": _SOURCE_REPOSITORY,
                    "commit": _SOURCE_COMMIT,
                },
                "selection": {
                    "classification": "ordinary-two-ipsw",
                    "destination_major": 26,
                    "expected_source_paths": paths,
                },
                "routes": [
                    {
                        "input_device_prefix": "iPhone",
                        "platform": "iOS",
                        "repository": "https://github.com/example/ios-26",
                    },
                    {
                        "input_device_prefix": "UniversalMac",
                        "platform": "macOS",
                        "repository": "https://github.com/example/macos-26",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return policy_path, census_path, output


def _read_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_plan_writes_and_checks_exact_specs(tmp_path: Path) -> None:
    policy, census, output = _write_inputs(tmp_path)

    result = plan(policy, census, output, check=False)

    assert result.specification_count == _EXPECTED_SPECIFICATION_COUNT
    ios = _read_object(output / "ios-26.0-A1-A2.json")
    macos = _read_object(output / "macos-26.0-B1-B2.json")
    assert ios["device"] == "iPhone18,1"
    assert macos["device"] == "UniversalMac"
    assert ios["source"] == {
        "repository": _SOURCE_REPOSITORY,
        "commit": _SOURCE_COMMIT,
        "path": "ios-row",
    }
    assert plan(policy, census, output, check=True).checked


def test_plan_preserves_explicit_toc_entrypoint(tmp_path: Path) -> None:
    rows = [_payload("ios-row", "iPhone18,1", "A1", "A2")]
    rows[0]["entrypoint"] = "TOC.md"
    policy, census, output = _write_inputs(tmp_path, payloads=rows)

    plan(policy, census, output, check=False)

    planned = _read_object(output / "ios-26.0-A1-A2.json")
    destination = planned["destination"]
    assert isinstance(destination, dict)
    assert destination["entrypoint"] == "diffs/ios-row/TOC.md"


def test_plan_rejects_allowlist_omission(tmp_path: Path) -> None:
    policy, census, output = _write_inputs(tmp_path)
    data = _read_object(policy)
    selection = data["selection"]
    assert isinstance(selection, dict)
    selection["expected_source_paths"] = ["ios-row"]
    policy.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(CatalogError, match=r"extra=\['macos-row'\]"):
        plan(policy, census, output, check=False)


def test_plan_rejects_changed_source_identity(tmp_path: Path) -> None:
    policy, census, output = _write_inputs(tmp_path)
    data = _read_object(policy)
    source = data["source"]
    assert isinstance(source, dict)
    source["commit"] = "d" * 40
    policy.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(CatalogError, match="source differs"):
        plan(policy, census, output, check=False)


def test_plan_rejects_different_input_devices(tmp_path: Path) -> None:
    rows = [_payload("ios-row", "iPhone18,1", "A1", "A2")]
    readme = rows[0]["readme"]
    assert isinstance(readme, dict)
    readme["from"] = _release("iPhone17,1", "26.0", "A1")
    policy, census, output = _write_inputs(tmp_path, payloads=rows)

    with pytest.raises(CatalogError, match="input devices differ"):
        plan(policy, census, output, check=False)


def test_plan_rejects_ambiguous_route(tmp_path: Path) -> None:
    rows = [_payload("ios-row", "iPhone18,1", "A1", "A2")]
    policy, census, output = _write_inputs(tmp_path, payloads=rows)
    data = _read_object(policy)
    routes = data["routes"]
    assert isinstance(routes, list)
    routes.append(
        {
            "input_device_prefix": "iPhone18",
            "platform": "iOS",
            "repository": "https://github.com/example/ios-26",
        }
    )
    policy.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(CatalogError, match="exactly one route, got 2"):
        plan(policy, census, output, check=False)


def test_plan_rejects_duplicate_identifiers_before_writing(tmp_path: Path) -> None:
    rows = [
        _payload("ios-row-a", "iPhone18,1", "A1", "A2"),
        _payload("ios-row-b", "iPhone18,1", "A1", "A2"),
    ]
    policy, census, output = _write_inputs(tmp_path, payloads=rows)

    with pytest.raises(CatalogError, match="identifiers must be unique"):
        plan(policy, census, output, check=False)
    assert not output.exists()


def test_plan_check_rejects_missing_specification(tmp_path: Path) -> None:
    policy, census, output = _write_inputs(tmp_path)

    with pytest.raises(CatalogError, match="cannot read planned specification"):
        plan(policy, census, output, check=True)


def test_plan_cli_requires_explicit_output() -> None:
    with pytest.raises(SystemExit):
        _parser().parse_args(
            [
                "plan",
                "--policy",
                "policy.json",
                "--census",
                "census.json",
            ]
        )


def test_plan_refuses_to_overwrite_different_specification(tmp_path: Path) -> None:
    policy, census, output = _write_inputs(tmp_path)
    plan(policy, census, output, check=False)
    changed = output / "ios-26.0-A1-A2.json"
    changed.write_text("{}\n", encoding="utf-8")

    with pytest.raises(CatalogError, match="refusing to overwrite differing"):
        plan(policy, census, output, check=False)


def test_plan_preflights_all_existing_specs_before_writing(tmp_path: Path) -> None:
    policy, census, output = _write_inputs(tmp_path)
    output.mkdir()
    changed = output / "macos-26.0-B1-B2.json"
    changed.write_text("{}\n", encoding="utf-8")

    with pytest.raises(CatalogError, match="refusing to overwrite differing"):
        plan(policy, census, output, check=False)
    assert not (output / "ios-26.0-A1-A2.json").exists()


def test_plan_rejects_stale_in_scope_specification(tmp_path: Path) -> None:
    policy, census, output = _write_inputs(tmp_path)
    plan(policy, census, output, check=False)
    expected = output / "ios-26.0-A1-A2.json"
    stale = output / "stale.json"
    stale.write_text(expected.read_text(encoding="utf-8"), encoding="utf-8")

    with pytest.raises(CatalogError, match="unexpected files"):
        plan(policy, census, output, check=True)


def test_plan_rejects_invalid_unused_route(tmp_path: Path) -> None:
    rows = [_payload("ios-row", "iPhone18,1", "A1", "A2")]
    policy, census, output = _write_inputs(tmp_path, payloads=rows)
    data = _read_object(policy)
    routes = data["routes"]
    assert isinstance(routes, list)
    routes.append(
        {
            "input_device_prefix": "Watch",
            "platform": "watchOS",
            "repository": "https://github.com/example/watchos-26",
        }
    )
    policy.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(CatalogError, match="platform must be exactly"):
        plan(policy, census, output, check=False)


def test_plan_records_reviewed_exclusion_without_silently_dropping_it(tmp_path: Path) -> None:
    rows = [
        _payload("ios-row", "iPhone18,1", "A1", "A2"),
        _payload("cross-device", "iPhone18,1", "B1", "B2"),
    ]
    readme = rows[1]["readme"]
    assert isinstance(readme, dict)
    readme["from"] = _release("iPhone17,1", "26.0", "B1")
    policy, census, output = _write_inputs(tmp_path, payloads=rows)
    data = _read_object(policy)
    selection = data["selection"]
    assert isinstance(selection, dict)
    selection["expected_source_paths"] = ["ios-row"]
    selection["excluded_source_paths"] = [
        {"path": "cross-device", "reason": "input devices differ"}
    ]
    policy.write_text(json.dumps(data), encoding="utf-8")

    result = plan(policy, census, output, check=False)

    assert result.specification_count == 1
    assert not (output / "ios-26.0-B1-B2.json").exists()


def test_plan_rejects_unreviewed_exclusion(tmp_path: Path) -> None:
    policy, census, output = _write_inputs(tmp_path)
    data = _read_object(policy)
    selection = data["selection"]
    assert isinstance(selection, dict)
    selection["expected_source_paths"] = ["ios-row"]
    selection["excluded_source_paths"] = [{"path": "not-in-census", "reason": "unsupported"}]
    policy.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(CatalogError, match=r"missing=.*not-in-census.*extra=.*macos-row"):
        plan(policy, census, output, check=False)


def test_plan_device_qualifies_one_reviewed_identifier_collision(tmp_path: Path) -> None:
    rows = [
        _payload("device-a", "iPhone17,1", "A1", "A2"),
        _payload("device-b", "iPhone17,5", "A1", "A2"),
    ]
    policy, census, output = _write_inputs(tmp_path, payloads=rows)
    data = _read_object(policy)
    selection = data["selection"]
    assert isinstance(selection, dict)
    selection["device_qualified_identifier_paths"] = ["device-b"]
    policy.write_text(json.dumps(data), encoding="utf-8")

    result = plan(policy, census, output, check=False)

    assert result.specification_count == _EXPECTED_SPECIFICATION_COUNT
    assert (output / "ios-26.0-A1-A2.json").exists()
    qualified = output / "ios-26.0-A1-A2-iPhone17,5.json"
    assert qualified.exists()
    assert _read_object(qualified)["id"] == "ios-26.0-A1-A2-iPhone17,5"


def test_plan_rejects_unselected_device_qualified_path(tmp_path: Path) -> None:
    policy, census, output = _write_inputs(tmp_path)
    data = _read_object(policy)
    selection = data["selection"]
    assert isinstance(selection, dict)
    selection["device_qualified_identifier_paths"] = ["not-selected"]
    policy.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(CatalogError, match="identifier paths are not selected"):
        plan(policy, census, output, check=False)


def test_plan_rejects_unnecessary_device_qualified_path(tmp_path: Path) -> None:
    policy, census, output = _write_inputs(tmp_path)
    data = _read_object(policy)
    selection = data["selection"]
    assert isinstance(selection, dict)
    selection["device_qualified_identifier_paths"] = ["ios-row"]
    policy.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(CatalogError, match="do not resolve a collision"):
        plan(policy, census, output, check=False)
