import sys

import pytest

from clipdock.media import MediaError


def test_supervisor_kills_deadline_and_disk_overrun(tmp_path):
    from clipdock.api import Settings
    from clipdock.supervisor import execute

    cfg = Settings(root=tmp_path, timeout=0.15, disk_budget=1024, max_file=1024)
    with pytest.raises(MediaError, match="tiempo"):
        execute(
            [sys.executable, "-c", "import time;time.sleep(10)"],
            {},
            tmp_path,
            lambda n: None,
            cfg,
        )
    cfg.timeout = 3
    with pytest.raises(MediaError, match="espacio"):
        execute(
            [
                sys.executable,
                "-c",
                "from pathlib import Path;import time;Path('huge').write_bytes(b'x'*2048);time.sleep(1)",
            ],
            {},
            tmp_path,
            lambda n: None,
            cfg,
        )
