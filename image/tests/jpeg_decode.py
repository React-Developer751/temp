"""A small, slow, independent baseline JPEG decoder used only to check pixelmath.jpegwrite (does not share code with it)."""
import math
import struct

ZZ = [0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6, 7, 14, 21, 28, 35, 42, 49, 56,
      57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51, 58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54, 47, 55, 62, 63]
COS = [[math.cos((2 * x + 1) * u * math.pi / 16) * (math.sqrt(0.125) if u == 0 else 0.5) for u in range(8)] for x in range(8)]


class Bits:
    def __init__(self, data):
        self.data, self.pos, self.acc, self.n = data, 0, 0, 0

    def bit(self):
        if self.n == 0:
            b = self.data[self.pos]
            self.pos += 1
            if b == 0xFF:
                nxt = self.data[self.pos]
                if nxt != 0:
                    raise ValueError("marker inside scan data")
                self.pos += 1
            self.acc, self.n = b, 8
        self.n -= 1
        return (self.acc >> self.n) & 1

    def bits(self, k):
        v = 0
        for _ in range(k):
            v = (v << 1) | self.bit()
        return v


def decode_huff(bits, table):
    code = 0
    for length in range(1, 17):
        code = (code << 1) | bits.bit()
        sym = table.get((length, code))
        if sym is not None:
            return sym
    raise ValueError("bad huffman code")


def extend(v, t):
    return v if v >= (1 << (t - 1)) else v - (1 << t) + 1


def idct(block):
    tmp = [[sum(block[v * 8 + u] * COS[x][u] for u in range(8)) for x in range(8)] for v in range(8)]       # per row v, over x
    return [[sum(tmp[v][x] * COS[y][v] for v in range(8)) + 128.0 for x in range(8)] for y in range(8)]


def decode_jpeg(data):
    """-> (width, height, rgb bytes)."""
    assert data[:2] == b"\xff\xd8"
    pos, qt, huff, comps, w, h = 2, {}, {}, [], 0, 0
    while True:
        assert data[pos] == 0xFF, "expected marker"
        marker = data[pos + 1]
        if marker == 0xD9:
            raise ValueError("EOI before scan")
        ln = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        seg = data[pos + 4:pos + 2 + ln]
        if marker == 0xDB:
            i = 0
            while i < len(seg):
                pq, tq = seg[i] >> 4, seg[i] & 15
                assert pq == 0
                qt[tq] = list(seg[i + 1:i + 65])
                i += 65
        elif marker == 0xC0:
            _, h, w, n = struct.unpack(">BHHB", seg[:6])
            for k in range(n):
                cid, hv, tq = seg[6 + 3 * k], seg[7 + 3 * k], seg[8 + 3 * k]
                comps.append({"id": cid, "h": hv >> 4, "v": hv & 15, "tq": tq, "pred": 0})
        elif marker in (0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB):
            raise ValueError("not a baseline JPEG")
        elif marker == 0xC4:
            i = 0
            while i < len(seg):
                tc_th = seg[i]
                counts = list(seg[i + 1:i + 17])
                syms = list(seg[i + 17:i + 17 + sum(counts)])
                table, code, k = {}, 0, 0
                for length in range(1, 17):
                    for _ in range(counts[length - 1]):
                        table[(length, code)] = syms[k]
                        code += 1
                        k += 1
                    code <<= 1
                huff[(tc_th >> 4, tc_th & 15)] = table
                i += 17 + sum(counts)
        elif marker == 0xDA:
            n = seg[0]
            for k in range(n):
                cid, tdta = seg[1 + 2 * k], seg[2 + 2 * k]
                c = next(c for c in comps if c["id"] == cid)
                c["td"], c["ta"] = tdta >> 4, tdta & 15
            pos += 2 + ln
            break
        pos += 2 + ln
    end = data.rindex(b"\xff\xd9")
    bits = Bits(data[pos:end])
    hmax, vmax = max(c["h"] for c in comps), max(c["v"] for c in comps)
    mcux, mcuy = -(-w // (8 * hmax)), -(-h // (8 * vmax))
    for c in comps:
        c["w"], c["hh"] = mcux * c["h"] * 8, mcuy * c["v"] * 8
        c["plane"] = [[0.0] * c["w"] for _ in range(c["hh"])]
    for my in range(mcuy):
        for mx in range(mcux):
            for c in comps:
                for by in range(c["v"]):
                    for bx in range(c["h"]):
                        t = decode_huff(bits, huff[(0, c["td"])])
                        diff = extend(bits.bits(t), t) if t else 0
                        c["pred"] += diff
                        coef = [0] * 64
                        coef[0] = c["pred"] * qt[c["tq"]][0]
                        k = 1
                        while k < 64:
                            rs = decode_huff(bits, huff[(1, c["ta"])])
                            r, s = rs >> 4, rs & 15
                            if s == 0:
                                if r == 15:
                                    k += 16
                                    continue
                                break
                            k += r
                            coef[ZZ[k]] = extend(bits.bits(s), s) * qt[c["tq"]][k]
                            k += 1
                        px = idct(coef)
                        x0, y0 = (mx * c["h"] + bx) * 8, (my * c["v"] + by) * 8
                        for yy in range(8):
                            c["plane"][y0 + yy][x0:x0 + 8] = px[yy]
    out = bytearray()
    for y in range(h):
        for x in range(w):
            vals = []
            for c in comps:
                vals.append(c["plane"][y * c["v"] // vmax][x * c["h"] // hmax])
            Y, Cb, Cr = vals
            r, g, b = Y + 1.402 * (Cr - 128), Y - 0.344136 * (Cb - 128) - 0.714136 * (Cr - 128), Y + 1.772 * (Cb - 128)
            out += bytes(max(0, min(255, int(round(v)))) for v in (r, g, b))
    return w, h, bytes(out)
