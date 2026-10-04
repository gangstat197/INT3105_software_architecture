from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_endpoints_removed():
    with TestClient(app) as client:
        for path in ("/api/health/models", "/api/health/db"):
            assert client.get(path).status_code == 404
        assert not any(
            path.startswith("/api/health")
            for path in client.get("/openapi.json").json()["paths"]
        )
