"""Tests for durable training package catalog persistence (Phase 12).

The catalog uses the same Database layer as concepts/relations but keeps
every registered version of a package so history survives process restarts.
These tests run against the SQLite (in-memory) driver, which exercises the
shared SQL through ``Database.execute``/``fetchall``; the PostgreSQL path
uses the same code path with ``$n`` placeholders.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.api.database import Database

MINIMAL_PACKAGE = {
    "package_id": "mathematics",
    "version": 1,
    "department": "mathematics",
    "languages": ["bn", "en"],
    "provenance": "pixline internal curriculum",
    "concepts": [{"concept_id": "addition", "name": "addition"}],
}


class TrainingPackagePersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        os.environ["MISTY_DB_URL"] = "sqlite:///test_training_packages.db"
        self.db = Database(db_url="sqlite:///test_training_packages.db")
        await self.db.initialize()
        # Guarantee a clean catalog at the start of every test.
        await self.db.execute("DELETE FROM training_packages")
        await self.db._connection.commit()

    async def asyncTearDown(self) -> None:
        await self.db.close()
        os.environ.pop("MISTY_DB_URL", None)

    async def test_save_and_load_package(self) -> None:
        await self.db.save_training_package(MINIMAL_PACKAGE)
        rows = await self.db.load_training_packages()
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["package_id"], "mathematics")
        self.assertEqual(row["version"], 1)
        self.assertEqual(row["department"], "mathematics")
        self.assertEqual(row["languages"], ["bn", "en"])
        self.assertIn("addition", row["package"]["concepts"][0]["name"])

    async def test_version_history_preserved(self) -> None:
        v1 = dict(MINIMAL_PACKAGE, version=1, concepts=[{"concept_id": "c", "name": "v1"}])
        v2 = dict(MINIMAL_PACKAGE, version=2, concepts=[{"concept_id": "c", "name": "v2"}])
        await self.db.save_training_package(v1)
        await self.db.save_training_package(v2)
        rows = await self.db.load_training_packages()
        versions = [r["version"] for r in rows]
        self.assertIn(1, versions)
        self.assertIn(2, versions)
        self.assertEqual(rows[0]["version"], 2)  # newest registered first

    async def test_department_filter(self) -> None:
        await self.db.save_training_package(MINIMAL_PACKAGE)
        empty = await self.db.load_training_packages(department="physics")
        self.assertEqual(empty, [])
        physics_rows = await self.db.load_training_packages(department="mathematics")
        self.assertEqual(len(physics_rows), 1)

    async def test_empty_catalog(self) -> None:
        self.assertEqual(await self.db.load_training_packages(), [])

    async def test_provenance_stored(self) -> None:
        await self.db.save_training_package(MINIMAL_PACKAGE)
        row = (await self.db.load_training_packages())[0]
        self.assertEqual(row["provenance"], "pixline internal curriculum")


if __name__ == "__main__":
    unittest.main()
