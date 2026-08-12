from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from ipsw_diff_catalog.model import CatalogError, MigrationSpec, parse_json_object

if TYPE_CHECKING:
    from tests.helpers import Repositories


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source.path", "../escape"),
        ("destination.payload_path", "elsewhere/diff"),
        ("destination.manifest_path", "manifests/not-json"),
    ],
)
def test_spec_rejects_unsafe_or_misplaced_paths(
    repositories: Repositories,
    field: str,
    value: str,
) -> None:
    data = json.loads(repositories.spec_path.read_text(encoding="utf-8"))
    section, name = field.split(".")
    data[section][name] = value
    with pytest.raises(CatalogError):
        MigrationSpec.from_object(data)


def test_spec_rejects_unknown_fields(repositories: Repositories) -> None:
    data = json.loads(repositories.spec_path.read_text(encoding="utf-8"))
    data["guessed_platform"] = True
    with pytest.raises(CatalogError, match=r"extra=.*guessed_platform"):
        MigrationSpec.from_object(data)


def test_json_rejects_duplicate_keys() -> None:
    with pytest.raises(CatalogError, match="duplicate key 'build'"):
        parse_json_object(
            b'{"release":{"build":"A1","build":"A2"}}',
            "test document",
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("platform", "watchOS", "platform must be exactly"),
        ("major_version", 2, "must match the destination version"),
    ],
)
def test_spec_rejects_unsupported_routing(
    repositories: Repositories,
    field: str,
    value: object,
    message: str,
) -> None:
    data = json.loads(repositories.spec_path.read_text(encoding="utf-8"))
    data[field] = value
    with pytest.raises(CatalogError, match=message):
        MigrationSpec.from_object(data)
