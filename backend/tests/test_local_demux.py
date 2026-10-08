import subprocess

import pytest


def test_downloaded_playlist_cannot_read_local_segments(tmp_path):
    from clipdock.media import MediaError
    from clipdock.worker import probe_media

    video = tmp_path / "private.ts"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=s=160x90:d=1",
            "-c:v",
            "libx264",
            "-y",
            str(video),
        ],
        check=True,
    )
    manifest = tmp_path / "untrusted.m3u8"
    manifest.write_text(
        "#EXTM3U\n#EXT-X-TARGETDURATION:1\n#EXTINF:1,\n"
        + str(video)
        + "\n#EXT-X-ENDLIST\n"
    )
    with pytest.raises(MediaError, match="verificar"):
        probe_media(manifest)
