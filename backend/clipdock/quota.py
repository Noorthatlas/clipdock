"""Single-process aggregate reservations prevent concurrent disk overcommit."""

import threading
from pathlib import Path

from clipdock.media import MediaError

_LOCK = threading.Lock()
_RESERVED = {}


def reserve(root, folder, amount, budget):
    root, folder = Path(root).resolve(), Path(folder).resolve()
    with _LOCK:
        relevant = {p: n for p, n in _RESERVED.items() if p.is_relative_to(root)}
        used = sum(
            p.stat().st_size
            for p in root.rglob("*")
            if p.is_file() and not any(p.is_relative_to(r) for r in relevant)
        )
        if used + sum(relevant.values()) + amount > budget:
            raise MediaError(
                "DISK_LIMIT", "No hay espacio suficiente para procesar el medio."
            )
        _RESERVED[folder] = amount


def release(root, folder):
    with _LOCK:
        _RESERVED.pop(Path(folder).resolve(), None)
