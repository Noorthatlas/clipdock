from fastapi.testclient import TestClient


def test_only_explicit_frontend_origin_can_call_browser_api(tmp_path, monkeypatch):
    from clipdock.api import Settings, create_app

    monkeypatch.setenv("CLIPDOCK_CORS_ORIGINS", "https://clipdock.example")
    with TestClient(
        create_app(Settings(root=tmp_path, signing_key="x" * 40), lambda *args: {})
    ) as c:
        response = c.options(
            "/api/inspect",
            headers={
                "Origin": "https://clipdock.example",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert (
            response.headers.get("access-control-allow-origin")
            == "https://clipdock.example"
        )
        rejected = c.options(
            "/api/inspect",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert "access-control-allow-origin" not in rejected.headers
