from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ipsw_diff_catalog.model import CatalogError
from ipsw_diff_catalog.render import load_entries, render
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
