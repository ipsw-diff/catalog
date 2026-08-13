from __future__ import annotations

import json
import stat
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import pytest

from ipsw_diff_catalog.census import census
from ipsw_diff_catalog.model import CatalogError, JsonObject, canonical_json
from tests.helpers import commit_all, git, init_repo

if TYPE_CHECKING:
    from pathlib import Path

EXPECTED_PAYLOAD_COUNT = 7
EXPECTED_ORDINARY_COUNT = 3
EXPECTED_BLOCKED_COUNT = 4
EXPECTED_TRACKED_FILE_COUNT = 15
EXPECTED_OUTPUT_MODE = 0o644


@dataclass(frozen=True)
class CensusFixture:
    source: Path
    policy_path: Path
    output: Path
    policy: JsonObject


def _ordinary_readme(heading: str) -> str:
    return (
        "# 1.0 (A1) .vs 1.1 (A2)\n\n"
        f"## {heading}\n\n"
        "- `Device1,1_1.0_A1_Restore.ipsw`\n"
        "- `Device1,1_1.1_A2_Restore.ipsw`\n\n"
        "## Data\n"
    )


def _write_payload(root: Path, readme: str | None) -> None:
    root.mkdir(parents=True)
    if readme is not None:
        (root / "README.md").write_text(readme, encoding="utf-8")


@pytest.fixture
def census_fixture(tmp_path: Path) -> CensusFixture:
    source = tmp_path / "source"
    init_repo(source)
    git(source, "remote", "add", "origin", "https://github.com/example/legacy.git")

    (source / ".cache").mkdir()
    (source / ".cache/data.json").write_text("{}\n", encoding="utf-8")
    (source / ".github").mkdir()
    (source / ".github/workflow.yml").write_text("name: test\n", encoding="utf-8")
    (source / "LICENSE").write_text("license\n", encoding="utf-8")
    (source / "README.md").write_text("# legacy\n", encoding="utf-8")
    (source / "justfile").write_text("test:\n", encoding="utf-8")

    _write_payload(source / "device/payload-ipsws", _ordinary_readme("IPSWs"))
    (source / "device/payload-ipsws/data.md").write_text("legacy\n", encoding="utf-8")
    _write_payload(source / "payload-inputs", _ordinary_readme("Inputs"))
    (source / "payload-inputs/data.md").write_text("current\n", encoding="utf-8")
    _write_payload(source / "payload-missing", None)
    (source / "payload-missing/TOC.md").write_text(_ordinary_readme("IPSWs"), encoding="utf-8")
    (source / "payload-missing/data.md").write_text("missing\n", encoding="utf-8")
    _write_payload(source / "payload-no-entrypoint", None)
    (source / "payload-no-entrypoint/data.md").write_text("missing\n", encoding="utf-8")
    _write_payload(
        source / "payload-redirect",
        "# ⚠️ Please see corrected [README](../payload-inputs/README.md)",
    )
    _write_payload(
        source / "payload-aea",
        "# 1.0 (A1) .vs 1.1 (A2)\n\n"
        "## Inputs\n\n"
        "- `Device1,1_A1.aea`\n"
        "- `Device1,1_A2.aea`\n\n"
        "## Data\n",
    )
    _write_payload(
        source / "payload-unsupported",
        "# A1 .vs A2\n\n## OTAs\n\n- `A1`\n- `A2`\n",
    )
    git(source, "add", "--force", ".cache/data.json")
    commit = commit_all(source, "legacy corpus")

    policy: JsonObject = {
        "schema_version": 1,
        "source": {
            "repository": "https://github.com/example/legacy",
            "commit": commit,
        },
        "payload_roots": [
            "device/payload-ipsws",
            "payload-aea",
            "payload-inputs",
            "payload-missing",
            "payload-no-entrypoint",
            "payload-redirect",
            "payload-unsupported",
        ],
        "excluded_roots": [".cache", ".github"],
        "excluded_files": ["LICENSE", "README.md", "justfile"],
    }
    policy_path = tmp_path / "source-layout.json"
    policy_path.write_text(canonical_json(policy), encoding="utf-8")
    return CensusFixture(
        source=source,
        policy_path=policy_path,
        output=tmp_path / "census.json",
        policy=policy,
    )


def _write_policy(path: Path, policy: JsonObject) -> None:
    path.write_text(canonical_json(policy), encoding="utf-8")


def test_census_reconciles_every_tracked_file(census_fixture: CensusFixture) -> None:
    before = git(
        census_fixture.source,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    result = census(
        census_fixture.policy_path,
        census_fixture.source,
        census_fixture.output,
    )
    after = git(
        census_fixture.source,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    data = json.loads(census_fixture.output.read_text(encoding="utf-8"))

    assert before == after == ""
    assert result.payload_count == EXPECTED_PAYLOAD_COUNT
    assert result.ordinary_count == EXPECTED_ORDINARY_COUNT
    assert result.blocked_count == EXPECTED_BLOCKED_COUNT
    assert result.tracked_file_count == EXPECTED_TRACKED_FILE_COUNT
    assert stat.S_IMODE(census_fixture.output.stat().st_mode) == EXPECTED_OUTPUT_MODE
    assert data["summary"] == {
        "blocked_by_reason": {
            "missing-entrypoint": 1,
            "non-ipsw-inputs": 1,
            "redirect-readme": 1,
            "unsupported-readme": 1,
        },
        "blocked_count": 4,
        "ordinary_two_ipsw_count": EXPECTED_ORDINARY_COUNT,
        "payload_count": EXPECTED_PAYLOAD_COUNT,
    }
    coverage = data["coverage"]
    assert (
        coverage["payloads"]["tracked_file_count"] + coverage["excluded"]["tracked_file_count"]
        == coverage["total"]["tracked_file_count"]
        == EXPECTED_TRACKED_FILE_COUNT
    )
    assert (
        coverage["payloads"]["logical_bytes"] + coverage["excluded"]["logical_bytes"]
        == coverage["total"]["logical_bytes"]
        == result.logical_bytes
    )
    ordinary = {
        payload["path"]: (
            payload["entrypoint"],
            payload["readme"]["input_section"],
        )
        for payload in data["payloads"]
        if payload["classification"] == "ordinary-two-ipsw"
    }
    assert ordinary == {
        "device/payload-ipsws": ("README.md", "IPSWs"),
        "payload-inputs": ("README.md", "Inputs"),
        "payload-missing": ("TOC.md", "IPSWs"),
    }
    checked = census(
        census_fixture.policy_path,
        census_fixture.source,
        census_fixture.output,
        check=True,
    )
    assert checked.checked


def test_census_rejects_unclassified_tracked_file(census_fixture: CensusFixture) -> None:
    policy = dict(census_fixture.policy)
    policy["excluded_files"] = ["LICENSE", "README.md"]
    _write_policy(census_fixture.policy_path, policy)
    with pytest.raises(CatalogError, match=r"not classified.*justfile"):
        census(census_fixture.policy_path, census_fixture.source, census_fixture.output)


def test_census_prefers_root_readme_when_toc_also_exists(
    census_fixture: CensusFixture,
) -> None:
    (census_fixture.source / "payload-inputs/TOC.md").write_text(
        "not a valid report\n",
        encoding="utf-8",
    )
    commit = commit_all(census_fixture.source, "add lower-priority TOC")
    policy = dict(census_fixture.policy)
    source = dict(cast("JsonObject", policy["source"]))
    source["commit"] = commit
    policy["source"] = source
    _write_policy(census_fixture.policy_path, policy)

    census(census_fixture.policy_path, census_fixture.source, census_fixture.output)

    data = json.loads(census_fixture.output.read_text(encoding="utf-8"))
    payload = next(row for row in data["payloads"] if row["path"] == "payload-inputs")
    assert payload["classification"] == "ordinary-two-ipsw"
    assert payload["entrypoint"] == "README.md"


def test_census_rejects_overlapping_policy_paths(census_fixture: CensusFixture) -> None:
    policy = dict(census_fixture.policy)
    policy["excluded_roots"] = [".cache", ".github", "payload-inputs"]
    _write_policy(census_fixture.policy_path, policy)
    with pytest.raises(CatalogError, match=r"paths overlap.*payload-inputs"):
        census(census_fixture.policy_path, census_fixture.source, census_fixture.output)


def test_census_rejects_absent_policy_root(census_fixture: CensusFixture) -> None:
    policy = dict(census_fixture.policy)
    payload_roots = list(cast("list[object]", census_fixture.policy["payload_roots"]))
    payload_roots.append("payload-z-absent")
    policy["payload_roots"] = payload_roots
    _write_policy(census_fixture.policy_path, policy)
    with pytest.raises(CatalogError, match="payload-z-absent"):
        census(census_fixture.policy_path, census_fixture.source, census_fixture.output)


def test_census_check_rejects_changed_output(census_fixture: CensusFixture) -> None:
    census_fixture.output.write_text("{}\n", encoding="utf-8")
    with pytest.raises(CatalogError, match="census output differs"):
        census(
            census_fixture.policy_path,
            census_fixture.source,
            census_fixture.output,
            check=True,
        )


def test_census_check_rejects_non_utf8_output(census_fixture: CensusFixture) -> None:
    census_fixture.output.write_bytes(b"\xff")
    with pytest.raises(CatalogError, match="cannot read census output"):
        census(
            census_fixture.policy_path,
            census_fixture.source,
            census_fixture.output,
            check=True,
        )


def test_census_ignores_and_preserves_source_worktree(census_fixture: CensusFixture) -> None:
    census(census_fixture.policy_path, census_fixture.source, census_fixture.output)
    expected = census_fixture.output.read_bytes()
    (census_fixture.source / "LICENSE").write_text("dirty license\n", encoding="utf-8")
    (census_fixture.source / "untracked.txt").write_text("untracked\n", encoding="utf-8")
    before = git(
        census_fixture.source,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )

    census(
        census_fixture.policy_path,
        census_fixture.source,
        census_fixture.output,
        check=True,
    )

    after = git(
        census_fixture.source,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    assert after == before
    assert census_fixture.output.read_bytes() == expected


def test_census_refuses_output_inside_source(census_fixture: CensusFixture) -> None:
    with pytest.raises(CatalogError, match="outside the source repository"):
        census(
            census_fixture.policy_path,
            census_fixture.source,
            census_fixture.source / "census.json",
        )
