import pytest

BASE = {
    "title": "Owner test asset",
    "duration": 3,
    "formats": [
        {
            "format_id": "v",
            "height": 720,
            "vcodec": "h264",
            "acodec": "aac",
            "url": "https://cdn.example/a",
            "protocol": "https",
        }
    ],
}


def test_metadata_rejects_non_public_or_unbounded_media():
    from clipdock.media import MediaError, describe

    assert describe(BASE, "youtube")["qualities"] == [720]
    assert describe(BASE, "youtube")["has_audio"] is True
    for changes in [
        {"duration": 1201},
        {"is_live": True},
        {"live_status": "was_live"},
        {"_type": "playlist"},
        {"has_drm": True},
        {"availability": "private"},
        {"age_limit": 18},
        {"formats": [dict(BASE["formats"][0], has_drm=True)]},
    ]:
        with pytest.raises(MediaError):
            describe(dict(BASE, **changes), "youtube")
    assert (
        describe(dict(BASE, thumbnail="https://evil/a"), "youtube")["thumbnail"] is None
    )
