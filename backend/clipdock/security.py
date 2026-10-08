"""Strict public post identifiers; no arbitrary extractor or share redirects."""

import re
from urllib.parse import parse_qs, urlsplit


class Unsafe(ValueError):
    pass


HOSTS = {
    "youtube.com": "youtube",
    "www.youtube.com": "youtube",
    "m.youtube.com": "youtube",
    "youtu.be": "youtube",
    "tiktok.com": "tiktok",
    "www.tiktok.com": "tiktok",
    "instagram.com": "instagram",
    "www.instagram.com": "instagram",
    "facebook.com": "facebook",
    "www.facebook.com": "facebook",
    "m.facebook.com": "facebook",
    "linkedin.com": "linkedin",
    "www.linkedin.com": "linkedin",
    "x.com": "x",
    "www.x.com": "x",
    "twitter.com": "x",
    "www.twitter.com": "x",
}


def normalize(url):
    try:
        p = urlsplit(url)
        if (
            p.scheme != "https"
            or p.username
            or p.password
            or p.port
            or p.fragment
            or any(c.isspace() for c in url)
            or "\\" in url
        ):
            raise Unsafe("URL no permitida")
        platform = HOSTS[p.netloc]
        path = p.path
        q = parse_qs(p.query, strict_parsing=True)
        if platform == "youtube":
            if set(q) - {"v"}:
                raise Unsafe("Listas no permitidas")
            ident = (
                path[1:]
                if p.netloc == "youtu.be"
                else (
                    q.get("v", [""])[0]
                    if path == "/watch"
                    else path.removeprefix("/shorts/")
                )
            )
            if not re.fullmatch(r"[A-Za-z0-9_-]{11}", ident) or any(
                len(v) != 1 for v in q.values()
            ):
                raise Unsafe("ID inválido")
            return "https://www.youtube.com/watch?v=" + ident, platform
        patterns = {
            "tiktok": r"/@[A-Za-z0-9_.-]+/video/\d{15,22}/?",
            "instagram": r"/(?:p|reel|tv)/[A-Za-z0-9_-]{5,64}/?",
            "linkedin": r"/posts/[A-Za-z0-9_-]+[-_](?:activity|ugcPost)-\d{15,22}-[A-Za-z0-9_-]+/?",
            "x": r"/[A-Za-z0-9_]{1,15}/status/\d{8,22}/?",
        }
        if platform == "facebook":
            valid = (
                path in ("/watch", "/watch/")
                and set(q) == {"v"}
                and len(q["v"]) == 1
                and re.fullmatch(r"\d{8,22}", q["v"][0])
            ) or (
                not q
                and re.fullmatch(
                    r"/(?:reel/\d{8,22}|[A-Za-z0-9_.-]+/videos/\d{8,22})/?", path
                )
            )
        else:
            valid = not q and re.fullmatch(patterns[platform], path)
        if not valid:
            raise Unsafe("ID inválido")
        return url, platform
    except (KeyError, ValueError) as e:
        raise Unsafe("URL pública no permitida") from e
