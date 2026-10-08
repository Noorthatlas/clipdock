from fastapi.testclient import TestClient


def test_authorized_inspection_and_capability_jobs(tmp_path):
    from clipdock.api import Settings, create_app

    def runner(action, payload, folder, progress):
        if action == "inspect":
            return {
                "title": "Fixture",
                "thumbnail": None,
                "platform": "youtube",
                "duration": 3,
                "qualities": [720],
                "has_audio": True,
            }
        (folder / ("output." + payload["format"])).write_bytes(
            b"authorized test fixture"
        )
        progress(80)
        return {}

    app = create_app(
        Settings(root=tmp_path, signing_key="test-key-" + "x" * 40), runner
    )
    with TestClient(app) as c:
        assert c.get("/health").status_code == 200
        assert (
            c.post(
                "/api/inspect",
                json={"url": "https://youtu.be/BaW_jenozKc", "authorized": False},
            ).status_code
            == 403
        )
        assert (
            c.post(
                "/api/inspect", json={"url": "https://evil.test/a", "authorized": True}
            ).status_code
            == 400
        )
        inspect = c.post(
            "/api/inspect",
            json={"url": "https://youtu.be/BaW_jenozKc", "authorized": True},
        ).json()
        assert inspect["platform"] == "youtube" and inspect["qualities"] == [720]
        token = inspect["token"]
        assert (
            c.post(
                "/api/jobs",
                json={
                    "token": token + "x",
                    "authorized": True,
                    "format": "mp4",
                    "quality": 720,
                },
            ).status_code
            == 400
        )
        assert (
            c.post(
                "/api/jobs",
                json={
                    "token": token,
                    "authorized": True,
                    "format": "mp4",
                    "quality": 1080,
                },
            ).status_code
            == 400
        )
        job = c.post(
            "/api/jobs",
            json={"token": token, "authorized": True, "format": "mp4", "quality": 720},
        ).json()
        assert c.get("/api/jobs/" + job["id"]).status_code == 404
        import time

        for _ in range(100):
            state = c.get(
                "/api/jobs/" + job["id"], params={"secret": job["secret"]}
            ).json()
            if state["status"] == "completed":
                break
            time.sleep(0.01)
        assert state["status"] == "completed"
        assert state["progress"] == 100
        assert c.get(state["download_url"]).content == b"authorized test fixture"
        assert c.get("/api/jobs/" + job["id"] + "/file?secret=wrong").status_code == 404
        assert (
            c.post(
                "/api/jobs",
                json={
                    "token": token,
                    "authorized": True,
                    "format": "exe",
                    "quality": 720,
                },
            ).json()["error"]["code"]
            == "INVALID_REQUEST"
        )
