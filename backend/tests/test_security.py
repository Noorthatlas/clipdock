import pytest


def test_url_normalization():
    from clipdock.security import Unsafe, normalize

    assert normalize("https://youtu.be/BaW_jenozKc") == (
        "https://www.youtube.com/watch?v=BaW_jenozKc",
        "youtube",
    )
    for url in [
        "http://youtube.com/watch?v=BaW_jenozKc",
        "https://youtube.com.evil/watch?v=BaW_jenozKc",
        "https://u:p@youtube.com/watch?v=BaW_jenozKc",
        "https://youtube.com:443/watch?v=BaW_jenozKc",
        "https://127.0.0.1/x",
        "https://youtube.com/playlist?list=123",
        "https://youtube.com/watch?v=bad",
        "https://youtube.com/watch?v=BaW_jenozKc&list=x",
    ]:
        with pytest.raises(Unsafe):
            normalize(url)
    cases = [
        ("https://www.tiktok.com/@demo/video/1234567890123456789", "tiktok"),
        ("https://instagram.com/reel/ABC_123/", "instagram"),
        ("https://www.facebook.com/watch/?v=123456789", "facebook"),
        (
            "https://www.linkedin.com/posts/demo_activity-1234567890123456789-abcd",
            "linkedin",
        ),
        ("https://x.com/demo/status/1234567890123456789", "x"),
    ]
    for url, platform in cases:
        assert normalize(url)[1] == platform
