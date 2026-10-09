"""API contract tests use injected transport; not production-download evidence."""

from fastapi.testclient import TestClient

from clipdock.api import Settings, create_app

SOURCE = (
    "https://raw.githubusercontent.com/Noorthatlas/clipdock/"
    "90089cc28480b1195c955e5333d06cb886f9a2f9/backend/tests/assets/owner-test.mp4"
)


def test_sample_inspection_is_explicit_permission_gated_and_fixed_source(tmp_path):
    calls = []

    def runner(action, payload, folder, progress):
        calls.append((action, payload))
        return dict(
            title="ClipDock · muestra propia CC0",
            thumbnail=None,
            platform="sample",
            duration=2,
            qualities=[180],
            has_audio=True,
        )

    app = create_app(Settings(root=tmp_path, signing_key="x" * 40), runner)
    with TestClient(app) as client:
        denied = client.post("/api/sample/inspect", json={"authorized": False})
        assert denied.status_code == 403
        assert not calls
        assert (
            client.post(
                "/api/sample/inspect",
                json={
                    "authorized": True,
                    "url": "https://127.0.0.1/private",
                },
            ).status_code
            == 422
        )
        assert not calls
        # A GitHub URL is NOT allowed through ordinary six-platform inspection.
        assert (
            client.post(
                "/api/inspect",
                json={
                    "authorized": True,
                    "url": SOURCE,
                },
            ).status_code
            == 400
        )
        response = client.post("/api/sample/inspect", json={"authorized": True})
        assert response.status_code == 200
        assert response.json()["platform"] == "sample"
        assert response.json()["token"]
        assert calls == [("inspect", {"url": SOURCE, "platform": "sample"})]


def test_owned_extractor_verifies_real_bytes_and_rejects_arbitrary_sources(monkeypatch):
    import io
    from pathlib import Path

    import pytest

    from clipdock.media import MediaError
    from clipdock.sample import OwnedSampleIE, validate_source
    from clipdock.worker import PublicYDL, options

    original = (Path(__file__).parent / "assets/owner-test.mp4").read_bytes()
    assert OwnedSampleIE.suitable(SOURCE)
    assert not OwnedSampleIE.suitable(SOURCE + "?url=http://127.0.0.1")
    assert not OwnedSampleIE.suitable(
        "https://raw.githubusercontent.com/evil/video.mp4"
    )
    validate_source({"url": SOURCE, "platform": "sample"})
    for url in (SOURCE + "?extra=1", "https://127.0.0.1/private"):
        with pytest.raises(MediaError):
            validate_source({"url": url, "platform": "sample"})
    with pytest.raises(MediaError):
        validate_source({"url": SOURCE, "platform": "youtube"})
    # Controlled HTTP response only: metadata must be verified against actual bytes.
    with PublicYDL(options({"max_file": 1_000_000}, Path.cwd())) as ydl:
        extractor = OwnedSampleIE(ydl)
        monkeypatch.setattr(
            extractor, "_request_webpage", lambda *a, **k: io.BytesIO(original)
        )
        info = extractor._real_extract(SOURCE)
        assert info["duration"] == 2
        assert info["formats"][0]["height"] == 180
        assert info["formats"][0]["url"] == SOURCE
        monkeypatch.setattr(
            extractor, "_request_webpage", lambda *a, **k: io.BytesIO(b"corrupted")
        )
        with pytest.raises(MediaError, match="La muestra"):
            extractor._real_extract(SOURCE)
