import socket

import pytest


def test_every_socket_connection_rejects_non_global_destinations(monkeypatch):
    # Guard is worker-only in production; restore sockets in the pytest host.
    monkeypatch.setattr(socket, "getaddrinfo", socket.getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", socket.socket.connect)
    monkeypatch.setattr(socket.socket, "connect_ex", socket.socket.connect_ex)
    monkeypatch.setattr(socket, "_clipdock_guard", False, raising=False)
    from clipdock.network import install_guard, public_ip

    for ip in [
        "127.0.0.1",
        "10.0.0.1",
        "169.254.169.254",
        "::1",
        "::ffff:127.0.0.1",
        "192.0.2.1",
        "224.0.0.1",
    ]:
        assert not public_ip(ip)
    assert public_ip("8.8.8.8")
    install_guard()
    with socket.socket() as s:
        with pytest.raises(OSError, match="SSRF"):
            s.connect(("127.0.0.1", 80))
    with pytest.raises(OSError, match="SSRF"):
        socket.getaddrinfo("localhost", 80)


def test_thumbnail_is_explicit_https_cdn_only():
    from clipdock.network import thumbnail

    assert thumbnail("https://i.ytimg.com/vi/123/a.jpg")
    for u in [
        "http://i.ytimg.com/a",
        "https://i.ytimg.com.evil/a",
        "https://127.0.0.1/a",
        "https://u@i.ytimg.com/a",
    ]:
        assert thumbnail(u) is None
