import pytest

from clipdock.media import MediaError


def test_aggregate_reservations_prevent_concurrent_overcommit(tmp_path):
    from clipdock.quota import release, reserve

    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    reserve(tmp_path, first, 600, 1000)
    with pytest.raises(MediaError, match="espacio"):
        reserve(tmp_path, second, 600, 1000)
    (first / "output").write_bytes(b"x" * 550)
    release(tmp_path, first)
    with pytest.raises(MediaError, match="espacio"):
        reserve(tmp_path, second, 600, 1000)
    (first / "output").unlink()
    reserve(tmp_path, second, 600, 1000)
    release(tmp_path, second)
