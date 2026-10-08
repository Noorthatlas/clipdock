import threading

from fastapi.testclient import TestClient


def test_download_and_inspection_share_single_execution_slot(tmp_path):
    from clipdock.api import Settings, create_app

    started, release = threading.Event(), threading.Event()
    lock = threading.Lock()
    active = peak = 0

    def runner(action, payload, folder, progress):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        try:
            if action == "download":
                started.set()
                assert release.wait(5)
                (folder / "output.mp4").write_bytes(b"owned fixture")
                return {}
            return {
                "title": "Owned fixture",
                "thumbnail": None,
                "platform": "youtube",
                "duration": 2,
                "qualities": [720],
                "has_audio": True,
            }
        finally:
            with lock:
                active -= 1

    config = Settings(root=tmp_path, signing_key="test" * 10, concurrency=1)
    with TestClient(create_app(config, runner)) as client:
        try:
            request = {"url": "https://youtu.be/BaW_jenozKc", "authorized": True}
            token = client.post("/api/inspect", json=request).json()["token"]
            response = client.post(
                "/api/jobs",
                json={"token": token, "authorized": True, "format": "mp4", "quality": 720},
            )
            assert response.status_code == 202
            assert started.wait(3)
            response = client.post("/api/inspect", json=request)
            assert response.status_code == 429
            assert response.json()["error"]["code"] == "BUSY"
            assert peak == 1
        finally:
            release.set()
