"""One immutable, first-party CC0 diagnostic source; never an arbitrary URL."""

import hashlib
import re

from yt_dlp.extractor.common import InfoExtractor

from clipdock.media import MediaError
from clipdock.security import Unsafe, normalize

SAMPLE_URL = (
    "https://raw.githubusercontent.com/Noorthatlas/clipdock/"
    "90089cc28480b1195c955e5333d06cb886f9a2f9/backend/tests/assets/owner-test.mp4"
)
SAMPLE_SHA256 = "ead9b689f8297aa5e2e9e0785e74592068e9b4aeb7406687a3010367bb028126"


def validate_source(payload):
    if payload.get("platform") == "sample":
        if payload["url"] != SAMPLE_URL:
            raise MediaError("INVALID_URL", "Solo se permite la muestra propia fijada.")
        return
    try:
        normalize(payload["url"])
    except Unsafe:
        raise MediaError(
            "INVALID_URL", "Introduce una URL pública compatible."
        ) from None


class OwnedSampleIE(InfoExtractor):
    # No GenericIE, redirects or caller-defined sources; shared guarded transport.
    _VALID_URL = "^" + re.escape(SAMPLE_URL) + "$"
    IE_NAME = "clipdock:owned-sample"

    def _real_extract(self, url):
        validate_source({"url": url, "platform": "sample"})
        with self._request_webpage(
            url, "owner-test", note="Verifying owned CC0 sample"
        ) as response:
            content = response.read(22250)
        if (
            len(content) != 22249
            or hashlib.sha256(content).hexdigest() != SAMPLE_SHA256
        ):
            raise MediaError(
                "SOURCE_CHANGED", "La muestra no coincide con el archivo autorizado."
            )
        # These are measured facts of the above hash-pinned audiovisual asset.
        return {
            "id": "owner-test",
            "title": "ClipDock · muestra propia CC0",
            "duration": 2,
            "license": "CC0 1.0",
            "formats": [
                {
                    "format_id": "owned-180",
                    "url": SAMPLE_URL,
                    "ext": "mp4",
                    "protocol": "https",
                    "height": 180,
                    "width": 320,
                    "vcodec": "h264",
                    "acodec": "aac",
                    "filesize": 22249,
                }
            ],
        }
