def test_unknown_dimensions_duration_and_codecs_are_honest_original():
    from clipdock.media import describe

    info = {
        "title": "LinkedIn public clip",
        "formats": [
            {
                "format_id": "1",
                "url": "https://example.com/v.mp4",
                "protocol": "https",
                "ext": "mp4",
            }
        ],
    }
    result = describe(info, "linkedin")
    assert result["qualities"] == [0]
    assert result["duration"] is None
    assert result["has_audio"] is True


def test_probe_checks_actual_duration_and_audio(tmp_path):
    import subprocess

    from clipdock.worker import probe_media

    path = tmp_path / "silent.mp4"
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
            str(path),
        ],
        check=True,
    )
    result = probe_media(path)
    assert result["video"] is True and result["audio"] is False
    assert 0.9 <= result["duration"] <= 1.1
