import hashlib
import json
import os
import secrets
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from fastapi.testclient import TestClient


def test_real_uvicorn_boot_and_invalid_destination(tmp_path):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = dict(
        os.environ,
        CLIPDOCK_SIGNING_KEY=secrets.token_urlsafe(48),
        CLIPDOCK_DATA_DIR=str(tmp_path),
    )
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--no-access-log",
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 15
        while True:
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/health", timeout=1
                ) as response:
                    assert json.load(response) == {"status": "ok"}
                break
            except OSError:
                assert process.poll() is None
                if time.monotonic() > deadline:
                    raise AssertionError("uvicorn startup deadline") from None
                time.sleep(0.05)
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/inspect",
            data=json.dumps(
                {"url": "https://127.0.0.1/private", "authorized": True}
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(request, timeout=2)
        except urllib.error.HTTPError as error:
            assert error.code == 400
            assert json.load(error)["error"]["code"] == "INVALID_URL"
        else:
            raise AssertionError("SSRF input accepted")
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def test_durable_restart_recovery_and_startup_ttl_cleanup(tmp_path):
    from clipdock.api import Settings, create_app

    db = sqlite3.connect(tmp_path / "jobs.sqlite3")
    db.execute(
        "CREATE TABLE jobs (id TEXT PRIMARY KEY, secret TEXT, body TEXT, created REAL)"
    )
    secret = "known-test-capability"
    ids = ["a" * 32, "b" * 32]
    for ident, status, created in [
        (ids[0], "processing", time.time()),
        (ids[1], "completed", time.time() - 4000),
    ]:
        folder = tmp_path / ident
        folder.mkdir()
        (folder / "output.mp4").write_bytes(b"test")
        db.execute(
            "INSERT INTO jobs VALUES (?,?,?,?)",
            (
                ident,
                hashlib.sha256(secret.encode()).hexdigest(),
                json.dumps(
                    {"id": ident, "status": status, "progress": 10, "format": "mp4"}
                ),
                created,
            ),
        )
    db.commit()
    db.close()
    orphan = tmp_path / ("c" * 32)
    orphan.mkdir()
    with TestClient(
        create_app(Settings(root=tmp_path, signing_key="x" * 40), lambda *args: {})
    ) as c:
        recovered = c.get("/api/jobs/" + ids[0], params={"secret": secret}).json()
        assert (
            recovered["status"] == "failed"
            and recovered["error"]["code"] == "SERVICE_RESTARTED"
        )
        assert (
            c.get("/api/jobs/" + ids[1], params={"secret": secret}).status_code == 404
        )
        assert not any((tmp_path / ident).exists() for ident in ids)
        assert not orphan.exists()
