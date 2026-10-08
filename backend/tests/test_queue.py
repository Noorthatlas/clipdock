import threading
import time

from fastapi.testclient import TestClient


def test_queue_two_workers_and_monotonic_progress(tmp_path):
    from clipdock.api import Settings, create_app

    release = threading.Event()
    lock = threading.Lock()
    active = 0
    peak = 0

    def runner(action, payload, folder, progress):
        nonlocal active, peak
        if action == "inspect":
            return {
                "title": "Fixture",
                "thumbnail": None,
                "platform": "youtube",
                "duration": 2,
                "qualities": [720],
                "has_audio": True,
            }
        with lock:
            active += 1
            peak = max(peak, active)
        progress(80)
        progress(10)
        release.wait(5)
        (folder / "output.mp4").write_bytes(b"test")
        with lock:
            active -= 1
        return {}

    with TestClient(
        create_app(Settings(root=tmp_path, signing_key="x" * 40, queue_cap=3), runner)
    ) as c:
        try:
            token = c.post(
                "/api/inspect",
                json={"url": "https://youtu.be/BaW_jenozKc", "authorized": True},
            ).json()["token"]
            payload = {
                "token": token,
                "authorized": True,
                "format": "mp4",
                "quality": 720,
            }
            jobs = [c.post("/api/jobs", json=payload).json() for _ in range(3)]
            assert c.post("/api/jobs", json=payload).status_code == 429
            for _ in range(100):
                state = c.get(
                    "/api/jobs/" + jobs[0]["id"], params={"secret": jobs[0]["secret"]}
                ).json()
                if active == 2 and state["progress"] >= 10:
                    break
                time.sleep(0.01)
            assert peak == 2
            assert state["progress"] == 80
        finally:
            release.set()
