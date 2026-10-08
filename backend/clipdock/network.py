"""Worker-only socket boundary: check DNS results AND actual connect address.
Only yt-dlp's Python Urllib handler is enabled; no curl/native sockets.
External media downloaders and remote ffmpeg inputs are prohibited.
"""

import ipaddress
import socket
from urllib.parse import urlsplit

CDNS = {
    "i.ytimg.com",
    "img.youtube.com",
    "i9.ytimg.com",
    "pbs.twimg.com",
    "video.twimg.com",
}


def public_ip(value):
    try:
        ip = ipaddress.ip_address(value)
        if getattr(ip, "ipv4_mapped", None):
            ip = ip.ipv4_mapped
        return ip.is_global and not ip.is_multicast and not ip.is_reserved
    except ValueError:
        return False


def install_guard():
    if getattr(socket, "_clipdock_guard", False):
        return
    original_dns, original_connect, original_ex = (
        socket.getaddrinfo,
        socket.socket.connect,
        socket.socket.connect_ex,
    )

    def dns(host, port, *args, **kwargs):
        results = original_dns(host, port, *args, **kwargs)
        if not results or any(not public_ip(row[4][0]) for row in results):
            raise OSError("SSRF: destino DNS no público")
        return results

    def checked_address(address):
        # getaddrinfo must already have resolved to a numeric address. This
        # prevents a second unchecked DNS resolution inside libc connect.
        if not isinstance(address, tuple) or not public_ip(address[0]):
            raise OSError("SSRF: dirección no pública")

    def connect(self, address):
        checked_address(address)
        return original_connect(self, address)

    def connect_ex(self, address):
        checked_address(address)
        return original_ex(self, address)

    socket.getaddrinfo, socket.socket.connect, socket.socket.connect_ex = (
        dns,
        connect,
        connect_ex,
    )
    socket._clipdock_guard = True


def thumbnail(value):
    try:
        p = urlsplit(value)
        return (
            value
            if p.scheme == "https" and p.netloc in CDNS and not p.fragment
            else None
        )
    except (ValueError, TypeError):
        return None
