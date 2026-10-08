import pytest


def test_native_hls_cannot_fall_back_to_network_ffmpeg(monkeypatch):
    from yt_dlp.downloader.external import ExternalFD, FFmpegFD

    from clipdock.media import MediaError
    from clipdock.worker import disable_external_downloaders

    monkeypatch.setattr(ExternalFD, "real_download", ExternalFD.real_download)
    disable_external_downloaders()
    with pytest.raises(MediaError, match="externos"):
        FFmpegFD.real_download(None, "out.mp4", {"url": "http://127.0.0.1/a"})
