"""Isolated yt-dlp worker. No cookies, accounts, proxies or generic extractor."""

import json
import resource
import subprocess
import sys
from pathlib import Path

import yt_dlp
from yt_dlp.extractor import gen_extractor_classes
from yt_dlp.networking._urllib import UrllibRH

from clipdock.media import MediaError, describe
from clipdock.network import install_guard
from clipdock.security import normalize


class PublicYDL(yt_dlp.YoutubeDL):
    def __init__(self, opts):
        super().__init__(opts, auto_init=False)
        for cls in gen_extractor_classes():
            if cls.__name__.startswith(
                ("Youtube", "TikTok", "Instagram", "Facebook", "LinkedIn", "Twitter")
            ):
                self.add_info_extractor(cls())

    def build_request_director(self, handlers, preferences=None):
        # Exactly one audited Python transport. Native curl/requests fallback,
        # browser impersonation and plugin request handlers cannot bypass guard.
        return super().build_request_director([UrllibRH], None)


def options(payload, folder):
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "allow_unplayable_formats": False,
        "geo_bypass": False,
        "skip_download": False,
        "socket_timeout": 15,
        "retries": 1,
        "fragment_retries": 1,
        "extractor_retries": 1,
        "concurrent_fragment_downloads": 1,
        "max_filesize": payload["max_file"],
        "outtmpl": str(folder / "source-%(format_id)s.%(ext)s"),
        "overwrites": False,
        "fixup": "never",
        "cachedir": False,
        "cookiefile": None,
        "proxy": "",
        "enable_file_urls": False,
        "external_downloader": None,
        "js_runtimes": {"node": {}},
        "remote_components": set(),
        "hls_prefer_native": True,
        "writeinfojson": False,
        "writethumbnail": False,
    }


def inspect_media(payload):
    normalize(payload["url"])
    with PublicYDL(options(payload, Path.cwd())) as ydl:
        info = ydl.extract_info(payload["url"], download=False)
        return describe(info, payload["platform"], payload.get("max_duration", 1200))


def probe_media(path, max_duration=1200):
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-protocol_whitelist",
                "file,pipe",
                "-format_whitelist",
                "mov,matroska,webm,mpegts,mp3,aac,ogg,flac,wav",
                "-show_entries",
                "format=duration:stream=codec_type,duration",
                "-of",
                "json",
                str(path),
            ],
            check=True,
            timeout=20,
            capture_output=True,
        )
        if len(result.stdout) > 2_000_000:
            raise ValueError("probe output limit")
        info = json.loads(result.stdout)
        durations = [
            float(v)
            for v in [info.get("format", {}).get("duration")]
            + [s.get("duration") for s in info.get("streams", [])]
            if v not in (None, "N/A")
        ]
        duration = max(durations, default=0)
        if not 0 < duration <= max_duration:
            raise MediaError(
                "DURATION_LIMIT", "El medio debe durar como máximo 20 minutos."
            )
        return {
            "duration": duration,
            "video": any(
                s.get("codec_type") == "video" for s in info.get("streams", [])
            ),
            "audio": any(
                s.get("codec_type") == "audio" for s in info.get("streams", [])
            ),
        }
    except MediaError:
        raise
    except Exception:
        raise MediaError(
            "PROBE_FAILED", "No fue posible verificar el archivo descargado."
        ) from None


def download_media(payload, folder, ydl_class=PublicYDL):
    folder = Path(folder)

    def progress(event):
        total = sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())
        if total > payload["max_file"]:
            raise MediaError(
                "FILE_TOO_LARGE", "El archivo supera el tamaño máximo permitido."
            )
        if (
            sum(
                p.stat().st_size
                for p in Path(payload["root"]).rglob("*")
                if p.is_file()
            )
            > payload["disk_budget"]
        ):
            raise MediaError("DISK_LIMIT", "Se superó el límite de espacio.")
        Path(payload["progress_path"]).write_text(
            json.dumps(
                {
                    "progress": min(
                        85,
                        5
                        + int(
                            75
                            * event.get("downloaded_bytes", 0)
                            / max(
                                1,
                                event.get("total_bytes")
                                or event.get("total_bytes_estimate")
                                or payload["max_file"],
                            )
                        ),
                    )
                }
            )
        )

    opts = options(payload, folder)
    opts["progress_hooks"] = [progress]
    with ydl_class(opts) as ydl:
        info = ydl.extract_info(payload["url"], download=False)
        metadata = describe(
            info, payload["platform"], payload.get("max_duration", 1200)
        )
        if (
            payload["format"] == "mp4"
            and payload["quality"] not in metadata["qualities"]
        ):
            raise MediaError("INVALID_OPTION", "La calidad ya no está disponible.")
        formats = [
            f
            for f in info.get("formats", [])
            if f.get("protocol")
            in ("http", "https", "m3u8_native", "http_dash_segments")
            and not f.get("has_drm")
        ]
        audios = [f for f in formats if f.get("acodec") != "none"]
        selected = []
        if payload["format"] == "mp4":
            videos = [
                f
                for f in formats
                if (f.get("height") or 0) == payload["quality"]
                and f.get("vcodec") != "none"
            ]
            if not videos:
                raise MediaError("INVALID_OPTION", "No existe la calidad seleccionada.")
            video = max(videos, key=lambda f: f.get("tbr") or 0)
            selected.append(video)
            if video.get("acodec") == "none" and audios:
                selected.append(
                    max(
                        audios,
                        key=lambda f: ((f.get("vcodec") == "none"), f.get("abr") or 0),
                    )
                )
        else:
            if not audios:
                raise MediaError("NO_AUDIO", "No hay audio disponible.")
            selected.append(
                max(
                    audios,
                    key=lambda f: ((f.get("vcodec") == "none"), f.get("abr") or 0),
                )
            )
        paths = []
        for index, f in enumerate(selected):
            # Do not allow metadata-controlled output names or automatic merging.
            item = dict(info, **f)
            item.update(
                format_id=str(index),
                ext="mp4",
                formats=None,
                requested_formats=None,
                requested_downloads=None,
            )
            item.pop("__postprocessors", None)
            path = Path(ydl.prepare_filename(item))
            ydl.process_info(item)
            if not path.is_file():
                raise MediaError(
                    "DOWNLOAD_FAILED", "No se generó el archivo de origen."
                )
            paths.append(path)
    probes = [probe_media(path, payload.get("max_duration", 1200)) for path in paths]
    if payload["format"] == "mp3" and not probes[0]["audio"]:
        raise MediaError("NO_AUDIO", "El medio no contiene una pista de audio.")
    if payload["format"] == "mp4" and not probes[0]["video"]:
        raise MediaError("NO_VIDEO", "El medio no contiene una pista de video.")
    output = folder / ("output." + payload["format"])
    command = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y"]
    for path in paths:
        command += [
            "-protocol_whitelist",
            "file,pipe",
            "-format_whitelist",
            "mov,matroska,webm,mpegts,mp3,aac,ogg,flac,wav",
            "-i",
            str(path),
        ]
    if payload["format"] == "mp3":
        command += ["-vn", "-c:a", "libmp3lame", "-b:a", "192k"]
    else:
        command += ["-map", "0:v:0"]
        if len(paths) > 1:
            command += ["-map", "1:a:0"]
        else:
            command += ["-map", "0:a:0?"]
        command += [
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-threads",
            "1",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
        ]
    command += [
        "-t",
        str(payload.get("max_duration", 1200)),
        "-fs",
        str(payload["max_file"]),
        str(output),
    ]
    try:
        subprocess.run(
            command,
            check=True,
            timeout=180,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        raise MediaError("TIMEOUT", "Se superó el tiempo de conversión.") from None
    except subprocess.CalledProcessError:
        raise MediaError(
            "CONVERSION_FAILED", "No fue posible convertir el archivo."
        ) from None
    if (
        not output.is_file()
        or output.stat().st_size <= 0
        or output.stat().st_size >= payload["max_file"]
    ):
        raise MediaError(
            "FILE_TOO_LARGE", "El archivo supera el tamaño máximo permitido."
        )
    for path in paths:
        path.unlink(missing_ok=True)
    return {}


def error_for(exception):
    if isinstance(exception, MediaError):
        return {"code": exception.code, "message": exception.message}
    text = str(exception).lower()
    if "ssrf" in text:
        return {
            "code": "UNSAFE_DESTINATION",
            "message": "El destino de red no es público.",
        }
    if "drm" in text:
        return {"code": "DRM_NOT_ALLOWED", "message": "No se permiten medios con DRM."}
    if any(
        v in text
        for v in (
            "private",
            "login",
            "sign in",
            "members",
            "age",
            "geo",
            "country",
            "not available",
            "restricted",
        )
    ):
        return {
            "code": "RESTRICTED_MEDIA",
            "message": "El medio requiere acceso restringido o no está disponible públicamente.",
        }
    return {
        "code": "EXTRACTION_FAILED",
        "message": "La plataforma no permite acceder a este medio público en este momento.",
    }


def disable_external_downloaders():
    from yt_dlp.downloader.external import ExternalFD

    def forbidden(*args, **kwargs):
        raise MediaError("UNSAFE_PROTOCOL", "No se permiten descargadores externos.")

    # This blocks native HLS -> FFmpeg fallbacks as well as explicit external
    # downloaders. FFmpeg only receives already-downloaded local files below.
    ExternalFD.real_download = forbidden


def main():
    payload = json.loads(sys.stdin.buffer.read(65536))
    resource.setrlimit(
        resource.RLIMIT_FSIZE, (payload["max_file"], payload["max_file"])
    )
    install_guard()
    disable_external_downloaders()
    try:
        normalize(payload["url"])
        result = (
            inspect_media(payload)
            if sys.argv[1] == "inspect"
            else download_media(payload, Path.cwd())
        )
    except Exception as e:
        result = {"error": error_for(e)}
    Path(payload["result_path"]).write_text(json.dumps(result))


if __name__ == "__main__":
    main()
