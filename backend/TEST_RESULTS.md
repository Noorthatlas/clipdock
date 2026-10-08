# Backend verification — actual executions

## Final local commands and results

Executed in `/opt/data/projects/clipdock/backend`:

```text
$ uv run ruff check clipdock tests main.py smoke.py
All checks passed!

$ uv run pytest -q
......................                                                   [100%]
22 passed in 6.39s

$ uv lock --check
Resolved 42 packages in 2ms
```

`uv sync --frozen` succeeded against the committed-ready `uv.lock`. Installed runtime: Python 3.12.9, yt-dlp 2026.08.19 with `[default]`/EJS, Node v26.5.1, FFmpeg/FFprobe 7.1.5. Docker is available as a client, but `docker info` returned `Cannot connect to the Docker daemon at unix:///var/run/docker.sock`; therefore **the image was not built or run** here.

## Real execution, not only mocks

- The real-pipeline test generated a two-second 320×180 blue video plus a synthesized 440 Hz tone with FFmpeg, served it on an isolated local HTTP server, downloaded it with the actual yt-dlp HTTP downloader, converted it with actual FFmpeg into MP4 and MP3, and checked real output duration and stream types with FFprobe.
- That real pipeline ran twice: known metadata and unknown duration/dimensions/codecs (`quality=0`, Original). Both MP4 and MP3 passed in both variants.
- `tests/assets/owner-test.mp4` was generated and independently probed: **22,249 bytes**, **2.000000 seconds**, **H.264 video 320×180**, **AAC audio**. Its CC0 license and regeneration command are in `tests/assets/README.md`.
- A real Uvicorn subprocess was started on a local port. An HTTP request to `/health` returned `{"status":"ok"}`. An authorized inspection request targeting `https://127.0.0.1/private` returned HTTP 400 with `INVALID_URL`. The test terminated the server afterward; no development server is left running.
- Other API tests use an injected deterministic runner to verify consent, schema errors, signed token tampering, unavailable qualities, secret-protected status/download, relative full download URLs, actual streamed file bytes, queue saturation and two-worker admission, monotonic progress, explicit CORS and request-body limits.
- SQLite restart tests verified interrupted-task failure, expired file/record cleanup and orphan-directory removal at startup.
- Actual short child processes exercised timeout and aggregate disk-overrun termination. Socket tests rejected loopback/private/reserved/mapped addresses and non-public DNS destinations. External downloader fallback and local playlist demuxing were blocked.

The fixture extractor is defined inside tests and injected as a Python class. Production still rejects localhost and arbitrary URL inputs; there is no runtime fixture flag or production generic-extractor exception.

## RED → GREEN evidence

Tests were written and executed before their implementation slices. Observed failures included missing URL-security, network, metadata, API, supervisor and worker modules; missing Original/unknown-metadata support; unknown LinkedIn post shapes; absent Spanish error envelopes; regressing progress (10 instead of 80); missing environment settings; missing explicit CORS and body-size admission; and acceptance of a local HLS playlist before demuxer restriction. Each slice was followed by a passing run; the final suite above is clean. Some later tests are regression coverage for already-implemented behavior, not additional production features.

## Read-only live platform smoke

`TMPDIR=/opt/data/cache/scratch uv run python smoke.py` examined **six** public upstream yt-dlp extractor fixtures. It made metadata requests only; **no remote video was downloaded**. Exact structured results are saved in `smoke-results.json`.

| Platform | Fixture | Observed outcome |
|---|---|---|
| YouTube | `IB3lcPjvWLA` | `RESTRICTED_MEDIA` |
| Facebook | `radiokicksfm/videos/3676516585958356` | `EXTRACTION_FAILED` |
| Instagram | `reel/Chunk8-jurw` | Metadata obtained; duration null; qualities `[0,840,1280]`; has_audio false |
| LinkedIn | `ugcPost-6850898786781339649-mM20` | Metadata obtained; duration null; qualities `[0]`; has_audio true |
| TikTok | `barudakhb_/video/6984138651336838402` | `RESTRICTED_MEDIA` |
| X/Twitter | `starwars/status/665052190608723968` | `RESTRICTED_MEDIA` |

These are real observed service-level results, not claims that all upstream failures have one particular root cause. Presence in yt-dlp's extractor registry/support list does not guarantee live compatibility. **Six-platform remote downloads have not been verified.** No Big Buck Bunny or other remote media was downloaded.

Official upstream README and supported-sites material were fetched from the yt-dlp GitHub repository; the README confirms `[default]` and JavaScript runtime/EJS requirements. The installed extractor fixtures supplied the six smoke URLs.

## Contract clarifications and remaining caveats

1. `quality:0` / `qualities:[0,...]` represents **Original**, not a zero-height video. `duration:null` represents genuinely unknown duration. The frontend must support both. Unknown codecs are provisional until local FFprobe verification; missing audio fails MP3 cleanly with `NO_AUDIO`.
2. Single-process architecture is enforced by a data-directory lock; there is no Redis/distributed worker or cross-instance queue. SQLite/files survive only when the underlying data directory survives.
3. Reservations, progress checks, a 50 ms aggregate monitor and kernel per-file size limits prevent ordinary overcommit and terminate over-budget workers. They are **not a physical instantaneous filesystem quota** for all auxiliary/external writes. A strictly hard aggregate physical cap requires a filesystem/container volume quota as documented; that deployment constraint was not installed or verified here.
4. The application checks effective socket IPs and DNS answers and forces the Python Urllib transport; FFmpeg network downloader fallbacks are blocked. Node is used solely for local yt-dlp EJS execution. A deployment-level egress policy remains useful defense in depth. No proxy bypass or cookie/login workflow was attempted.
5. Dockerfile includes Python, FFmpeg and Node 22 and uses `$PORT`; the image build remains unverified because the daemon is unavailable.
6. `.env.render.example` is only a conservative low-resource configuration example. **No hosting resource was created, no production deployment occurred, and no payment method or free-hosting quota assumptions were made.**
7. `authorized:true` is user consent/attestation, not proof of ownership. Only generated owned media was used for download tests.

## Start for local parent-agent review

```sh
cd /opt/data/projects/clipdock/backend
uv sync --frozen
export CLIPDOCK_SIGNING_KEY="$(uv run python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export CLIPDOCK_DATA_DIR=./data
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1 --no-access-log
```

Keep the signing key stable if restarting with the same data directory. `.env` is not loaded automatically. No secrets have been added to the backend files and no commit was made by the implementation subagent.

## Parent-agent audit corrections and revalidation

The independent audit found the implicit yt-dlp geographic bypass default and separate inspection/download concurrency counters. The parent wrote regression tests and observed failures before changing production code. `geo_bypass=False` now prevents the permitted LinkedIn extractor from generating a fake geographic forwarding IP. One shared semaphore now limits both execution types: a second inspection while a download owns the only slot returns HTTP429/BUSY.

```text
uv run pytest tests/test_geo_policy.py -q      # RED: fake forwarding IP generated; GREEN: 1 passed
uv run pytest tests/test_shared_concurrency.py -q  # RED: HTTP200 instead of 429; GREEN: 1 passed
uv run pytest -q
24 passed in 7.22s
uv run ruff check .
All checks passed!
```

The Render example now includes the exact public frontend origin for CORS. The parent deployed only the disconnected frontend to Vercel Production; backend remains local. See root `VERIFICATION.md` for the current deployment state rather than interpreting the original subagent snapshot as a project-wide claim.

