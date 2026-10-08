"""Policy regression: public extraction must never fake geographic origin."""


def test_public_extractor_never_generates_geographic_forwarding_ip(tmp_path):
    from clipdock.worker import PublicYDL, options

    with PublicYDL(options({"max_file": 1_000_000}, tmp_path)) as downloader:
        extractor = downloader.get_info_extractor("LinkedIn")
        extractor._initialize_geo_bypass({"countries": ["US"]})
        assert extractor._x_forwarded_for_ip is None
