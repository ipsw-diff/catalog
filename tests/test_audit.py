from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ipsw_diff_catalog.audit import audit
from ipsw_diff_catalog.model import CatalogError
from ipsw_diff_catalog.verify import record
from tests.helpers import populate_destination

if TYPE_CHECKING:
    from pathlib import Path

    from tests.helpers import Repositories


def test_audit_rejects_catalog_and_spec_set_mismatch(
    repositories: Repositories,
    tmp_path: Path,
) -> None:
    entries = tmp_path / "entries"
    specs = tmp_path / "specs"
    specs.mkdir()
    destination_commit = populate_destination(repositories)
    record(
        repositories.spec,
        repositories.source,
        repositories.destination,
        destination_commit,
        entries,
    )
    (specs / "different-id.json").write_text(
        repositories.spec_path.read_text(encoding="utf-8").replace(
            repositories.spec.identifier,
            "different-id",
        ),
        encoding="utf-8",
    )
    with pytest.raises(CatalogError, match="catalog/spec id sets differ"):
        audit(entries, specs)
