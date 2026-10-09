# Generated, owner-authorized test asset

`owner-test.mp4` is a two-second solid blue 320×180 video with a synthesized 440 Hz tone. It contains no external footage or samples. This generated test asset is dedicated to the public domain under CC0-1.0: copying, downloading and conversion are permitted, including the public processing diagnostic.

Regenerate from the backend directory:

```sh
ffmpeg -v error -f lavfi -i color=c=blue:s=320x180:d=2 \
  -f lavfi -i sine=frequency=440:duration=2 \
  -c:v libx264 -threads 1 -pix_fmt yuv420p -c:a aac -shortest \
  -y tests/assets/owner-test.mp4
```

The local integration test generates equivalent owned media and injects a test-only extractor class. Production additionally exposes `/api/sample/inspect`, a clearly labeled first-party diagnostic which accepts only `authorized`, never a source URL. It uses this exact file pinned to commit `90089cc28480b1195c955e5333d06cb886f9a2f9` and verifies SHA-256 `ead9b689f8297aa5e2e9e0785e74592068e9b4aeb7406687a3010367bb028126` before and after download. There is no localhost exception or generic-extractor backdoor. A successful diagnostic does NOT verify extraction from any external social platform.
