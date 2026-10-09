"""Single-process service. Durable job records, two workers, capability URLs."""

import asyncio
import fcntl
import hashlib
import hmac
import json
import os
import secrets
import shutil
import sqlite3
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlencode

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from itsdangerous import BadSignature, URLSafeTimedSerializer
from pydantic import BaseModel, ConfigDict, StrictBool, StrictInt

from clipdock.media import MediaError
from clipdock.sample import SAMPLE_URL
from clipdock.security import Unsafe, normalize


@dataclass
class Settings:
    root: Path = Path(os.environ.get("CLIPDOCK_DATA_DIR", "data"))
    signing_key: str = os.environ.get("CLIPDOCK_SIGNING_KEY", "")
    queue_cap: int = 8
    ttl: int = 3600
    token_ttl: int = 600
    disk_budget: int = 1024 * 1024 * 1024
    max_file: int = 64 * 1024 * 1024
    concurrency: int = 2
    max_duration: int = 1200
    timeout: int = 300

    @classmethod
    def from_env(cls):
        settings = cls()
        names = {
            "queue_cap": "QUEUE_CAP",
            "ttl": "JOB_TTL_SECONDS",
            "token_ttl": "TOKEN_TTL_SECONDS",
            "disk_budget": "DISK_BUDGET_BYTES",
            "max_file": "MAX_FILE_BYTES",
            "timeout": "TIMEOUT_SECONDS",
            "concurrency": "CONCURRENCY",
            "max_duration": "MAX_DURATION_SECONDS",
        }
        for field, suffix in names.items():
            value = int(os.environ.get("CLIPDOCK_" + suffix, getattr(settings, field)))
            if value <= 0:
                raise ValueError("Los límites deben ser positivos")
            setattr(settings, field, value)
        if settings.concurrency > 2 or settings.max_duration > 1200:
            raise ValueError("Concurrencia máxima 2; duración máxima 1200 segundos")
        settings.root = Path(os.environ.get("CLIPDOCK_DATA_DIR", "data"))
        settings.signing_key = os.environ.get("CLIPDOCK_SIGNING_KEY", "")
        return settings


class InspectBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str
    authorized: StrictBool


class JobBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str
    authorized: StrictBool
    format: Literal["mp4", "mp3"]
    quality: StrictInt = 720


class SampleBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    authorized: StrictBool


class APIError(Exception):
    def __init__(self, code, message, status=400):
        self.code, self.message, self.status = code, message, status


def create_app(settings=None, runner=None):
    cfg = settings or Settings.from_env()
    if runner is None:
        from clipdock.supervisor import run_worker

        def runner(action, payload, folder, progress):
            return run_worker(action, payload, folder, progress, cfg)

    state = {}

    def query(sql, args=()):
        return state["db"].execute(sql, args)

    def update(ident, **changes):
        row = query("SELECT body FROM jobs WHERE id=?", (ident,)).fetchone()
        if row:
            body = json.loads(row[0])
            body.update(changes)
            query("UPDATE jobs SET body=? WHERE id=?", (json.dumps(body), ident))
            state["db"].commit()

    def cleanup():
        cutoff = time.time() - cfg.ttl
        for ident, body, created in query(
            "SELECT id,body,created FROM jobs"
        ).fetchall():
            item = json.loads(body)
            if created < cutoff and item["status"] not in ("queued", "processing"):
                shutil.rmtree(cfg.root / ident, ignore_errors=True)
                query("DELETE FROM jobs WHERE id=?", (ident,))
        state["db"].commit()

    async def worker():
        while True:
            ident, payload = await state["queue"].get()
            try:
                loop = asyncio.get_running_loop()

                def progress(n, loop=loop, ident=ident):
                    loop.call_soon_threadsafe(update_progress, ident, n)

                async with state["runner_slots"]:
                    update(ident, status="processing", progress=1)
                    await asyncio.to_thread(
                        runner, "download", payload, cfg.root / ident, progress
                    )
                if not (cfg.root / ident / ("output." + payload["format"])).is_file():
                    raise MediaError("DOWNLOAD_FAILED", "No se generó el archivo.")
                update(ident, status="completed", progress=100)
            except Exception as e:
                error = (
                    {"code": e.code, "message": e.message}
                    if isinstance(e, MediaError)
                    else {
                        "code": "DOWNLOAD_FAILED",
                        "message": "No fue posible descargar este medio público.",
                    }
                )
                update(ident, status="failed", error=error)
                shutil.rmtree(cfg.root / ident, ignore_errors=True)
            finally:
                state["queue"].task_done()

    def update_progress(ident, n):
        row = query("SELECT body FROM jobs WHERE id=?", (ident,)).fetchone()
        if row:
            body = json.loads(row[0])
            if body["status"] == "processing":
                update(ident, progress=max(body["progress"], min(99, int(n))))

    async def janitor():
        while True:
            await asyncio.sleep(30)
            cleanup()

    @asynccontextmanager
    async def lifespan(app):
        if len(cfg.signing_key) < 32:
            raise RuntimeError("CLIPDOCK_SIGNING_KEY debe tener al menos 32 caracteres")
        cfg.root.mkdir(parents=True, exist_ok=True)
        lock = open(cfg.root / "service.lock", "a")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            lock.close()
            raise RuntimeError(
                "Solo se permite un proceso por directorio de datos"
            ) from None
        db = sqlite3.connect(cfg.root / "jobs.sqlite3")
        db.execute(
            "CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, secret TEXT, body TEXT, created REAL)"
        )
        state.update(
            db=db,
            queue=asyncio.Queue(maxsize=cfg.queue_cap),
            signer=URLSafeTimedSerializer(cfg.signing_key, salt="clipdock-inspect-v1"),
            runner_slots=asyncio.Semaphore(cfg.concurrency),
        )
        for ident, body in query("SELECT id,body FROM jobs").fetchall():
            if json.loads(body)["status"] in ("queued", "processing"):
                update(
                    ident,
                    status="failed",
                    error={
                        "code": "SERVICE_RESTARTED",
                        "message": "La tarea fue interrumpida al reiniciar el servicio.",
                    },
                )
                shutil.rmtree(cfg.root / ident, ignore_errors=True)
        # Remove orphan directories only when they match generated job IDs.
        known = {r[0] for r in query("SELECT id FROM jobs")}
        import re

        for path in cfg.root.iterdir():
            if (
                path.is_dir()
                and re.fullmatch("[0-9a-f]{32}", path.name)
                and path.name not in known
            ):
                shutil.rmtree(path)
        cleanup()
        tasks = [asyncio.create_task(worker()) for _ in range(cfg.concurrency)] + [
            asyncio.create_task(janitor())
        ]
        try:
            yield
        finally:
            # Gracefully finish bounded in-flight work before closing SQLite.
            try:
                await asyncio.wait_for(state["queue"].join(), timeout=cfg.timeout + 10)
            except TimeoutError:
                pass
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            db.close()
            lock.close()

    app = FastAPI(title="ClipDock", lifespan=lifespan)
    app.state.settings = cfg
    origins = [
        v.strip()
        for v in os.environ.get("CLIPDOCK_CORS_ORIGINS", "").split(",")
        if v.strip()
    ]
    if origins:
        from urllib.parse import urlsplit

        from fastapi.middleware.cors import CORSMiddleware

        for origin in origins:
            parsed = urlsplit(origin)
            if (
                parsed.scheme != "https"
                or not parsed.netloc
                or parsed.path
                or parsed.query
                or parsed.fragment
                or parsed.username
            ):
                raise ValueError("CORS requiere orígenes HTTPS exactos")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
            allow_credentials=False,
        )
    from starlette.exceptions import HTTPException

    @app.exception_handler(HTTPException)
    async def http_error(request, e):
        return JSONResponse(
            {
                "error": {
                    "code": "NOT_FOUND" if e.status_code == 404 else "HTTP_ERROR",
                    "message": "Recurso no encontrado."
                    if e.status_code == 404
                    else "Solicitud no permitida.",
                }
            },
            status_code=e.status_code,
        )

    @app.exception_handler(Exception)
    async def internal_error(request, e):
        return JSONResponse(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Error interno del servicio.",
                }
            },
            status_code=500,
        )

    @app.exception_handler(APIError)
    async def api_error(request, e):
        return JSONResponse(
            {"error": {"code": e.code, "message": e.message}}, status_code=e.status
        )

    @app.exception_handler(RequestValidationError)
    async def invalid(request, e):
        return JSONResponse(
            {"error": {"code": "INVALID_REQUEST", "message": "Solicitud inválida."}},
            status_code=422,
        )

    @app.exception_handler(MediaError)
    async def media_error(request, e):
        return JSONResponse(
            {"error": {"code": e.code, "message": e.message}}, status_code=400
        )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    def authorize(value):
        if value is not True:
            raise APIError(
                "AUTHORIZATION_REQUIRED",
                "Debes ser propietario o tener permiso para descargar.",
                403,
            )

    @app.post("/api/inspect")
    async def inspect_media(body: InspectBody):
        authorize(body.authorized)
        if len(body.url) > 2048:
            raise APIError("INVALID_URL", "URL no permitida.")
        try:
            url, platform = normalize(body.url)
        except Unsafe:
            raise APIError(
                "INVALID_URL", "Introduce una URL pública compatible."
            ) from None
        return await inspect_source(url, platform)

    @app.post("/api/sample/inspect")
    async def inspect_sample(body: SampleBody):
        authorize(body.authorized)
        return dict(await inspect_source(SAMPLE_URL, "sample"), source_url=SAMPLE_URL)

    async def inspect_source(url, platform):
        if state["runner_slots"].locked():
            raise APIError("BUSY", "Servicio ocupado. Inténtalo más tarde.", 429)
        await state["runner_slots"].acquire()
        try:
            result = await asyncio.to_thread(
                runner,
                "inspect",
                {"url": url, "platform": platform},
                cfg.root,
                lambda n: None,
            )
        except MediaError:
            raise
        except Exception:
            raise MediaError(
                "EXTRACTION_FAILED", "No fue posible inspeccionar este medio público."
            ) from None
        finally:
            state["runner_slots"].release()
        token = state["signer"].dumps({"url": url, "metadata": result})
        return dict(result, token=token)

    @app.post("/api/jobs", status_code=202)
    async def jobs(body: JobBody):
        authorize(body.authorized)
        if len(body.token) > 16384:
            raise APIError("INVALID_TOKEN", "Inspección inválida o caducada.") from None
        try:
            data = state["signer"].loads(body.token, max_age=cfg.token_ttl)
        except BadSignature:
            raise APIError("INVALID_TOKEN", "Inspección inválida o caducada.") from None
        meta = data["metadata"]
        if (body.format == "mp4" and body.quality not in meta["qualities"]) or (
            body.format == "mp3" and not meta["has_audio"]
        ):
            raise APIError(
                "INVALID_OPTION", "El formato o la calidad no están disponibles."
            )
        active = sum(
            json.loads(row[0])["status"] in ("queued", "processing")
            for row in query("SELECT body FROM jobs")
        )
        if active >= cfg.queue_cap or state["queue"].full():
            raise APIError("QUEUE_FULL", "La cola está llena.", 429)
        if (
            sum(p.stat().st_size for p in cfg.root.rglob("*") if p.is_file())
            >= cfg.disk_budget
        ):
            raise APIError("DISK_LIMIT", "No hay espacio disponible.", 429)
        ident = secrets.token_hex(16)
        secret = secrets.token_urlsafe(32)
        record = {"id": ident, "status": "queued", "progress": 0, "format": body.format}
        query(
            "INSERT INTO jobs VALUES (?,?,?,?)",
            (
                ident,
                hashlib.sha256(secret.encode()).hexdigest(),
                json.dumps(record),
                time.time(),
            ),
        )
        state["db"].commit()
        folder = cfg.root / ident
        folder.mkdir()
        state["queue"].put_nowait(
            (
                ident,
                {
                    "url": data["url"],
                    "platform": meta["platform"],
                    "format": body.format,
                    "quality": body.quality,
                    "metadata": meta,
                },
            )
        )
        return {"id": ident, "secret": secret, "status": "queued"}

    def get_job(ident, secret):
        row = query(
            "SELECT secret,body,created FROM jobs WHERE id=?", (ident,)
        ).fetchone()
        digest = hashlib.sha256((secret or "").encode()).hexdigest()
        if (
            not row
            or not hmac.compare_digest(row[0], digest)
            or (
                time.time() - row[2] > cfg.ttl
                and json.loads(row[1])["status"] not in ("queued", "processing")
            )
        ):
            raise APIError("NOT_FOUND", "Tarea no encontrada.", 404)
        return json.loads(row[1])

    @app.get("/api/jobs/{ident}")
    async def job(ident: str, secret: str = ""):
        record = get_job(ident, secret)
        result = {k: v for k, v in record.items() if k != "format"}
        if record["status"] == "completed":
            result["download_url"] = f"/api/jobs/{ident}/file?" + urlencode(
                {"secret": secret}
            )
        return result

    @app.get("/api/jobs/{ident}/file")
    async def file(ident: str, secret: str = ""):
        record = get_job(ident, secret)
        if record["status"] != "completed":
            raise APIError("NOT_READY", "El archivo todavía no está disponible.", 409)
        path = cfg.root / ident / ("output." + record["format"])
        if not path.is_file():
            raise APIError("NOT_FOUND", "Archivo no encontrado.", 404)
        return FileResponse(
            path,
            media_type="video/mp4" if record["format"] == "mp4" else "audio/mpeg",
            filename="clipdock." + record["format"],
            headers={
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
            },
        )

    @app.middleware("http")
    async def no_cache(request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            chunks = []
            count = 0
            async for chunk in request.stream():
                count += len(chunk)
                if count > 32768:
                    return JSONResponse(
                        {
                            "error": {
                                "code": "REQUEST_TOO_LARGE",
                                "message": "La solicitud supera el tamaño máximo.",
                            }
                        },
                        status_code=413,
                    )
                chunks.append(chunk)
            request._body = b"".join(chunks)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    return app
