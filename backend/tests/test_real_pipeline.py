"""Real test-owned media, served ONLY to an explicitly injected test extractor."""

import functools
import json
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest


@pytest.mark.parametrize("unknown", [False, True])
def test_real_ytdlp_ffmpeg_authorized_fixture(tmp_path, unknown):
    import yt_dlp
    from yt_dlp.extractor.common import InfoExtractor

    from clipdock.worker import download_media

    source = tmp_path / "owner-test.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=320x180:d=2",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=2",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            "-y",
            str(source),
        ],
        check=True,
    )
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        functools.partial(SimpleHTTPRequestHandler, directory=str(tmp_path)),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/owner-test.mp4"

    class OwnerFixtureIE(InfoExtractor):
        _VALID_URL = r"http://127\.0\.0\.1:\d+/owner-test\.mp4"

        def _real_extract(self, url):
            return {
                "id": "owner-test",
                "title": "Generated owner-authorized test asset",
                "duration": None if unknown else 2,
                "formats": [
                    {
                        "format_id": "fixture",
                        "url": url,
                        "ext": "mp4",
                        "protocol": "http",
                        "height": None if unknown else 180,
                        "vcodec": None if unknown else "h264",
                        "acodec": None if unknown else "aac",
                    }
                ],
            }

    class FixtureYDL(yt_dlp.YoutubeDL):
        def __init__(self, opts):
            super().__init__(opts, auto_init=False)
            self.add_info_extractor(OwnerFixtureIE())

    try:
        for fmt in ("mp4", "mp3"):
            folder = tmp_path / fmt
            folder.mkdir()
            payload = {
                "url": url,
                "platform": "youtube",
                "format": fmt,
                "quality": 0 if unknown else 180,
                "max_file": 10_000_000,
                "disk_budget": 100_000_000,
                "root": str(tmp_path),
                "progress_path": str(folder / "progress.json"),
                "metadata": {"qualities": [180], "has_audio": True},
            }
            download_media(payload, folder, FixtureYDL)
            output = folder / f"output.{fmt}"
            probe = json.loads(
                subprocess.check_output(
                    [
                        "ffprobe",
                        "-v",
                        "error",
                        "-show_streams",
                        "-show_format",
                        "-of",
                        "json",
                        str(output),
                    ]
                )
            )
            assert 1.8 <= float(probe["format"]["duration"]) <= 2.5
            types = {s["codec_type"] for s in probe["streams"]}
            assert types == ({"video", "audio"} if fmt == "mp4" else {"audio"})
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
