"""Minimal PDF text extractor (stdlib): Chrome/Skia PDFs with Type0 fonts + ToUnicode maps."""
import re, sys, zlib
data = open(sys.argv[1], "rb").read()
objs = {}
for m in re.finditer(rb"(\d+) 0 obj(.*?)endobj", data, re.S):
    objs[int(m.group(1))] = m.group(2)
def stream(body):
    m = re.search(rb"stream\r?\n(.*?)\r?\nendstream", body, re.S)
    if not m: return None
    raw = m.group(1)
    if b"FlateDecode" in body.split(b"stream")[0]:
        try: return zlib.decompress(raw)
        except Exception: 
            try: return zlib.decompressobj().decompress(raw)
            except Exception: return None
    return raw
def parse_cmap(txt):
    mp = {}
    for blk in re.findall(rb"beginbfchar(.*?)endbfchar", txt, re.S):
        for a, b in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            mp[int(a, 16)] = bytes.fromhex(b.decode()).decode("utf-16-be", "replace")
    for blk in re.findall(rb"beginbfrange(.*?)endbfrange", txt, re.S):
        for a, b, c in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
            lo, hi, st = int(a, 16), int(b, 16), int(c, 16)
            for i in range(lo, hi + 1):
                mp[i] = chr(st + i - lo)
        for a, b, arr in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]", blk, re.S):
            lo = int(a, 16)
            for i, h in enumerate(re.findall(rb"<([0-9A-Fa-f]+)>", arr)):
                mp[lo + i] = bytes.fromhex(h.decode()).decode("utf-16-be", "replace")
    return mp
fonts = {}   # obj -> cmap
for n, body in objs.items():
    if b"/ToUnicode" in body:
        t = re.search(rb"/ToUnicode (\d+) 0 R", body)
        if t:
            s = stream(objs[int(t.group(1))])
            if s: fonts[n] = parse_cmap(s)
# page -> font resource names
pages = []
for n, body in objs.items():
    if re.search(rb"/Type /Page\b", body) and b"/Contents" in body:
        pages.append((n, body))
def page_fonts(body):
    res = body
    m = re.search(rb"/Resources (\d+) 0 R", body)
    if m: res = objs[int(m.group(1))]
    f = re.search(rb"/Font <<(.*?)>>", res, re.S)
    out = {}
    if f:
        for name, ref in re.findall(rb"/(\w+) (\d+) 0 R", f.group(1)):
            out[name] = int(ref)
    else:
        m2 = re.search(rb"/Font (\d+) 0 R", res)
        if m2:
            for name, ref in re.findall(rb"/(\w+) (\d+) 0 R", objs[int(m2.group(1))]):
                out[name] = int(ref)
    return out
def order(body):
    return [int(x) for x in re.findall(rb"(\d+) 0 R", re.search(rb"/Contents (\[.*?\]|\d+ 0 R)", body, re.S).group(1))]
out_pages = []
for pn, body in sorted(pages):
    pf = page_fonts(body)
    cm = {k: fonts.get(v, {}) for k, v in pf.items()}
    # Type0 font -> descendant; the ToUnicode is on the Type0 object itself
    text = []
    for cn in order(body):
        s = stream(objs[cn]) or b""
        cur = {}
        y_last = None
        for tok in re.finditer(rb"/(\w+) [\d.]+ Tf|\[(.*?)\]\s*TJ|<([0-9A-Fa-f]*)>\s*Tj|([\d.\-]+) ([\d.\-]+) Td|[\d.\-]+ [\d.\-]+ [\d.\-]+ [\d.\-]+ ([\d.\-]+) ([\d.\-]+) Tm|(T\*|ET)", s, re.S):
            if tok.group(1):
                cur = cm.get(tok.group(1), {})
            elif tok.group(2) is not None or tok.group(3) is not None:
                hexes = re.findall(rb"<([0-9A-Fa-f]*)>", tok.group(2)) if tok.group(2) is not None else [tok.group(3)]
                kern = re.findall(rb"\](?:|)|(-?\d+\.?\d*)", tok.group(2) or b"")
                for h in hexes:
                    h = h.decode()
                    for i in range(0, len(h), 4):
                        text.append(cur.get(int(h[i:i+4], 16), "?"))
            elif tok.group(6) is not None:
                y = float(tok.group(7))
                if y_last is not None and abs(y - y_last) > 1: text.append("\n")
                y_last = y
            elif tok.group(5) is not None:
                if abs(float(tok.group(5))) > 1: text.append("\n")
            elif tok.group(8) == b"T*":
                text.append("\n")
    out_pages.append("".join(text))
print("\n\n=====PAGE=====\n".join(out_pages))
