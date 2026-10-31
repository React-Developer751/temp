#!/usr/bin/env python3
"""Developer tool (standard library only): read glyph outlines from a TrueType font and derive centrelines.

Used to build the Devanagari stroke skeletons from an OPEN-LICENCE font (Noto Sans Devanagari, SIL OFL 1.1). Not used at runtime.

    python3 tools/ttf_outlines.py FONT.ttf U+0915 out.png     # render the filled glyph and its skeleton
"""
import struct
import sys


class Font:
    def __init__(self, path):
        with open(path, "rb") as fh:
            self.data = fh.read()
        d = self.data
        n = struct.unpack(">H", d[4:6])[0]
        self.tables = {}
        for i in range(n):
            tag, _cs, off, ln = struct.unpack(">4sIII", d[12 + 16 * i:28 + 16 * i])
            self.tables[tag.decode("latin-1")] = (off, ln)
        off = self.tables["head"][0]
        self.units = struct.unpack(">H", d[off + 18:off + 20])[0]
        self.loc_fmt = struct.unpack(">h", d[off + 50:off + 52])[0]
        self.num_glyphs = struct.unpack(">H", d[self.tables["maxp"][0] + 4:self.tables["maxp"][0] + 6])[0]
        lo, ll = self.tables["loca"]
        if self.loc_fmt == 0:
            self.loca = [2 * v for v in struct.unpack(">%dH" % (self.num_glyphs + 1), d[lo:lo + 2 * (self.num_glyphs + 1)])]
        else:
            self.loca = list(struct.unpack(">%dI" % (self.num_glyphs + 1), d[lo:lo + 4 * (self.num_glyphs + 1)]))
        self.cmap = self._read_cmap()

    # ---------------------------------------------------------------- cmap
    def _read_cmap(self):
        d = self.data
        base = self.tables["cmap"][0]
        n = struct.unpack(">H", d[base + 2:base + 4])[0]
        best = {}
        for i in range(n):
            pid, eid, off = struct.unpack(">HHI", d[base + 4 + 8 * i:base + 12 + 8 * i])
            fmt = struct.unpack(">H", d[base + off:base + off + 2])[0]
            if fmt not in (4, 12):
                continue
            mapping = {}
            sub = base + off
            if fmt == 4:
                segx2 = struct.unpack(">H", d[sub + 6:sub + 8])[0]
                seg = segx2 // 2
                ends = struct.unpack(">%dH" % seg, d[sub + 14:sub + 14 + segx2])
                starts = struct.unpack(">%dH" % seg, d[sub + 16 + segx2:sub + 16 + 2 * segx2])
                deltas = struct.unpack(">%dh" % seg, d[sub + 16 + 2 * segx2:sub + 16 + 3 * segx2])
                ro_pos = sub + 16 + 3 * segx2
                ranges = struct.unpack(">%dH" % seg, d[ro_pos:ro_pos + segx2])
                for k in range(seg):
                    for c in range(starts[k], ends[k] + 1):
                        if c == 0xFFFF:
                            continue
                        if ranges[k] == 0:
                            g = (c + deltas[k]) & 0xFFFF
                        else:
                            p = ro_pos + 2 * k + ranges[k] + 2 * (c - starts[k])
                            g = struct.unpack(">H", d[p:p + 2])[0]
                            g = (g + deltas[k]) & 0xFFFF if g else 0
                        if g:
                            mapping[c] = g
            else:
                ng = struct.unpack(">I", d[sub + 12:sub + 16])[0]
                for k in range(ng):
                    s, e, g0 = struct.unpack(">III", d[sub + 16 + 12 * k:sub + 28 + 12 * k])
                    for c in range(s, e + 1):
                        mapping[c] = g0 + c - s
            if len(mapping) > len(best):
                best = mapping
        return best

    # ---------------------------------------------------------------- glyf
    def contours(self, gid, _depth=0):
        """Flattened outline of a glyph: list of closed polylines [(x, y), ...] in font units."""
        d = self.data
        go = self.tables["glyf"][0]
        a, b = self.loca[gid], self.loca[gid + 1]
        if a == b:
            return []
        p = go + a
        nc = struct.unpack(">h", d[p:p + 2])[0]
        p += 10
        if nc >= 0:
            ends = struct.unpack(">%dH" % nc, d[p:p + 2 * nc])
            p += 2 * nc
            ilen = struct.unpack(">H", d[p:p + 2])[0]
            p += 2 + ilen
            npts = (ends[-1] + 1) if nc else 0
            flags = []
            while len(flags) < npts:
                f = d[p]
                p += 1
                flags.append(f)
                if f & 8:
                    r = d[p]
                    p += 1
                    flags.extend([f] * r)
            xs, ys, v = [], [], 0
            for f in flags:
                if f & 2:
                    dx = d[p]
                    p += 1
                    v += dx if f & 16 else -dx
                elif not f & 16:
                    v += struct.unpack(">h", d[p:p + 2])[0]
                    p += 2
                xs.append(v)
            v = 0
            for f in flags:
                if f & 4:
                    dy = d[p]
                    p += 1
                    v += dy if f & 32 else -dy
                elif not f & 32:
                    v += struct.unpack(">h", d[p:p + 2])[0]
                    p += 2
                ys.append(v)
            out, start = [], 0
            for e in ends:
                pts = [(xs[i], ys[i], flags[i] & 1) for i in range(start, e + 1)]
                out.append(_flatten(pts))
                start = e + 1
            return out
        out = []                                                       # composite glyph
        if _depth > 6:
            return out
        while True:
            fl, gi = struct.unpack(">HH", d[p:p + 4])
            p += 4
            if fl & 1:
                a1, a2 = struct.unpack(">hh", d[p:p + 4])
                p += 4
            else:
                a1, a2 = struct.unpack(">bb", d[p:p + 2])
                p += 2
            m = [1.0, 0.0, 0.0, 1.0]
            if fl & 8:
                m[0] = m[3] = struct.unpack(">h", d[p:p + 2])[0] / 16384.0
                p += 2
            elif fl & 0x40:
                m[0], m[3] = [v / 16384.0 for v in struct.unpack(">hh", d[p:p + 4])]
                p += 4
            elif fl & 0x80:
                m = [v / 16384.0 for v in struct.unpack(">hhhh", d[p:p + 8])]
                p += 8
            dx, dy = (a1, a2) if fl & 2 else (0, 0)
            for c in self.contours(gi, _depth + 1):
                out.append([(m[0] * x + m[2] * y + dx, m[1] * x + m[3] * y + dy) for x, y in c])
            if not fl & 0x20:
                break
        return out

    def glyph_for(self, cp):
        return self.cmap.get(cp)


def _flatten(pts, steps=10):
    """Closed contour with on/off-curve quadratic points -> polyline."""
    n = len(pts)
    if n == 0:
        return []
    # make sure we start on an on-curve point
    start = next((i for i, q in enumerate(pts) if q[2]), None)
    if start is None:
        mid = ((pts[0][0] + pts[-1][0]) / 2.0, (pts[0][1] + pts[-1][1]) / 2.0, 1)
        pts = [mid] + pts
    else:
        pts = pts[start:] + pts[:start]
    out = [(pts[0][0], pts[0][1])]
    i = 1
    cur = pts[0]
    m = len(pts)
    while i <= m:
        q = pts[i % m]
        if q[2]:
            out.append((q[0], q[1]))
            cur = q
            i += 1
        else:
            nxt = pts[(i + 1) % m]
            if nxt[2]:
                end = nxt
                i += 2
            else:
                end = ((q[0] + nxt[0]) / 2.0, (q[1] + nxt[1]) / 2.0, 1)
                i += 1
            for k in range(1, steps + 1):
                t = k / float(steps)
                x = (1 - t) ** 2 * cur[0] + 2 * (1 - t) * t * q[0] + t * t * end[0]
                y = (1 - t) ** 2 * cur[1] + 2 * (1 - t) * t * q[1] + t * t * end[1]
                out.append((x, y))
            cur = end
    return out


# ------------------------------------------------------------------ raster + skeleton
def fill_mask(contours, scale, ox, oy, width, height):
    """Nonzero-winding fill of the outline into a height x width 0/1 grid. Pixel (px, py) = ((x-ox)*scale, (oy-y)*scale)."""
    edges = []
    for c in contours:
        pts = [((x - ox) * scale, (oy - y) * scale) for x, y in c]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            if a[1] != b[1]:
                edges.append((a, b))
    rows = []
    for py in range(height):
        yc = py + 0.5
        xs = []
        for (x0, y0), (x1, y1) in edges:
            if (y0 <= yc < y1) or (y1 <= yc < y0):
                xs.append((x0 + (yc - y0) * (x1 - x0) / (y1 - y0), 1 if y1 > y0 else -1))
        xs.sort()
        row = bytearray(width)
        wind = 0
        for k in range(len(xs) - 1):
            wind += xs[k][1]
            if wind:
                for px in range(max(0, int(xs[k][0] + 0.5)), min(width, int(xs[k + 1][0] + 0.5))):
                    row[px] = 1
        rows.append(row)
    return rows


def thin(mask):
    """Zhang-Suen thinning of a 0/1 grid (list of bytearrays), in place. Returns the grid."""
    h, w = len(mask), len(mask[0])
    changed = True
    nb = ((-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1))
    while changed:
        changed = False
        for step in (0, 1):
            kill = []
            for y in range(1, h - 1):
                for x in range(1, w - 1):
                    if not mask[y][x]:
                        continue
                    p = [mask[y + dy][x + dx] for dy, dx in nb]
                    s = sum(p)
                    if s < 2 or s > 6:
                        continue
                    trans = sum(1 for k in range(8) if p[k] == 0 and p[(k + 1) % 8] == 1)
                    if trans != 1:
                        continue
                    if step == 0 and (p[0] * p[2] * p[4] or p[2] * p[4] * p[6]):
                        continue
                    if step == 1 and (p[0] * p[2] * p[6] or p[0] * p[4] * p[6]):
                        continue
                    kill.append((y, x))
            for y, x in kill:
                mask[y][x] = 0
            changed = changed or bool(kill)
    return mask


def trace(skel):
    """Skeleton pixels -> polylines of (x, y) pixel coordinates (follows chains between endpoints/junctions)."""
    h, w = len(skel), len(skel[0])
    nbrs = ((-1, 0), (0, 1), (1, 0), (0, -1), (-1, 1), (1, 1), (1, -1), (-1, -1))

    def around(y, x):
        return [(y + dy, x + dx) for dy, dx in nbrs if 0 <= y + dy < h and 0 <= x + dx < w and skel[y + dy][x + dx]]
    pix = {(y, x) for y in range(h) for x in range(w) if skel[y][x]}
    nodes = {q for q in pix if len(around(*q)) != 2}
    seen, lines = set(), []

    def walk(a, b):
        line = [a, b]
        seen.add((a, b))
        seen.add((b, a))
        prev, cur = a, b
        while cur not in nodes:
            nxt = [q for q in around(*cur) if q != prev and (cur, q) not in seen]
            if not nxt:
                break
            q = min(nxt, key=lambda t: abs(t[0] - cur[0]) + abs(t[1] - cur[1]))
            seen.add((cur, q))
            seen.add((q, cur))
            line.append(q)
            prev, cur = cur, q
        return line
    for n0 in nodes:
        for q in around(*n0):
            if (n0, q) not in seen:
                lines.append(walk(n0, q))
    for q in pix:                                                       # closed loops with no node
        if not any(((q, r) in seen) for r in around(*q)):
            ring = walk(q, around(*q)[0])
            lines.append(ring)
    return [[(x, y) for y, x in ln] for ln in lines]


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    dx, dy = x1 - x0, y1 - y0
    norm = (dx * dx + dy * dy) ** 0.5 or 1e-9
    k, dmax = 0, 0.0
    for i in range(1, len(pts) - 1):
        d = abs(dy * pts[i][0] - dx * pts[i][1] + x1 * y0 - y1 * x0) / norm
        if d > dmax:
            k, dmax = i, d
    if dmax <= eps:
        return [pts[0], pts[-1]]
    return rdp(pts[:k + 1], eps)[:-1] + rdp(pts[k:], eps)


def skeleton_of(font, cp, px_per_em=400, eps=1.2, pad=20):
    """Centreline polylines of a codepoint in FONT UNITS: returns (polylines, bbox, scale) or None."""
    gid = font.glyph_for(cp)
    if gid is None:
        return None
    cs = font.contours(gid)
    if not cs:
        return None
    xs = [x for c in cs for x, _ in c]
    ys = [y for c in cs for _, y in c]
    scale = px_per_em / float(font.units)
    ox, oy = min(xs) - pad / scale, max(ys) + pad / scale
    w = int((max(xs) - min(xs)) * scale + 2 * pad)
    h = int((max(ys) - min(ys)) * scale + 2 * pad)
    skel = thin(fill_mask(cs, scale, ox, oy, w, h))
    lines = [rdp(ln, eps) for ln in trace(skel)]
    return [[(ox + x / scale, oy - y / scale) for x, y in ln] for ln in lines if len(ln) > 1], (min(xs), min(ys), max(xs), max(ys)), scale


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    sys.path.insert(0, __file__.rsplit("/tools/", 1)[0])
    from pixelmath import encode_png
    f = Font(sys.argv[1])
    cp = int(sys.argv[2].replace("U+", "0x"), 16)
    cs = f.contours(f.glyph_for(cp))
    res = skeleton_of(f, cp)
    xs = [x for c in cs for x, _ in c]
    ys = [y for c in cs for _, y in c]
    sc = 300.0 / f.units
    ox, oy = min(xs) - 15 / sc, max(ys) + 15 / sc
    W, H = int((max(xs) - min(xs)) * sc + 30), int((max(ys) - min(ys)) * sc + 30)
    mask = fill_mask(cs, sc, ox, oy, W, H)
    px = bytearray(b"\xff" * (W * H * 3))
    for y in range(H):
        for x in range(W):
            if mask[y][x]:
                i = (y * W + x) * 3
                px[i:i + 3] = b"\xc8\xd0\xe0"
    for ln in res[0]:
        for (ax, ay), (bx, by) in zip(ln, ln[1:]):
            n = int(max(abs(bx - ax), abs(by - ay)) * sc) + 1
            for k in range(n + 1):
                x = int(((ax + (bx - ax) * k / n) - ox) * sc)
                y = int((oy - (ay + (by - ay) * k / n)) * sc)
                for dx in (0, 1):
                    for dy in (0, 1):
                        if 0 <= x + dx < W and 0 <= y + dy < H:
                            i = ((y + dy) * W + x + dx) * 3
                            px[i:i + 3] = b"\xd0\x10\x10"
    open(sys.argv[3], "wb").write(encode_png(W, H, bytes(px)))
    print("glyph", f.glyph_for(cp), "contours", len(cs), "skeleton polylines", len(res[0]), "units/em", f.units)
