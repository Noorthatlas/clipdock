import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from clipdock.media import MediaError


def execute(command, payload, folder, progress, cfg):
    folder = Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    # Inspection responses and payloads never contain public downloadable URLs.
    with tempfile.TemporaryDirectory(prefix="inspect-", dir=folder) as temp:
        result = Path(temp) / "result.json"
        event = Path(temp) / "progress.json"
        payload = dict(
            payload,
            result_path=str(result),
            progress_path=str(event),
            max_file=cfg.max_file,
            max_duration=cfg.max_duration,
            root=str(cfg.root.resolve()),
            disk_budget=cfg.disk_budget,
        )
        env = {
            k: v
            for k, v in os.environ.items()
            if k.lower() not in ("http_proxy", "https_proxy", "all_proxy", "no_proxy")
        }
        env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent)
        proc = subprocess.Popen(
            command,
            cwd=folder,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            proc.stdin.write(json.dumps(payload).encode())
            proc.stdin.close()
            deadline = time.monotonic() + cfg.timeout
            while True:
                size = sum(p.stat().st_size for p in cfg.root.rglob("*") if p.is_file())
                if size > cfg.disk_budget:
                    raise MediaError("DISK_LIMIT", "Se superó el límite de espacio.")
                if time.monotonic() > deadline:
                    raise MediaError(
                        "TIMEOUT", "Se superó el tiempo máximo de procesamiento."
                    )
                try:
                    progress(json.loads(event.read_text())["progress"])
                except (OSError, ValueError, KeyError):
                    pass
                if proc.poll() is not None:
                    break
                time.sleep(0.05)
            if not result.exists() or result.stat().st_size > 2_000_000:
                raise MediaError(
                    "DOWNLOAD_FAILED", "No fue posible procesar este medio público."
                )
            response = json.loads(result.read_text())
            if "error" in response:
                raise MediaError(
                    response["error"]["code"], response["error"]["message"]
                )
            if proc.returncode:
                raise MediaError(
                    "DOWNLOAD_FAILED", "No fue posible procesar este medio público."
                )
            return response
        finally:
            # Kill the entire group even when the leader exits early: ffmpeg and
            # node cannot outlive their bounded extraction/download worker.
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()


def run_worker(action, payload, folder, progress, cfg):
    from clipdock.quota import release, reserve

    if action == "download":
        # Two source files, one transient fragment, one converted output;
        # each is kernel-capped by RLIMIT_FSIZE. Reserve overhead as well.
        reserve(cfg.root, folder, 4 * cfg.max_file + 4 * 1024 * 1024, cfg.disk_budget)
    try:
        return execute(
            [sys.executable, "-m", "clipdock.worker", action],
            payload,
            folder,
            progress,
            cfg,
        )
    finally:
        if action == "download":
            release(cfg.root, folder)
