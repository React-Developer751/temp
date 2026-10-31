"""Contact sheets: several renders of one niche (hero, about, tiles, moods) on one PNG, with timings."""
import time

from ..imagefile import encode_png
from ..jpegwrite import encode_jpeg
from ..raster import Canvas
from ..text import draw_text
from .niches import NICHES, load_all
from .palette import make_palette
from .scene import render_niche


def shrink(cv, tw, th):
    """Box-sampled downscale of a canvas to tw x th (for sheets)."""
    out = Canvas(tw, th)
    fx, fy = cv.w / float(tw), cv.h / float(th)
    sx, sy = max(1, int(fx // 3)), max(1, int(fy // 3))
    px, src, w = out.px, cv.px, cv.w
    k = 0
    for y in range(th):
        ya, yb = int(y * fy), max(int(y * fy) + 1, int((y + 1) * fy))
        for x in range(tw):
            xa, xb = int(x * fx), max(int(x * fx) + 1, int((x + 1) * fx))
            r = g = b = n = 0.0
            for yy in range(ya, min(cv.h, yb), sy):
                base = yy * w * 3
                for xx in range(xa, min(w, xb), sx):
                    i = base + xx * 3
                    r += src[i]
                    g += src[i + 1]
                    b += src[i + 2]
                    n += 1
            px[k:k + 3] = [r / n, g / n, b / n]
            k += 3
    return out


SPECS = (("hero left", 1280, 640, "left", "fit", None), ("about", 640, 600, None, "fit", None), ("close", 640, 400, None, "close", None),
         ("detail", 640, 400, None, "detail-flip", None), ("wide", 640, 400, None, "wide", None), ("dark", 640, 400, None, "fit", "dark"))


def niche_sheet(niche_ids, path, seed=1, specs=SPECS, thumb_h=170, log=print):
    load_all()
    pad, label = 6, 20
    cells = []
    rows = []
    widest = 0
    for nid in niche_ids:
        n = NICHES[nid]
        row = []
        for name, w, h, zone, variant, mood in specs:
            t = time.time()
            pal = make_palette(n.accent, mood or n.mood)
            r = render_niche(n, w, h, seed, pal, zone, variant)
            dt = time.time() - t
            log("  %-22s %-10s %5.2fs  subject %.2f" % (nid, name, dt, r.subject_score))
            row.append((name, shrink(r.canvas, int(thumb_h * w / h), thumb_h), dt, r.subject_score))
        rows.append((nid, row))
        widest = max(widest, sum(c[1].w + pad for c in row) + pad)
    H = len(rows) * (thumb_h + label + pad) + pad
    sheet = Canvas(widest, H, (0.94, 0.94, 0.95))
    for ri, (nid, row) in enumerate(rows):
        x = pad
        y = pad + ri * (thumb_h + label + pad)
        for name, cv, dt, sc in row:
            for yy in range(cv.h):
                i, j = yy * cv.w * 3, ((y + label + yy) * widest + x) * 3
                sheet.px[j:j + cv.w * 3] = cv.px[i:i + cv.w * 3]
            draw_text(sheet, ("%s %s %.1fs" % (nid, name, dt)).upper()[:44], x + cv.w / 2, y + label / 2, 8.5, (0.1, 0.1, 0.2), 0.12, max_width=cv.w)
            x += cv.w + pad
    with open(path, "wb") as fh:
        fh.write(encode_png(sheet.w, sheet.h, sheet.to_rgb_bytes()))
    return path


def set_sheet(results, report, path, thumb_h=210):
    """One PNG showing a whole site set (hero on top, the rest below) with the judge's numbers: the proof picture of a niche."""
    pad, label = 8, 22
    hero, rest = results[0], results[1:]
    hw = 3 * (thumb_h * 1.6) + 2 * pad                     # width of the lower row sets the sheet width
    rest_th = [shrink(r.canvas, int(thumb_h * r.canvas.w / r.canvas.h), thumb_h) for r in rest]
    row_w = sum(c.w for c in rest_th) + pad * (len(rest_th) + 1)
    hero_h = int(row_w * hero.canvas.h / hero.canvas.w / 1.0)
    hero_th = shrink(hero.canvas, int(row_w - 2 * pad), int((row_w - 2 * pad) * hero.canvas.h / hero.canvas.w))
    H = label + hero_th.h + pad + label + thumb_h + pad * 2 + 26
    W = max(row_w, hero_th.w + 2 * pad)
    sheet = Canvas(W, H, (0.94, 0.94, 0.95))

    def paste(cv, x, y):
        for yy in range(cv.h):
            i, j = yy * cv.w * 3, ((y + yy) * W + x) * 3
            sheet.px[j:j + cv.w * 3] = cv.px[i:i + cv.w * 3]
    head = "%s | mood %s | accent %s | min dist %d | family %.2f | hero contrast %s | redrawn %d | %.1fs" % (
        report["title"], report["mood"], report["accent"], report["min_distance"], report["palette_family"], report["hero_contrast"], report["redrawn"],
        report["seconds"])
    draw_text(sheet, head.upper()[:150], W / 2, 12, 9, (0.1, 0.1, 0.2), 0.12, max_width=W - 20)
    paste(hero_th, pad, label)
    y = label + hero_th.h + pad
    x = pad
    for r, th in zip(rest, rest_th):
        draw_text(sheet, ("%s %dx%d %dB" % (r.report["role"], r.canvas.w, r.canvas.h, r.report.get("bytes", 0))).upper(), x + th.w / 2, y + 10, 8, (0.1, 0.1, 0.2), 0.12,
                  max_width=th.w)
        paste(th, x, y + label)
        x += th.w + pad
    with open(path, "wb") as fh:                    # JPEG keeps a proof sheet around 200 KB instead of 2.5 MB
        fh.write(encode_jpeg(W, H, sheet.px, 88) if path.lower().endswith((".jpg", ".jpeg")) else encode_png(W, H, sheet.to_rgb_bytes()))
    return path
