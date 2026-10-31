"""Colour theory: palettes built from a base hue by a harmony rule, instead of random colours.

    analogous       neighbouring hues (calm, natural)
    complementary   the opposite hue (maximum contrast)
    split           the base plus the two hues beside its complement
    triadic         three hues 120 degrees apart (lively)
    tetradic        four hues 90 degrees apart (rich)
    monochrome      one hue in many lightnesses

The base hue is a user colour if the prompt has one, otherwise it comes from the prompt's own vector (so the same prompt
always gets the same palette). The prompt can also name the rule: "analogous", "complementary", "triadic", ...
"""
import colorsys

SCHEME_NAMES = ("analogous", "complementary", "split", "triadic", "tetradic", "monochrome")
OFFSETS = {
    "analogous": (0, 30, -30, 60, -60),
    "complementary": (0, 180, 20, 200),
    "split": (0, 150, 210, 30),
    "triadic": (0, 120, 240, 60),
    "tetradic": (0, 90, 180, 270),
    "monochrome": (0,),
}


def scheme_palette(hue, scheme, n=5, sat=0.68, val=0.92):
    """n colours (rgb 0..1) following the rule around `hue` (0..1)."""
    offs = OFFSETS[scheme]
    out = []
    for i in range(n):
        h = (hue + offs[i % len(offs)] / 360.0) % 1.0
        ring = i // len(offs)
        if scheme == "monochrome":
            t = i / max(1, n - 1)
            out.append(colorsys.hsv_to_rgb(hue % 1.0, 0.35 + 0.55 * t, 0.45 + 0.50 * t))
        else:
            out.append(colorsys.hsv_to_rgb(h, max(0.35, sat - 0.12 * ring), max(0.5, val - 0.18 * ring)))
    return out


def scheme_of(parsed, vec=None):
    for f in sorted(parsed.flags):
        if f.startswith("scheme_"):
            return f[7:]
    if vec is None:
        return "analogous"
    return SCHEME_NAMES[int(abs(vec[3 % len(vec)]) * 997) % len(SCHEME_NAMES)]


def base_hue(parsed, vec):
    cols = [e.color for e in parsed.entities if e.color] + list(parsed.loose_colors)
    if parsed.background:
        cols.append(parsed.background)
    if cols:
        return colorsys.rgb_to_hsv(*cols[0])[0]
    return (vec[0] * 0.5 + 0.5) % 1.0


def harmonic_palette(parsed, vec, n=5):
    """The default palette of a picture: harmonious, deterministic, and anchored on the user's colour if there is one."""
    return scheme_palette(base_hue(parsed, vec), scheme_of(parsed, vec), n)


def gradient(colors, t, loop=True):
    """Colour at position t (0..1) along the palette (wraps around when loop)."""
    n = len(colors)
    if n == 1:
        return colors[0]
    if loop:
        t = (t % 1.0) * n
        i = int(t)
        f = t - i
        a, b = colors[i % n], colors[(i + 1) % n]
    else:
        t = min(max(t, 0.0), 1.0) * (n - 1)
        i = min(int(t), n - 2)
        f = t - i
        a, b = colors[i], colors[i + 1]
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f)
