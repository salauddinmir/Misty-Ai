"""Tests for the read-only GET /api/training/catalog endpoint."""

from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app, raise_server_exceptions=False)


class TestTrainingCatalogRoute:
    def test_catalog_empty_when_no_packages(self) -> None:
        with client:
            response = client.get("/api/training/catalog")
        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 0
        assert payload["packages"] == []
        assert payload["source"] == "catalog"

    def test_catalog_route_shape(self) -> None:
        """The catalog payload always exposes packages, count, and source."""
        with client:
            response = client.get("/api/training/catalog")
        payload = response.json()
        assert set(payload.keys()) == {"packages", "count", "source"}
        assert isinstance(payload["packages"], list)
        assert isinstance(payload["count"], int)
