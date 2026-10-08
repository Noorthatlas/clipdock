from clipdock.network import thumbnail


class MediaError(ValueError):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)


def describe(info, platform, max_duration=1200):
    if info.get("_type", "video") != "video":
        raise MediaError(
            "PLAYLIST_NOT_ALLOWED", "No se permiten listas de reproducción."
        )
    if info.get("is_live") or info.get("live_status") not in (None, "not_live"):
        raise MediaError("LIVE_NOT_ALLOWED", "No se permiten transmisiones en vivo.")
    if info.get("has_drm") or any(f.get("has_drm") for f in info.get("formats", [])):
        raise MediaError("DRM_NOT_ALLOWED", "No se permiten medios con DRM.")
    if (
        info.get("availability") not in (None, "public", "unlisted")
        or (info.get("age_limit") or 0) >= 18
    ):
        raise MediaError(
            "RESTRICTED_MEDIA", "Solo se permiten medios públicos sin restricciones."
        )
    duration = info.get("duration")
    if duration is not None and (
        not isinstance(duration, (int, float)) or not 0 < duration <= max_duration
    ):
        raise MediaError(
            "DURATION_LIMIT", "El medio debe durar como máximo 20 minutos."
        )
    formats = [
        f
        for f in info.get("formats", [])
        if f.get("protocol") in ("http", "https", "m3u8_native", "http_dash_segments")
        and not f.get("has_drm")
    ]
    heights = sorted(
        {
            int(f["height"])
            for f in formats
            if f.get("height")
            and f.get("vcodec") != "none"
            and float(f["height"]).is_integer()
        }
    )
    if any(not f.get("height") and f.get("vcodec") != "none" for f in formats):
        heights.insert(0, 0)
    audio = any(f.get("acodec") != "none" for f in formats)
    if not heights and not audio:
        raise MediaError("NO_FORMATS", "No hay formatos públicos compatibles.")
    return {
        "title": str(info.get("title") or "Video")[:300],
        "thumbnail": thumbnail(info.get("thumbnail")),
        "platform": platform,
        "duration": duration,
        "qualities": heights,
        "has_audio": audio,
    }
