from fastapi.testclient import TestClient


def test_request_body_is_capped_before_json_parsing(tmp_path):
    from clipdock.api import Settings, create_app

    with TestClient(
        create_app(Settings(root=tmp_path, signing_key="x" * 40), lambda *args: {})
    ) as c:
        response = c.post("/api/inspect", json={"url": "x" * 40000, "authorized": True})
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "REQUEST_TOO_LARGE"
