"""Baseline JPEG writer in pure Python (standard library only): 4:2:0, optimised Huffman tables, quality or size target.

    data = encode_jpeg(width, height, rgb_bytes_or_float_list, quality=72)
    data = encode_jpeg(width, height, pixels, target_bytes=60000)     # lowers quality until the file fits (or says it cannot)

The expensive part (colour conversion + DCT) runs once; changing the quality only re-quantises and re-encodes, so a size target
costs about one extra pass. The pixels are a Canvas float list (0..1, RGB interleaved) or bytes (0..255).
"""
import struct

ZIGZAG = (0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6, 7, 14, 21, 28, 35, 42, 49, 56,
          57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51, 58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54, 47, 55, 62, 63)
BASE_LUMA = (16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55, 14, 13, 16, 24, 40, 57, 69, 56, 14, 17, 22, 29, 51, 87, 80, 62,
             18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92, 49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99)
BASE_CHROMA = (17, 18, 24, 47, 99, 99, 99, 99, 18, 21, 26, 66, 99, 99, 99, 99, 24, 26, 56, 99, 99, 99, 99, 99, 47, 66, 99, 99, 99, 99, 99, 99) + (99,) * 32
AAN = (1.0, 1.387039845, 1.306562965, 1.175875602, 1.0, 0.785694958, 0.541196100, 0.275899379)


class JpegError(ValueError):
    pass


def quant_table(base, quality):
    quality = max(1, min(100, int(quality)))
    s = 5000 // quality if quality < 50 else 200 - quality * 2
    return [max(1, min(255, (b * s + 50) // 100)) for b in base]


def _fdct_block(rows):
    """AAN forward DCT (float) of an 8x8 block given as 8 lists of 8 values (already level shifted). Returns 64 floats, row-major."""
    tmp = []
    for d in rows:                                           # rows
        d0, d1, d2, d3, d4, d5, d6, d7 = d
        t0, t7, t1, t6, t2, t5, t3, t4 = d0 + d7, d0 - d7, d1 + d6, d1 - d6, d2 + d5, d2 - d5, d3 + d4, d3 - d4
        t10, t13, t11, t12 = t0 + t3, t0 - t3, t1 + t2, t1 - t2
        z1 = (t12 + t13) * 0.707106781
        a, b, c = t4 + t5, t5 + t6, t6 + t7
        z5 = (a - c) * 0.382683433
        z2, z4, z3 = 0.541196100 * a + z5, 1.306562965 * c + z5, b * 0.707106781
        z11, z13 = t7 + z3, t7 - z3
        tmp.append((t10 + t11, z11 + z4, t13 + z1, z13 - z2, t10 - t11, z13 + z2, t13 - z1, z11 - z4))
    out = [0.0] * 64
    for col in range(8):                                     # columns
        d0, d1, d2, d3, d4, d5, d6, d7 = (tmp[0][col], tmp[1][col], tmp[2][col], tmp[3][col], tmp[4][col], tmp[5][col], tmp[6][col], tmp[7][col])
        t0, t7, t1, t6, t2, t5, t3, t4 = d0 + d7, d0 - d7, d1 + d6, d1 - d6, d2 + d5, d2 - d5, d3 + d4, d3 - d4
        t10, t13, t11, t12 = t0 + t3, t0 - t3, t1 + t2, t1 - t2
        z1 = (t12 + t13) * 0.707106781
        a, b, c = t4 + t5, t5 + t6, t6 + t7
        z5 = (a - c) * 0.382683433
        z2, z4, z3 = 0.541196100 * a + z5, 1.306562965 * c + z5, b * 0.707106781
        z11, z13 = t7 + z3, t7 - z3
        out[col] = t10 + t11
        out[8 + col] = z11 + z4
        out[16 + col] = t13 + z1
        out[24 + col] = z13 - z2
        out[32 + col] = t10 - t11
        out[40 + col] = z13 + z2
        out[48 + col] = t13 - z1
        out[56 + col] = z11 - z4
    return out


def _planes(width, height, px, is_float):
    """Level-shifted Y plane (full size) and Cb / Cr planes (half size), all padded to multiples of 16, as row lists."""
    W, H = (width + 15) // 16 * 16, (height + 15) // 16 * 16
    R, G, B = list(px[0::3]), list(px[1::3]), list(px[2::3])
    k = 255.0 if is_float else 1.0

    def pad(rows, w, h):
        rows = [r + [r[-1]] * (w - len(r)) for r in rows]
        return rows + [rows[-1]] * (h - len(rows))
    ys, cbs, crs = [], [], []
    rows_r = [R[y * width:(y + 1) * width] for y in range(height)]
    rows_g = [G[y * width:(y + 1) * width] for y in range(height)]
    rows_b = [B[y * width:(y + 1) * width] for y in range(height)]
    for r, g, b in zip(rows_r, rows_g, rows_b):
        ys.append([(0.299 * a + 0.587 * c + 0.114 * d) * k - 128.0 for a, c, d in zip(r, g, b)])
    rows_r, rows_g, rows_b = pad(rows_r, W, H), pad(rows_g, W, H), pad(rows_b, W, H)
    ys = pad(ys, W, H)
    for y in range(0, H, 2):
        r0, r1, g0, g1, b0, b1 = rows_r[y], rows_r[y + 1], rows_g[y], rows_g[y + 1], rows_b[y], rows_b[y + 1]
        ar = [(a + b + c + d) * 0.25 * k for a, b, c, d in zip(r0[0::2], r0[1::2], r1[0::2], r1[1::2])]
        ag = [(a + b + c + d) * 0.25 * k for a, b, c, d in zip(g0[0::2], g0[1::2], g1[0::2], g1[1::2])]
        ab = [(a + b + c + d) * 0.25 * k for a, b, c, d in zip(b0[0::2], b0[1::2], b1[0::2], b1[1::2])]
        cbs.append([-0.168736 * a - 0.331264 * c + 0.5 * d for a, c, d in zip(ar, ag, ab)])
        crs.append([0.5 * a - 0.418688 * c - 0.081312 * d for a, c, d in zip(ar, ag, ab)])
    return W, H, ys, cbs, crs


def _dct_plane(rows, w, h):
    blocks = []
    for by in range(0, h, 8):
        strip = rows[by:by + 8]
        for bx in range(0, w, 8):
            blocks.append(_fdct_block([r[bx:bx + 8] for r in strip]))
    return blocks


def _order_blocks(W, H, yb, cbb, crb):
    """Interleave blocks MCU by MCU (Y Y Y Y Cb Cr per 16x16 area): returns list of (component, block)."""
    wb = W // 8
    mw, mh = W // 16, H // 16
    out = []
    for my in range(mh):
        for mx in range(mw):
            for dy in (0, 1):
                for dx in (0, 1):
                    out.append((0, yb[(my * 2 + dy) * wb + mx * 2 + dx]))
            out.append((1, cbb[my * mw + mx]))
            out.append((2, crb[my * mw + mx]))
    return out


def _optimal_table(freq):
    """Annex K.2: length-limited (16) Huffman table from symbol frequencies. Returns (bits[1..16], huffval)."""
    freq = list(freq) + [0] * (257 - len(freq))
    freq[256] = 1
    codesize = [0] * 257
    others = [-1] * 257
    while True:
        c1, v = -1, 1 << 60
        for i in range(257):
            if freq[i] and freq[i] <= v:
                v, c1 = freq[i], i
        c2, v = -1, 1 << 60
        for i in range(257):
            if freq[i] and freq[i] <= v and i != c1:
                v, c2 = freq[i], i
        if c2 < 0:
            break
        freq[c1] += freq[c2]
        freq[c2] = 0
        codesize[c1] += 1
        while others[c1] >= 0:
            c1 = others[c1]
            codesize[c1] += 1
        others[c1] = c2
        codesize[c2] += 1
        while others[c2] >= 0:
            c2 = others[c2]
            codesize[c2] += 1
    bits = [0] * 40
    for i in range(257):
        if codesize[i]:
            bits[codesize[i]] += 1
    for i in range(39, 16, -1):
        while bits[i] > 0:
            j = i - 2
            while bits[j] == 0:
                j -= 1
            bits[i] -= 2
            bits[i - 1] += 1
            bits[j + 1] += 2
            bits[j] -= 1
    i = 16
    while bits[i] == 0:
        i -= 1
    bits[i] -= 1
    vals = [s for length in range(1, 33) for s in range(256) if codesize[s] == length]
    return bits[1:17], vals


def _codes(bits, vals):
    """Canonical codes: symbol -> (code, length)."""
    table, code, k = {}, 0, 0
    for length in range(1, 17):
        for _ in range(bits[length - 1]):
            table[vals[k]] = (code, length)
            code += 1
            k += 1
        code <<= 1
    return table


def _size(v):
    return abs(v).bit_length()


def _quantise(blocks_by_comp, qtabs):
    """-> list of 64-int zigzag blocks per entry of `blocks` ((component, dct)), using the AAN scaling folded into the tables."""
    inv = []
    for q in qtabs:
        inv.append([1.0 / (q[i] * AAN[i // 8] * AAN[i % 8] * 8.0) for i in range(64)])      # natural order
    out = []
    for comp, blk in blocks_by_comp:
        t = inv[0 if comp == 0 else 1]
        qd = [int(round(b * f)) for b, f in zip(blk, t)]
        out.append((comp, [qd[i] for i in ZIGZAG]))
    return out


def _symbols(qblocks):
    """Run-length symbols per block -> (stats, token list). A token is (table_id, symbol, extra_bits_value, extra_bits_len)."""
    freq = {0: [0] * 257, 1: [0] * 257, 2: [0] * 257, 3: [0] * 257}          # 0 DC luma, 1 DC chroma, 2 AC luma, 3 AC chroma
    tokens = []
    pred = [0, 0, 0]
    for comp, zz in qblocks:
        dcid = 0 if comp == 0 else 1
        acid = 2 if comp == 0 else 3
        diff = zz[0] - pred[comp]
        pred[comp] = zz[0]
        s = _size(diff)
        freq[dcid][s] += 1
        tokens.append((dcid, s, diff if diff >= 0 else diff + (1 << s) - 1, s))
        last = 63
        while last > 0 and zz[last] == 0:
            last -= 1
        run = 0
        fa = freq[acid]
        for i in range(1, last + 1):
            v = zz[i]
            if v == 0:
                run += 1
                continue
            while run > 15:
                fa[0xF0] += 1
                tokens.append((acid, 0xF0, 0, 0))
                run -= 16
            s = _size(v)
            sym = (run << 4) | s
            fa[sym] += 1
            tokens.append((acid, sym, v if v >= 0 else v + (1 << s) - 1, s))
            run = 0
        if last < 63:
            fa[0] += 1
            tokens.append((acid, 0, 0, 0))
    return freq, tokens


def _entropy(tokens, tables):
    acc, nb = 0, 0
    out = bytearray()
    codes = [_codes(*t) for t in tables]
    for tid, sym, extra, elen in tokens:
        code, ln = codes[tid][sym]
        acc = (acc << (ln + elen)) | (code << elen) | extra
        nb += ln + elen
        while nb >= 8:
            nb -= 8
            out.append((acc >> nb) & 0xFF)
        acc &= (1 << nb) - 1
    if nb:
        out.append(((acc << (8 - nb)) | ((1 << (8 - nb)) - 1)) & 0xFF)
    return bytes(out).replace(b"\xff", b"\xff\x00")


def _segment(marker, payload):
    return b"\xff" + bytes((marker,)) + struct.pack(">H", len(payload) + 2) + payload


class _Prepared:
    def __init__(self, width, height, pixels):
        if width < 1 or height < 1:
            raise JpegError("empty image")
        is_float = isinstance(pixels, list)
        if len(pixels) != width * height * 3:
            raise JpegError("pixel buffer size does not match dimensions")
        W, H, ys, cbs, crs = _planes(width, height, pixels, is_float)
        self.width, self.height, self.W, self.H = width, height, W, H
        self.blocks = _order_blocks(W, H, _dct_plane(ys, W, H), _dct_plane(cbs, W // 2, H // 2), _dct_plane(crs, W // 2, H // 2))

    def encode(self, quality):
        ql, qc = quant_table(BASE_LUMA, quality), quant_table(BASE_CHROMA, quality)
        qb = _quantise(self.blocks, (ql, qc))
        freq, tokens = _symbols(qb)
        tables = [_optimal_table(freq[i]) for i in range(4)]
        scan = _entropy(tokens, tables)
        out = bytearray(b"\xff\xd8")
        out += _segment(0xE0, b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00")
        out += _segment(0xDB, b"\x00" + bytes(ql[i] for i in ZIGZAG))
        out += _segment(0xDB, b"\x01" + bytes(qc[i] for i in ZIGZAG))
        out += _segment(0xC0, struct.pack(">BHHB", 8, self.height, self.width, 3) + b"\x01\x22\x00\x02\x11\x01\x03\x11\x01")
        for tc_th, (bits, vals) in zip((0x00, 0x01, 0x10, 0x11), tables):       # DC luma, DC chroma, AC luma, AC chroma
            out += _segment(0xC4, bytes((tc_th,)) + bytes(bits) + bytes(vals))
        out += _segment(0xDA, b"\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00")
        out += scan
        out += b"\xff\xd9"
        return bytes(out)


def encode_jpeg(width, height, pixels, quality=72, target_bytes=None, min_quality=30):
    """JPEG bytes. With target_bytes the quality is lowered (in steps of 6) until the file fits; raises JpegError if even
    min_quality is too big, so a caller can fall back to simplifying the picture."""
    prep = _Prepared(width, height, pixels)
    data = prep.encode(quality)
    if target_bytes is None:
        return data
    q = quality
    while len(data) > target_bytes and q > min_quality:
        q = max(min_quality, q - 6)
        data = prep.encode(q)
    if len(data) > target_bytes:
        raise JpegError("cannot reach %d bytes (got %d at quality %d)" % (target_bytes, len(data), q))
    return data
