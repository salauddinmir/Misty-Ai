"""Shared test fixtures for the MISTY test suite.

The route tests instantiate ``apps.api.main.app`` module-level, which means
the FastAPI lifespan creates its own Database against the repository's
default ``data/misty_brain.db``. If that path is shared with other tests
(e.g. the Phase-12 package persistence tests that seed the catalog), the
catalog route tests become order-dependent and flaky. This conftest points
the default database location at a test-only file so every test run starts
with a clean, isolated data directory.
"""

from __future__ import annotations

import os
import tempfile

import pytest


@pytest.fixture(autouse=True)
def _isolate_default_database() -> None:  # type: ignore[misc]
    """Redirect the repo-default SQLite path to a temporary file.

    ``apps.api.database.DEFAULT_DB_PATH`` is resolved at module import time,
    so the redirection must happen before that module is imported. pytest
    loads conftest first, and ``apps.api.main`` is imported by the route
    tests inside their module, which happens after conftest fixtures run.
    For the module-level TestClient imports this also works because pytest
    re-imports conftest before collecting the test modules.
    """
    if not os.environ.get("MISTY_DB_URL"):
        os.environ["MISTY_DB_URL"] = f"sqlite:///{tempfile.mktemp(suffix='.db', prefix='misty_test_')}"
