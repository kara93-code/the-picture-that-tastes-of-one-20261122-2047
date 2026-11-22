#!/usr/bin/env python3
"""Ripe Mango, Glistening — entry program.

Reads the bundled mango photograph (assets/entry.jpg), checks that it is a
whole JPEG inside the contest caps, and copies it to the output path as
entry.png. Standard library only; no network, no third-party packages.
"""

import os
import struct
import sys

MAX_BYTES = 1_048_576
MAX_SIDE = 1024
ASSET_NAME = "entry.jpg"
OUTPUT_NAME = "entry.png"


def asset_path():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "assets", ASSET_NAME)


def jpeg_dimensions(blob):
    """Return (width, height) from a JPEG byte string, or None if unparsable.

    Walks the marker segments until a Start Of Frame marker is found and
    reads its height/width fields (big-endian, 2 bytes each).
    """
    if len(blob) < 4 or blob[0:2] != b"\xff\xd8":
        return None
    pos = 2
    while pos + 9 < len(blob):
        if blob[pos] != 0xFF:
            return None
        marker = blob[pos + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        seg_len = struct.unpack(">H", blob[pos + 2:pos + 4])[0]
        if seg_len < 2 or pos + 2 + seg_len > len(blob):
            return None
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height, width = struct.unpack(">HH", blob[pos + 5:pos + 9])
            return (width, height)
        pos += 2 + seg_len
    return None


def main():
    src = asset_path()
    with open(src, "rb") as handle:
        blob = handle.read()

    if len(blob) > MAX_BYTES:
        print("entry.jpg too large: %d bytes (cap %d)" % (len(blob), MAX_BYTES),
              file=sys.stderr)
        return 1
    dims = jpeg_dimensions(blob)
    if dims is None:
        print("entry.jpg is not a readable JPEG", file=sys.stderr)
        return 1
    if not blob.rstrip(b"\x00").endswith(b"\xff\xd9"):
        print("entry.jpg is truncated (no JPEG end marker)", file=sys.stderr)
        return 1
    width, height = dims
    if width > MAX_SIDE or height > MAX_SIDE:
        print("entry.jpg too big: %dx%d (cap %dx%d)"
              % (width, height, MAX_SIDE, MAX_SIDE), file=sys.stderr)
        return 1

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, OUTPUT_NAME)
    with open(dest, "wb") as handle:
        handle.write(blob)
    os.chmod(dest, 0o644)
    print("wrote %s (%dx%d, %d bytes)" % (dest, width, height, len(blob)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
