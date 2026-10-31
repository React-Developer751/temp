"""Module 3 - Binary pixel-buffer writers (PNG and BMP) built from raw bytes.

Only `struct` and `zlib` (Python standard library) are used. zlib is just the
DEFLATE compressor that the PNG format itself mandates.
"""
import os
import struct
import zlib


def _chunk(tag, data):
    body = tag + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def encode_png(width, height, rgb):
    """rgb: bytes, row-major, 3 bytes per pixel."""
    if len(rgb) != width * height * 3:
        raise ValueError("pixel buffer size does not match dimensions")
    stride = width * 3
    raw = bytearray()
    for y in range(height):
        raw.append(0)                                   # filter type 0 (None)
        raw += rgb[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)   # 8-bit RGB
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _chunk(b"IEND", b""))


def encode_bmp(width, height, rgb):
    """24-bit BMP: BGR byte order, bottom-up rows, each row padded to 4 bytes."""
    if len(rgb) != width * height * 3:
        raise ValueError("pixel buffer size does not match dimensions")
    pad = (4 - (width * 3) % 4) % 4
    rows = bytearray()
    for y in range(height - 1, -1, -1):
        row = rgb[y * width * 3:(y + 1) * width * 3]
        bgr = bytearray(row)
        bgr[0::3], bgr[2::3] = row[2::3], row[0::3]
        rows += bgr + b"\x00" * pad
    file_header = b"BM" + struct.pack("<IHHI", 54 + len(rows), 0, 0, 54)
    dib = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, len(rows), 2835, 2835, 0, 0)
    return file_header + dib + bytes(rows)


def save(path, width, height, rgb, fmt=None):
    fmt = (fmt or path.rsplit(".", 1)[-1]).lower()
    if fmt == "png":
        data = encode_png(width, height, rgb)
    elif fmt == "bmp":
        data = encode_bmp(width, height, rgb)
    else:
        raise ValueError("unsupported format %r (use png or bmp)" % fmt)
    tmp = "%s.tmp%d" % (path, os.getpid())            # write-then-rename: never a half-written file
    try:
        with open(tmp, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return len(data)
