"""Render one niche scene: dry run -> camera -> real run -> text-zone contrast. Also the per-picture judge pieces."""
from dataclasses import dataclass

from .palette import make_palette
from .stage import ASPECT, Camera, Stage

ZONES = {                       # text zone as fractions of the picture: (x0, y0, x1, y1)
    "left": (0.05, 0.14, 0.50, 0.86),
    "center": (0.14, 0.20, 0.86, 0.56),
    "bottom": (0.05, 0.64, 0.95, 0.94),
}
FREE = {                        # where the subject should live when that zone is reserved
    "left": (0.49, 0.05, 0.99, 0.97),
    "center": (0.08, 0.58, 0.92, 0.98),
    "bottom": (0.06, 0.04, 0.94, 0.62),
    None: (0.08, 0.08, 0.92, 0.94),
}
VARIANTS = ("fit", "close", "detail", "wide", "fit-flip", "close-flip", "detail-flip", "wide-flip")


@dataclass
class Rendered:
    canvas: object
    stage: object
    camera: Camera
    variant: str
    zone: tuple
    subject_score: float
    subject_visible: dict


def _union(boxes):
    return (min(b[1] for b in boxes), min(b[2] for b in boxes), max(b[3] for b in boxes), max(b[4] for b in boxes))


def _fit_zoom(bw, bh, free, fa, pad=0.03):
    fw, fh = (free[2] - free[0]) * (1 - pad), (free[3] - free[1]) * (1 - pad)
    return min(fw * fa / max(bw, 1e-6), fh / max(bh, 1e-6))


def solve_camera(dry, W, H, zone_name, variant):
    """Zoom / pan / mirror for one picture so the subjects sit in the right part of the frame."""
    flip = variant.endswith("-flip")
    kind = variant.replace("-flip", "")
    fa = W / float(H)
    subs = dry.cluster or dry.subjects
    if not subs:
        return Camera(ASPECT / 2, 0.5, 1.0, flip)
    ub = _union(subs)
    free = FREE.get(zone_name, FREE[None])
    bw, bh = ub[2] - ub[0], ub[3] - ub[1]
    cu, cv_ = (ub[0] + ub[2]) / 2, (ub[1] + ub[3]) / 2
    fcx, fcy = (free[0] + free[2]) / 2, (free[1] + free[3]) / 2
    if kind == "close":
        pool = dry.subjects or subs
        main = max(pool, key=lambda s: (s[3] - s[1]) * (s[4] - s[2]))
        mb = (main[1], main[2], main[3], main[4])
        z = _fit_zoom(mb[2] - mb[0], mb[3] - mb[1], (0.06, 0.06, 0.94, 0.94), fa, 0.0) * 1.0
        z = min(max(z, _fit_zoom(bw, bh, free, fa) * 1.15), 2.4)
        cu, cv_ = (mb[0] + mb[2]) / 2, (mb[1] + mb[3]) / 2
        fcx = fcy = 0.5
    elif kind == "detail":
        pts = list(dry.focus_points.values())
        if pts:
            cu, cv_ = pts[0]
        elif len(subs) > 1:
            second = sorted(subs, key=lambda s: (s[3] - s[1]) * (s[4] - s[2]))[0]
            cu, cv_ = (second[1] + second[3]) / 2, (second[2] + second[4]) / 2
        z = min(4.0, _fit_zoom(bw, bh, free, fa) * 1.9)
        fcx = fcy = 0.5
    elif kind == "wide":
        z = max(0.55, _fit_zoom(bw, bh, free, fa) * 0.78)
    else:
        z = _fit_zoom(bw, bh, free, fa)
    z = min(max(z, 0.55), 2.4 if kind in ('close', 'detail') else 1.45)
    cam = Camera(0.0, 0.0, z, flip)
    sgn = -1.0 if flip else 1.0
    cam.cx = cu - sgn * (fcx - 0.5) * fa / z
    cam.cy = cv_ - (fcy - 0.5) / z
    return cam


def visible_fraction(box, cam, W, H):
    sc = H * cam.zoom
    sgn = -1.0 if cam.flip else 1.0
    xs = [W / 2 + (u - cam.cx) * sc * sgn for u in (box[1], box[3])]
    ys = [H / 2 + (v - cam.cy) * sc for v in (box[2], box[4])]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    area = max(1e-9, (x1 - x0) * (y1 - y0))
    iw = max(0.0, min(x1, W) - max(x0, 0.0))
    ih = max(0.0, min(y1, H) - max(y0, 0.0))
    return iw * ih / area


def render_niche(niche, width, height, seed, pal, zone_name=None, variant="fit", light_u=None, view=None):
    """Draw `niche` into a width x height canvas. Returns Rendered (canvas is graded but the text-zone scrim is not applied yet)."""
    lu = light_u if light_u is not None else (-0.6 if variant.endswith("flip") else 0.6) * (1 if seed % 2 == 0 else -1) * -1
    dry = Stage(width, height, pal, seed, dry=True, light_u=lu)
    niche.fn(dry)
    cam = solve_camera(dry, width, height, zone_name, variant)
    if view:                                                       # (zoom factor, pan u, pan v): another crop of the same view
        cam.zoom = max(0.5, min(cam.zoom * view[0], 2.8))
        cam.cx += view[1]
        cam.cy += view[2]
    S = Stage(width, height, pal, seed, cam=cam, light_u=lu)
    niche.fn(S)
    cv = S.finish()
    vis = {}
    for name in niche.subjects:
        boxes = [b for b in S.subjects if b[0] == name]
        vis[name] = max((visible_fraction(b, cam, width, height) for b in boxes), default=0.0)
    kind = variant.replace('-flip', '')
    score = (max(vis.values()) if kind in ('detail', 'close') else min(vis.values())) if vis else 0.0
    return Rendered(cv, S, cam, variant, ZONES.get(zone_name), score, vis)
