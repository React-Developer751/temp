"""Pure-Python image readers (PNG, BMP, baseline JPEG) used to build training thumbnails.

Only `struct`, `zlib` and `re` from the standard library are used.

* PNG: all colour types, bit depths 1-16, Adam7 interlacing. Alpha is composited on white.
* BMP: 8-bit palette, 24-bit and 32-bit, bottom-up or top-down.
* JPEG: baseline / extended-sequential Huffman files (what cameras and the web use).
  Only the DC coefficients are decoded, which gives each 8x8 block's exact mean colour:
  the image comes back at 1/8 size, which is all a training thumbnail needs, and is much
  faster than a full decode. Progressive and arithmetic-coded JPEGs are rejected with a
  clear message (re-save them as PNG).
"""
import re
import struct
import zlib

MAX_PIXELS = 40_000_000             # default decode cap (a 24 MP camera photo fits); the HTTP server passes a lower one
MAX_FILE_BYTES = 300 * 1024 * 1024


class ImageError(ValueError):
    pass


def _check_pixels(w, h, max_pixels):
    """Refuse huge images before allocating anything: decoding costs several bytes of RAM per pixel."""
    if w * h > max_pixels:
        raise ImageError("image too large (%dx%d = %.1f MP, limit %.0f MP)" % (w, h, w * h / 1e6, max_pixels / 1e6))


# ------------------------------------------------------------------ PNG
_PNG_SIG = b"\x89PNG\r\n\x1a\n"
_ADAM7 = ((0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4), (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2))
_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
_DEPTHS = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}


def _unfilter(ftype, row, prev, bpp):
    if ftype == 0:
        return row
    out = bytearray(row)
    n = len(out)
    if ftype == 1:
        for i in range(bpp, n):
            out[i] = (out[i] + out[i - bpp]) & 255
    elif ftype == 2:
        for i in range(n):
            out[i] = (out[i] + prev[i]) & 255
    elif ftype == 3:
        for i in range(n):
            left = out[i - bpp] if i >= bpp else 0
            out[i] = (out[i] + ((left + prev[i]) >> 1)) & 255
    elif ftype == 4:
        for i in range(n):
            a = out[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            p = a + b - c
            pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            out[i] = (out[i] + pred) & 255
    else:
        raise ImageError("corrupt PNG (bad filter type %d)" % ftype)
    return out


def _samples(row, depth, count):
    """Row bytes -> list of `count` samples (8-bit scale for 16-bit, raw for <8-bit)."""
    if depth == 8:
        return row
    if depth == 16:
        return row[0::2]
    per = 8 // depth
    mask = (1 << depth) - 1
    out = []
    for byte in row:
        for k in range(per):
            out.append((byte >> (8 - depth * (k + 1))) & mask)
    return out[:count]


def _over_white(c, a):
    return (c * a + 255 * (255 - a)) // 255


def decode_png(data, max_pixels=MAX_PIXELS):
    if data[:8] != _PNG_SIG:
        raise ImageError("not a PNG file")
    pos, idat, ihdr, plte, trns = 8, [], None, None, None
    while pos + 8 <= len(data):
        length, tag = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if tag == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif tag == b"PLTE":
            plte = body
        elif tag == b"tRNS":
            trns = body
        elif tag == b"IDAT":
            idat.append(body)
        elif tag == b"IEND":
            break
    if ihdr is None or not idat:
        raise ImageError("corrupt PNG (missing IHDR/IDAT)")
    w, h, depth, ctype, comp, filt, interlace = ihdr
    if ctype not in _CHANNELS or depth not in _DEPTHS[ctype] or comp != 0 or filt != 0 or interlace > 1:
        raise ImageError("unsupported PNG variant")
    if w < 1 or h < 1:
        raise ImageError("PNG dimensions out of range")
    _check_pixels(w, h, max_pixels)
    channels = _CHANNELS[ctype]
    bits_pp = channels * depth
    bpp = max(1, bits_pp // 8)
    limit = 2 * h * ((w * bits_pp + 7) // 8 + 1) + 4096
    dec = zlib.decompressobj()
    try:
        raw = dec.decompress(b"".join(idat), limit)
    except zlib.error as exc:
        raise ImageError("corrupt PNG data: %s" % exc)
    if dec.unconsumed_tail:
        raise ImageError("PNG decompresses to more data than its header allows")

    palette = None
    if ctype == 3:
        if plte is None:
            raise ImageError("palette PNG without PLTE")
        alpha = trns or b""
        palette = []
        for i in range(len(plte) // 3):
            r, g, b = plte[3 * i:3 * i + 3]
            a = alpha[i] if i < len(alpha) else 255
            palette.append(bytes((_over_white(r, a), _over_white(g, a), _over_white(b, a))))
    gray_scale = 255 // ((1 << depth) - 1) if depth < 8 else 1

    passes = _ADAM7 if interlace else ((0, 0, 1, 1),)
    need = 0
    for xs, ys, dx, dy in passes:
        pw, ph = (w - xs + dx - 1) // dx, (h - ys + dy - 1) // dy
        if pw > 0 and ph > 0:
            need += ph * (1 + (pw * bits_pp + 7) // 8)
    if len(raw) < need:                           # check before allocating the output buffer
        raise ImageError("truncated PNG data")
    out = bytearray(w * h * 3)
    off = 0
    for xs, ys, dx, dy in passes:
        pw, ph = (w - xs + dx - 1) // dx, (h - ys + dy - 1) // dy
        if pw <= 0 or ph <= 0:
            continue
        rbytes = (pw * bits_pp + 7) // 8
        prev = bytearray(rbytes)
        for j in range(ph):
            if off + 1 + rbytes > len(raw):
                raise ImageError("truncated PNG data")
            row = _unfilter(raw[off], raw[off + 1:off + 1 + rbytes], prev, bpp)
            prev = row
            off += 1 + rbytes
            s = _samples(row, depth, pw * channels)
            if ctype == 2:
                rgb = s
            elif ctype == 6:
                rgb = bytearray(pw * 3)
                a = s[3::4]
                for c in range(3):
                    rgb[c::3] = bytes(_over_white(v, al) for v, al in zip(s[c::4], a))
            elif ctype == 0:
                g = bytes(v * gray_scale for v in s) if depth < 8 else s
                rgb = bytearray(pw * 3)
                rgb[0::3] = rgb[1::3] = rgb[2::3] = g
            elif ctype == 4:
                g = s[0::2]
                al = s[1::2]
                g = bytes(_over_white(v, a) for v, a in zip(g, al))
                rgb = bytearray(pw * 3)
                rgb[0::3] = rgb[1::3] = rgb[2::3] = g
            else:
                npal = len(palette)
                rgb = b"".join(palette[i] if i < npal else b"\x00\x00\x00" for i in s)
            y = ys + j * dy
            base = (y * w + xs) * 3
            end = (y + 1) * w * 3
            for c in range(3):
                out[base + c:end:3 * dx] = rgb[c::3]
    return w, h, out                              # bytearray: no extra copy of a big image


# ------------------------------------------------------------------ BMP
def decode_bmp(data, max_pixels=MAX_PIXELS):
    if data[:2] != b"BM" or len(data) < 26:
        raise ImageError("not a BMP file")
    (offset,) = struct.unpack("<I", data[10:14])
    (hsize,) = struct.unpack("<I", data[14:18])
    if hsize == 12:
        w, h, _planes, bpp = struct.unpack("<HHHH", data[18:26])
        comp, entry, ncolors = 0, 3, 256
    else:
        w, h, _planes, bpp, comp, _size, _x, _y, ncolors, _imp = struct.unpack("<iiHHIIiiII", data[18:54])
        entry = 4
    top_down = h < 0
    h = abs(h)
    if w < 1 or h < 1:
        raise ImageError("BMP dimensions out of range")
    _check_pixels(w, h, max_pixels)
    if comp not in (0, 3) or bpp not in (8, 24, 32):
        raise ImageError("unsupported BMP (need uncompressed 8/24/32-bit)")
    row_size = ((w * bpp + 31) // 32) * 4
    if offset + row_size * h > len(data):
        raise ImageError("truncated BMP data")
    palette = None
    if bpp == 8:
        start = 14 + hsize
        n = ncolors or 256
        palette = [bytes((data[start + entry * i + 2], data[start + entry * i + 1], data[start + entry * i]))
                   for i in range(n) if start + entry * i + 2 < len(data)]
    out = bytearray(w * h * 3)
    for j in range(h):
        y = j if top_down else h - 1 - j
        row = data[offset + j * row_size: offset + j * row_size + row_size]
        if bpp == 24:
            px = row[:w * 3]
            rgb = bytearray(px)
            rgb[0::3], rgb[2::3] = px[2::3], px[0::3]
        elif bpp == 32:
            px = row[:w * 4]
            rgb = bytearray(w * 3)
            rgb[0::3], rgb[1::3], rgb[2::3] = px[2::4], px[1::4], px[0::4]
        else:
            rgb = b"".join(palette[i] if i < len(palette) else b"\x00\x00\x00" for i in row[:w])
        out[y * w * 3:(y + 1) * w * 3] = rgb
    return w, h, out                              # bytearray: no extra copy of a big image


# ------------------------------------------------------------------ JPEG (DC only)
class _Huff:
    def __init__(self, counts, symbols):
        table = [0] * 65536
        code = k = 0
        for length in range(1, 17):
            for _ in range(counts[length - 1]):
                if k >= len(symbols):
                    raise ImageError("corrupt JPEG Huffman table")
                start, end = code << (16 - length), (code + 1) << (16 - length)
                if end > 65536:
                    raise ImageError("corrupt JPEG Huffman table")
                table[start:end] = [(length << 8) | symbols[k]] * (end - start)
                k += 1
                code += 1
            code <<= 1
        self.table = table


_END_OF_SCAN = re.compile(rb"\xff[\x01-\xcf\xd8-\xfe]", re.S)
_RESTART = re.compile(rb"\xff[\xd0-\xd7]")


def _decode_scan(segments, restart, total, mcus_x, blocks, planes):
    """Entropy-decode one scan, storing only the DC value of every block."""
    m = 0
    for seg in segments:
        preds = [0] * len(planes)
        buf = nbits = pos = 0
        n = len(seg)
        for _ in range(restart or total):
            if m >= total:
                break
            mx, my = m % mcus_x, m // mcus_x
            for ci, ox, oy, dct, act, pw, hs, vs in blocks:
                while nbits < 16:
                    buf = (buf << 8) | (seg[pos] if pos < n else 0)
                    pos += 1
                    nbits += 8
                v = dct[(buf >> (nbits - 16)) & 0xFFFF]
                if not v:
                    raise ImageError("corrupt JPEG data")
                nbits -= v >> 8
                s = v & 255
                diff = 0
                if s:
                    if s > 11:
                        raise ImageError("corrupt JPEG data")
                    while nbits < s:
                        buf = (buf << 8) | (seg[pos] if pos < n else 0)
                        pos += 1
                        nbits += 8
                    bits = (buf >> (nbits - s)) & ((1 << s) - 1)
                    nbits -= s
                    diff = bits if bits >= (1 << (s - 1)) else bits - (1 << s) + 1
                buf &= (1 << nbits) - 1
                preds[ci] += diff
                planes[ci][(my * vs + oy) * pw + mx * hs + ox] = preds[ci]
                k = 1
                while k < 64:
                    while nbits < 16:
                        buf = (buf << 8) | (seg[pos] if pos < n else 0)
                        pos += 1
                        nbits += 8
                    v = act[(buf >> (nbits - 16)) & 0xFFFF]
                    if not v:
                        raise ImageError("corrupt JPEG data")
                    nbits -= v >> 8
                    r, s = (v & 255) >> 4, v & 15
                    if s == 0:
                        if r == 15:
                            k += 16
                            buf &= (1 << nbits) - 1
                            continue
                        buf &= (1 << nbits) - 1
                        break
                    k += r + 1
                    while nbits < s:
                        buf = (buf << 8) | (seg[pos] if pos < n else 0)
                        pos += 1
                        nbits += 8
                    nbits -= s
                    buf &= (1 << nbits) - 1
            m += 1
        if pos * 8 - nbits > n * 8:                      # decoder had to invent bits: file is cut short
            raise ImageError("truncated JPEG data")
    if m < total:
        raise ImageError("truncated JPEG data")


def decode_jpeg_dc(data, max_pixels=MAX_PIXELS):
    """Return (w, h, rgb) at 1/8 scale: one pixel per 8x8 block (exact block mean)."""
    if data[:2] != b"\xff\xd8":
        raise ImageError("not a JPEG file")
    pos, n = 2, len(data)
    qt, dc_tabs, ac_tabs = {}, {}, {}
    frame, restart, adobe = None, 0, None
    planes = None
    scans = 0
    while pos < n:
        if data[pos] != 0xFF:
            pos += 1
            continue
        while pos < n and data[pos] == 0xFF:
            pos += 1
        if pos >= n:
            break
        marker = data[pos]
        pos += 1
        if marker == 0xD9:
            break
        if marker == 0x01 or 0xD0 <= marker <= 0xD8 or marker == 0:
            continue
        if pos + 2 > n:
            raise ImageError("truncated JPEG")
        (length,) = struct.unpack(">H", data[pos:pos + 2])
        seg = data[pos + 2:pos + length]
        pos += length
        if marker == 0xDB:
            i = 0
            while i < len(seg):
                pq, tq = seg[i] >> 4, seg[i] & 15
                size = 128 if pq else 64
                first = struct.unpack(">H", seg[i + 1:i + 3])[0] if pq else seg[i + 1]
                qt[tq] = first
                i += 1 + size
        elif marker in (0xC0, 0xC1):
            prec, h, w, nc = struct.unpack(">BHHB", seg[:6])
            if prec != 8:
                raise ImageError("only 8-bit JPEG is supported")
            if w < 1 or h < 1 or nc not in (1, 3):
                raise ImageError("unsupported JPEG (size or component count)")
            _check_pixels(w, h, max_pixels)
            comps = [(seg[6 + 3 * i], seg[7 + 3 * i] >> 4, seg[7 + 3 * i] & 15, seg[8 + 3 * i]) for i in range(nc)]
            hmax, vmax = max(c[1] for c in comps), max(c[2] for c in comps)
            if any(c[1] < 1 or c[2] < 1 for c in comps):
                raise ImageError("corrupt JPEG frame")
            mcus_x = -(-w // (8 * hmax))
            mcus_y = -(-h // (8 * vmax))
            frame = dict(w=w, h=h, comps=comps, hmax=hmax, vmax=vmax, mx=mcus_x, my=mcus_y)
            planes = [[0] * (mcus_x * c[1] * mcus_y * c[2]) for c in comps]
        elif marker in (0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            raise ImageError("progressive/arithmetic/lossless JPEG is not supported; re-save it as PNG or baseline JPEG")
        elif marker == 0xC4:
            i = 0
            while i + 17 <= len(seg):
                tc, th = seg[i] >> 4, seg[i] & 15
                counts = list(seg[i + 1:i + 17])
                total = sum(counts)
                (dc_tabs if tc == 0 else ac_tabs)[th] = _Huff(counts, seg[i + 17:i + 17 + total])
                i += 17 + total
        elif marker == 0xDD:
            (restart,) = struct.unpack(">H", seg[:2])
        elif marker == 0xEE and seg[:5] == b"Adobe" and len(seg) >= 12:
            adobe = seg[11]
        elif marker == 0xDA:
            if frame is None:
                raise ImageError("corrupt JPEG (scan before frame)")
            ns = seg[0]
            sel = []
            for i in range(ns):
                cid, tabs = seg[1 + 2 * i], seg[2 + 2 * i]
                idx = [c[0] for c in frame["comps"]].index(cid) if cid in [c[0] for c in frame["comps"]] else -1
                if idx < 0:
                    raise ImageError("corrupt JPEG scan header")
                sel.append((idx, tabs >> 4, tabs & 15))
            m = _END_OF_SCAN.search(data, pos)
            end = m.start() if m else n
            segments = [s.replace(b"\xff\x00", b"\xff") for s in _RESTART.split(data[pos:end])]
            pos = end
            comps = frame["comps"]
            interleaved = ns > 1
            blocks = []
            for idx, dcid, acid in sel:
                _, hs, vs, _tq = comps[idx]
                if dcid not in dc_tabs or acid not in ac_tabs:
                    raise ImageError("corrupt JPEG (missing Huffman table)")
                pw = frame["mx"] * hs
                for oy in range(vs if interleaved else 1):
                    for ox in range(hs if interleaved else 1):
                        blocks.append((idx, ox, oy, dc_tabs[dcid].table, ac_tabs[acid].table,
                                       pw, hs if interleaved else 1, vs if interleaved else 1))
            if interleaved:
                total, mcus_x = frame["mx"] * frame["my"], frame["mx"]
            else:
                _, hs, vs, _tq = comps[sel[0][0]]
                cw = -(-frame["w"] * hs // frame["hmax"])
                chh = -(-frame["h"] * vs // frame["vmax"])
                mcus_x = -(-cw // 8)
                total = mcus_x * -(-chh // 8)
            _decode_scan(segments, restart, total, mcus_x, blocks, planes)
            scans += 1
    if frame is None or not scans:
        raise ImageError("corrupt JPEG (no image data)")

    w8, h8 = -(-frame["w"] // 8), -(-frame["h"] // 8)
    comps = frame["comps"]
    cols = []
    for (idx, (_cid, hs, vs, tq)), plane in zip(enumerate(comps), planes):
        q0 = qt.get(tq, 16)
        pw = frame["mx"] * hs
        cols.append([[plane[((y * vs) // frame["vmax"]) * pw + (x * hs) // frame["hmax"]] * q0 / 8.0 + 128.0
                      for x in range(w8)] for y in range(h8)])
    out = bytearray(w8 * h8 * 3)
    i = 0
    rgb_direct = len(comps) == 3 and adobe == 0
    for y in range(h8):
        for x in range(w8):
            if len(comps) == 1:
                r = g = b = cols[0][y][x]
            else:
                yy, cb, cr = cols[0][y][x], cols[1][y][x] - 128.0, cols[2][y][x] - 128.0
                if rgb_direct:
                    r, g, b = yy, cols[1][y][x], cols[2][y][x]
                else:
                    r, g, b = yy + 1.402 * cr, yy - 0.344136 * cb - 0.714136 * cr, yy + 1.772 * cb
            out[i] = 0 if r < 0 else 255 if r > 255 else int(r + 0.5)
            out[i + 1] = 0 if g < 0 else 255 if g > 255 else int(g + 0.5)
            out[i + 2] = 0 if b < 0 else 255 if b > 255 else int(b + 0.5)
            i += 3
    return w8, h8, bytes(out)


# ------------------------------------------------------------------ public API
def decode_image(data, max_pixels=MAX_PIXELS):
    """Decode PNG / BMP / baseline JPEG bytes. Malformed input (or more than `max_pixels`) raises ImageError."""
    try:
        if data[:8] == _PNG_SIG:
            return decode_png(data, max_pixels)
        if data[:2] == b"BM":
            return decode_bmp(data, max_pixels)
        if data[:2] == b"\xff\xd8":
            return decode_jpeg_dc(data, max_pixels)
    except ImageError:
        raise
    except (struct.error, IndexError, KeyError, ValueError, TypeError, zlib.error) as exc:
        raise ImageError("corrupt or truncated image (%s)" % exc)
    raise ImageError("unrecognised image format (supported: PNG, BMP, baseline JPEG)")


def to_thumbnail(w, h, rgb, n):
    """Centre-crop to a square, then area-average (sampled) down to n x n.

    Returns a flat list of n*n*3 floats in [0, 1], row-major RGB.
    """
    side = min(w, h)
    x0, y0 = (w - side) // 2, (h - side) // 2
    out = []
    for ty in range(n):
        ya = y0 + ty * side // n
        yb = max(ya + 1, y0 + (ty + 1) * side // n)
        sy = max(1, (yb - ya) // 8)
        for tx in range(n):
            xa = x0 + tx * side // n
            xb = max(xa + 1, x0 + (tx + 1) * side // n)
            sx = max(1, (xb - xa) // 8)
            r = g = b = cnt = 0
            for y in range(ya, yb, sy):
                base = y * w * 3
                for x in range(xa, xb, sx):
                    i = base + x * 3
                    r += rgb[i]
                    g += rgb[i + 1]
                    b += rgb[i + 2]
                    cnt += 1
            k = 255.0 * cnt
            out += (r / k, g / k, b / k)
    return out


def load_thumbnail(path, n, max_pixels=MAX_PIXELS):
    with open(path, "rb") as fh:
        data = fh.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ImageError("file too large")
    w, h, rgb = decode_image(data, max_pixels)
    return to_thumbnail(w, h, rgb, n)


def load_thumbnails(path, sizes, max_pixels=MAX_PIXELS):
    """Decode once, return one thumbnail per requested size (e.g. the model grid and a preview)."""
    with open(path, "rb") as fh:
        data = fh.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ImageError("file too large")
    w, h, rgb = decode_image(data, max_pixels)
    return [to_thumbnail(w, h, rgb, n) for n in sizes]
