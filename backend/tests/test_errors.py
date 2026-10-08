from fastapi.testclient import TestClient


def test_unknown_routes_use_spanish_error_envelope(tmp_path):
    from clipdock.api import Settings, create_app

    with TestClient(
        create_app(Settings(root=tmp_path, signing_key="x" * 40), lambda *args: {})
    ) as c:
        response = c.get("/api/unknown")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"


def test_unexpected_inspector_errors_do_not_leak_details(tmp_path):
    from clipdock.api import Settings, create_app

    def failed(*args):
        raise RuntimeError("SECRET DATABASE CREDENTIALS")

    with TestClient(
        create_app(Settings(root=tmp_path, signing_key="x" * 40), failed),
        raise_server_exceptions=False,
    ) as c:
        response = c.post(
            "/api/inspect",
            json={"url": "https://youtu.be/BaW_jenozKc", "authorized": True},
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "EXTRACTION_FAILED"
        assert "SECRET" not in response.text
