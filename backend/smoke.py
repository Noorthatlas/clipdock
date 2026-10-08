"""Read-only public upstream test-fixture metadata smoke; NEVER downloads media."""

import json
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from yt_dlp.extractor import gen_extractor_classes

from clipdock.api import Settings
from clipdock.media import MediaError
from clipdock.security import Unsafe, normalize
from clipdock.supervisor import run_worker

NAMES = {
    "YoutubeIE": "youtube",
    "TikTokIE": "tiktok",
    "InstagramIE": "instagram",
    "FacebookIE": "facebook",
    "LinkedInIE": "linkedin",
    "TwitterIE": "x",
}


def main():
    candidates = []
    for cls in gen_extractor_classes():
        if cls.__name__ not in NAMES:
            continue
        for item in cls.get_testcases():
            if item.get("skip") or item.get("only_matching"):
                continue
            try:
                url, platform = normalize(item["url"])
            except (Unsafe, KeyError):
                continue
            candidates.append(
                {"extractor": cls.__name__, "platform": platform, "url": url}
            )
            break

    def smoke(item):
        with tempfile.TemporaryDirectory(prefix="clipdock-smoke-") as folder:
            cfg = Settings(root=Path(folder), timeout=25)
            try:
                result = run_worker("inspect", item, Path(folder), lambda n: None, cfg)
                return dict(item, status="metadata_ok", metadata=result)
            except MediaError as e:
                return dict(
                    item,
                    status="metadata_failed",
                    error={"code": e.code, "message": e.message},
                )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(smoke, candidates))
    report = {
        "mode": "metadata_only_no_remote_media_downloads",
        "results": results,
        "count": len(results),
    }
    Path("smoke-results.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
