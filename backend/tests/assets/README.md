# Generated, owner-authorized test asset

`owner-test.mp4` is a two-second solid blue 320×180 video with a synthesized 440 Hz tone. It contains no external footage or samples. This generated test asset is dedicated to the public domain under CC0-1.0 and may be used for local pipeline tests.

Regenerate from the backend directory:

```sh
ffmpeg -v error -f lavfi -i color=c=blue:s=320x180:d=2 \
  -f lavfi -i sine=frequency=440:duration=2 \
  -c:v libx264 -threads 1 -pix_fmt yuv420p -c:a aac -shortest \
  -y tests/assets/owner-test.mp4
```

The integration test generates equivalent owned media and injects a test-only extractor class. There is no production URL flag, environment switch, localhost exception, or generic-extractor backdoor.
