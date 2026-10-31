"""Devices, office items and documents."""
import math

from .core import WHITE, mix, prop, scale


def _ui(c, u, v, w, h, accent, dark=False):
    """A tiny analytics dashboard drawn inside the rectangle centred at (u, v) of size (w, h)."""
    x0, x1, y0, y1 = u - w / 2, u + w / 2, v - h / 2, v + h / 2
    bg = c.col((0.10, 0.12, 0.19)) if dark else c.col((0.95, 0.96, 0.99))
    card = c.col((0.17, 0.20, 0.30)) if dark else c.col((1.0, 1.0, 1.0))
    c.rect(u, v, w, h, bg, lift=0.0)
    c.rect(u, y1 - 0.06 * h, w, 0.12 * h, accent, lift=0.1)
    c.circle(x1 - 0.05 * w, y1 - 0.06 * h, 0.03 * h, c.col((1, 1, 1)), lift=0)
    c.rect(x0 + 0.10 * w, v - 0.06 * h, 0.20 * w, 0.88 * h, scale(accent, 0.62), lift=0.05)
    for k in range(5):
        c.rect(x0 + 0.10 * w, y1 - 0.20 * h - k * 0.12 * h, 0.13 * w, 0.03 * h, mix(accent, WHITE, 0.6 if k else 0.9), r=0.01, lift=0)
    cw = 0.19 * w
    for k in range(3):                                        # KPI cards
        cx = x0 + 0.31 * w + k * (cw + 0.03 * w) + cw / 2
        c.rect(cx, y1 - 0.26 * h, cw, 0.20 * h, card, r=0.015, lift=0.0)
        c.rect(cx - cw * 0.1, y1 - 0.30 * h, cw * 0.5, 0.03 * h, mix(accent, WHITE, 0.2 * k), r=0.01, lift=0)
        c.rect(cx - cw * 0.18, y1 - 0.23 * h, cw * 0.35, 0.025 * h, c.col((0.6, 0.62, 0.7)), r=0.01, lift=0)
    c.rect(x0 + 0.45 * w, y0 + 0.27 * h, 0.40 * w, 0.40 * h, card, r=0.015, lift=0.0)           # bar chart panel
    for k, hh in enumerate((0.12, 0.2, 0.15, 0.27, 0.22, 0.31)):
        c.rect(x0 + 0.29 * w + k * 0.055 * w, y0 + 0.09 * h + hh * h / 2, 0.035 * w, hh * h, mix(accent, WHITE, 0.12 * (k % 3)), lift=0.05)
    pts = [(x0 + 0.29 * w + k * 0.055 * w, y0 + 0.2 * h + (0.04 * math.sin(k * 1.2) + 0.03 * k) * h) for k in range(6)]
    c.path(pts, 0.012 * h * 4, c.col((1.0, 0.62, 0.15)), smooth=True)
    c.rect(x1 - 0.20 * w, y0 + 0.27 * h, 0.30 * w, 0.40 * h, card, r=0.015, lift=0.0)           # donut panel
    cu, cv_, rr = x1 - 0.20 * w, y0 + 0.27 * h, 0.12 * h
    c.arc(cu, cv_, rr, 90, 330, 0.05 * h, accent)
    c.arc(cu, cv_, rr, 330, 450, 0.05 * h, c.col((1.0, 0.62, 0.15)))


@prop("laptop", aspect=1.45, place="table", nominal=0.36, category="tech", words=("computer", "macbook", "notebook", "laptops", "pc", "software", "app", "website", "web", "online", "digital", "saas", "startup"))
def laptop(c, color):
    c.shadow(0.0, 0.01, 1.4, 0.07)
    accent = c.pick(color, (0.25, 0.47, 0.92))
    c.rect(0, 0.56, 0.86, 0.60, c.col((0.16, 0.17, 0.21)), r=0.035, lift=0.06)
    _ui(c, 0, 0.57, 0.78, 0.52, accent)
    c.poly([(-0.46, 0.255), (0.46, 0.255), (0.62, 0.17), (-0.62, 0.17)], c.col((0.80, 0.82, 0.87)), lift=0.12)
    c.rect(0, 0.145, 1.24, 0.045, c.col((0.66, 0.68, 0.74)), r=0.02, lift=0.1)
    c.rect(0, 0.205, 0.22, 0.02, c.col((0.60, 0.62, 0.69)), r=0.01, lift=0)


@prop("monitor", aspect=1.35, place="table", nominal=0.42, category="tech", words=("dashboard", "screen", "desktop", "monitors", "display", "analytics", "crm", "interface", "ui"))
def monitor(c, color):
    c.shadow(0.0, 0.01, 0.8, 0.06)
    accent = c.pick(color, (0.25, 0.47, 0.92))
    c.rect(0, 0.10, 0.5, 0.045, c.col((0.72, 0.74, 0.80)), r=0.02, lift=0.1)
    c.rect(0, 0.2, 0.09, 0.2, c.col((0.78, 0.80, 0.85)), lift=0.08)
    c.rect(0, 0.60, 1.20, 0.78, c.col((0.16, 0.17, 0.21)), r=0.04, lift=0.08)
    _ui(c, 0, 0.60, 1.10, 0.68, accent)
    c.circle(0, 0.215, 0.012, c.col((0.45, 0.47, 0.55)), lift=0)


@prop("phone", aspect=0.52, place="table", nominal=0.4, category="tech", words=("mobile", "smartphone", "iphone", "android", "phones", "cellphone", "whatsapp", "sms"))
def phone(c, color):
    c.shadow(0.02, 0.01, 0.5, 0.05)
    accent = c.pick(color, (0.20, 0.72, 0.52))
    c.rect(0, 0.5, 0.50, 0.98, c.col((0.14, 0.15, 0.19)), r=0.09, lift=0.1)
    c.rect(0, 0.5, 0.45, 0.91, c.col((0.96, 0.97, 0.99)), r=0.06, lift=0.0)
    c.rect(0, 0.84, 0.45, 0.22, accent, r=0.04, lift=0.12)
    c.circle(-0.12, 0.84, 0.05, c.col((1, 1, 1)), lift=0)
    c.rect(0.06, 0.86, 0.22, 0.025, c.col((1, 1, 1)), r=0.01, lift=0)
    c.rect(0.02, 0.81, 0.14, 0.02, mix(accent, WHITE, 0.6), r=0.01, lift=0)
    for k in range(3):
        c.rect(0, 0.62 - k * 0.17, 0.38, 0.13, c.col((1, 1, 1)), r=0.02, lift=0.03)
        c.circle(-0.12, 0.62 - k * 0.17, 0.04, mix(accent, WHITE, 0.2 * k), lift=0)
        c.rect(0.06, 0.64 - k * 0.17, 0.2, 0.02, c.col((0.55, 0.58, 0.66)), r=0.01, lift=0)
        c.rect(0.03, 0.60 - k * 0.17, 0.14, 0.018, c.col((0.78, 0.8, 0.86)), r=0.01, lift=0)
    c.rect(0, 0.97, 0.16, 0.02, c.col((0.05, 0.05, 0.08)), r=0.01, lift=0)
    c.rect(0, 0.10, 0.20, 0.014, c.col((0.7, 0.72, 0.78)), r=0.007, lift=0)


@prop("tablet", aspect=1.4, place="table", nominal=0.3, fill=0.9, category="tech", words=("tablets", "ipad"))
def tablet(c, color):
    c.shadow(0.0, 0.03, 1.2, 0.06)
    accent = c.pick(color, (0.55, 0.35, 0.85))
    c.rect(0, 0.5, 1.28, 0.88, c.col((0.14, 0.15, 0.19)), r=0.07, lift=0.08)
    _ui(c, 0, 0.5, 1.18, 0.78, accent)


@prop("camera", aspect=1.5, place="table", nominal=0.28, fill=0.78, category="tech", words=("cameras", "photography", "photo", "photographer", "photos", "film"))
def camera(c, color):
    c.shadow(0.0, 0.03, 1.2, 0.07)
    body = c.pick(color, (0.20, 0.21, 0.25))
    c.rect(-0.2, 0.80, 0.34, 0.14, scale(body, 0.8), r=0.03)
    c.rect(0.32, 0.77, 0.2, 0.1, c.col((0.85, 0.86, 0.9)), r=0.02)
    c.rect(0, 0.45, 1.0, 0.62, body, r=0.08, lift=0.12)
    c.rect(-0.38, 0.42, 0.2, 0.48, scale(body, 0.7), r=0.05, lift=0.05)
    c.rect(0, 0.62, 1.0, 0.05, c.col((0.6, 0.62, 0.68)), lift=0.1, alpha=0.5)
    c.circle(0.05, 0.45, 0.29, c.col((0.08, 0.08, 0.10)), lift=0.1)
    c.circle(0.05, 0.45, 0.24, c.col((0.30, 0.33, 0.40)), lift=0.15)
    c.circle(0.05, 0.45, 0.18, c.col((0.10, 0.14, 0.30)), lift=0.2)
    c.circle(0.05, 0.45, 0.10, c.col((0.04, 0.05, 0.12)), lift=0.1)
    c.circle(-0.02, 0.52, 0.04, c.col((1, 1, 1)), lift=0, alpha=0.7)
    c.circle(0.40, 0.62, 0.025, c.col((0.9, 0.25, 0.25)), lift=0)
    c.circle(-0.42, 0.66, 0.025, c.col((0.85, 0.86, 0.9)), lift=0)


@prop("headphones", aspect=1.0, place="table", nominal=0.3, category="tech", words=("headphone", "earphones", "audio", "music", "podcast"))
def headphones(c, color):
    c.shadow(0.0, 0.02, 0.9, 0.07)
    col = c.pick(color, (0.92, 0.30, 0.38))
    dark = c.col((0.16, 0.17, 0.22))
    c.arc(0, 0.46, 0.40, 8, 172, 0.075, dark, ry=0.46)
    for sgn in (-1, 1):
        c.rect(sgn * 0.40, 0.47, 0.06, 0.2, dark, r=0.02)
        c.ellipse(sgn * 0.40, 0.33, 0.14, 0.22, col, lift=0.15)
        c.ellipse(sgn * 0.40 - sgn * 0.03, 0.33, 0.09, 0.15, scale(col, 0.7), lift=0.05)
        c.ellipse(sgn * 0.40 - sgn * 0.06, 0.38, 0.03, 0.06, WHITE, lift=0, alpha=0.3)


@prop("book", aspect=0.74, place="table", nominal=0.3, category="office", words=("books", "textbook", "reading", "study", "studying", "library", "ebook", "novel", "education", "learning", "course", "courses"))
def book(c, color):
    c.shadow(0.03, 0.01, 0.8, 0.07)
    cover = c.pick(color, (0.22, 0.45, 0.82))
    c.rect(0.01, 0.5, 0.64, 0.98, scale(cover, 0.55), r=0.02, lift=0.05)                 # back/shadow
    c.rect(0.30, 0.49, 0.06, 0.90, c.col((0.97, 0.94, 0.86)), lift=0.02)                  # pages
    for k in range(5):
        c.line(0.275, 0.12 + k * 0.17, 0.33, 0.12 + k * 0.17, 0.006, c.col((0.8, 0.77, 0.7)))
    c.rect(-0.02, 0.5, 0.62, 0.98, cover, r=0.025, lift=0.12)
    c.rect(-0.27, 0.5, 0.06, 0.98, scale(cover, 0.72), r=0.01, lift=0.05)                 # spine
    c.rect(0.0, 0.70, 0.40, 0.045, c.col((1.0, 0.92, 0.55)), r=0.015, lift=0)
    c.rect(0.0, 0.62, 0.28, 0.03, c.col((1.0, 0.92, 0.55)), r=0.012, lift=0, alpha=0.8)
    c.circle(0.0, 0.34, 0.10, c.col((1.0, 0.92, 0.55)), lift=0.05)
    c.circle(0.0, 0.34, 0.06, cover, lift=0)
    c.poly([(0.18, 0.99), (0.24, 0.99), (0.24, 0.84), (0.21, 0.87), (0.18, 0.84)], c.col((0.88, 0.2, 0.25)), lift=0)


@prop("document", aspect=0.74, place="table", nominal=0.36, category="office",
      words=("documents", "paper", "papers", "contract", "invoice", "report", "file", "files", "letter", "certified", "notary", "notarised", "notarized", "paperwork", "assignment", "assignments", "essay", "thesis", "dissertation", "homework"))
def document(c, color):
    c.shadow(0.03, 0.01, 0.8, 0.06)
    accent = c.pick(color, (0.24, 0.48, 0.88))
    c.rect(0.06, 0.48, 0.66, 0.94, c.col((0.86, 0.88, 0.93)), r=0.02, lift=0.0)             # sheet behind
    c.rect(0, 0.5, 0.68, 0.96, c.col((1.0, 1.0, 1.0)), r=0.02, lift=0.03)
    c.poly([(0.22, 0.98), (0.34, 0.98), (0.34, 0.86)], c.col((0.82, 0.85, 0.92)), lift=0.0)
    c.rect(-0.04, 0.84, 0.46, 0.06, accent, r=0.015, lift=0.1)
    widths = (0.52, 0.46, 0.52, 0.30, 0.50, 0.40)
    for k, wd in enumerate(widths):
        c.rect(-0.34 + 0.02 + wd / 2, 0.70 - k * 0.075, wd, 0.026, c.col((0.72, 0.75, 0.82)), r=0.012, lift=0)
    red = c.col((0.86, 0.15, 0.22))
    c.poly([(0.14, 0.20), (0.10, 0.04), (0.17, 0.09), (0.23, 0.02), (0.22, 0.20)], scale(red, 0.85), lift=0)
    c.circle(0.17, 0.25, 0.11, red, lift=0.12)
    c.ring(0.17, 0.25, 0.075, 0.016, c.col((1.0, 0.9, 0.9)))
    c.poly([(0.17, 0.31), (0.186, 0.265), (0.23, 0.26), (0.195, 0.235), (0.205, 0.19), (0.17, 0.215), (0.135, 0.19), (0.145, 0.235), (0.11, 0.26), (0.154, 0.265)], c.col((1.0, 0.95, 0.95)), lift=0)
    c.path([(-0.28, 0.14), (-0.22, 0.20), (-0.16, 0.12), (-0.10, 0.19), (-0.04, 0.13)], 0.014, c.col((0.2, 0.25, 0.5)))


@prop("certificate", aspect=1.4, place="table", nominal=0.3, fill=0.72, category="office", words=("diploma", "degree", "award", "certificates", "graduation", "transcript"))
def certificate(c, color):
    c.shadow(0.02, 0.1, 1.3, 0.07)
    gold = c.col((0.86, 0.68, 0.20))
    c.rect(0, 0.45, 1.3, 0.90, c.col((0.99, 0.97, 0.90)), r=0.02, lift=0.03)
    c.rect(0, 0.45, 1.22, 0.82, gold, r=0.015, lift=0.0)
    c.rect(0, 0.45, 1.18, 0.78, c.col((0.99, 0.97, 0.90)), r=0.01, lift=0.0)
    accent = c.pick(color, (0.20, 0.30, 0.60))
    c.rect(0, 0.70, 0.7, 0.07, accent, r=0.02, lift=0.08)
    for k, wd in enumerate((0.8, 0.62, 0.74)):
        c.rect(0, 0.56 - k * 0.09, wd, 0.028, c.col((0.74, 0.74, 0.8)), r=0.012, lift=0)
    red = c.col((0.80, 0.14, 0.2))
    c.poly([(-0.06, 0.28), (-0.10, 0.08), (-0.02, 0.15), (0.0, 0.05), (0.0, 0.28)], scale(red, 0.85), lift=0)
    c.poly([(0.06, 0.28), (0.10, 0.08), (0.02, 0.15), (0.0, 0.05), (0.0, 0.28)], red, lift=0)
    c.circle(0.0, 0.30, 0.10, gold, lift=0.15)
    c.circle(0.0, 0.30, 0.07, scale(gold, 0.85), lift=0.1)
    c.path([(-0.5, 0.18), (-0.42, 0.25), (-0.34, 0.15), (-0.26, 0.24), (-0.18, 0.17)], 0.015, c.col((0.2, 0.25, 0.5)))


@prop("globe", aspect=0.85, place="table", nominal=0.38, category="office", words=("world", "worldwide", "international", "global", "earth", "languages", "language", "translation", "translate", "translator", "translators", "translations", "multilingual", "travel", "geography"))
def globe(c, color):
    c.shadow(0.0, 0.01, 0.6, 0.06)
    ocean = c.pick(color, (0.20, 0.50, 0.88))
    c.arc(0, 0.57, 0.43, 205, 335, 0.035, c.col((0.45, 0.47, 0.55)), ry=0.43)
    c.rect(0, 0.07, 0.40, 0.05, c.col((0.30, 0.32, 0.40)), r=0.02)
    c.rect(0, 0.15, 0.05, 0.14, c.col((0.45, 0.47, 0.55)))
    c.circle(0, 0.60, 0.38, ocean, lift=0.2)
    green = c.col((0.35, 0.72, 0.38))
    for u, v, a, b, ang in ((-0.12, 0.70, 0.13, 0.08, 25), (0.12, 0.50, 0.09, 0.15, -15), (-0.18, 0.48, 0.07, 0.05, 40), (0.16, 0.76, 0.07, 0.04, 0), (-0.02, 0.58, 0.05, 0.07, 10)):
        c.ellipse(u, v, a, b, green, angle=ang, lift=0.1)
    light = mix(ocean, WHITE, 0.45)
    c.eoutline(0, 0.60, 0.17, 0.38, 0.012, light, alpha=0.7)
    c.eoutline(0, 0.60, 0.30, 0.38, 0.012, light, alpha=0.7)
    for dv in (-0.2, 0.0, 0.2):
        half = math.sqrt(max(0.0, 0.38 ** 2 - dv ** 2)) - 0.012
        c.line(-half, 0.60 + dv, half, 0.60 + dv, 0.012, light, alpha=0.7)
    c.ellipse(-0.14, 0.78, 0.09, 0.06, WHITE, angle=40, lift=0, alpha=0.28)


@prop("pencil", aspect=0.5, place="table", nominal=0.36, category="office", words=("pen", "writing", "pencils", "write", "stationery", "edit", "editing", "proofreading"))
def pencil(c, color):
    c.shadow(0.12, 0.01, 0.5, 0.05)
    body = c.pick(color, (1.0, 0.80, 0.18))
    piv, ang = (0.0, 0.5), 28
    c.poly([(-0.07, 0.10), (0.07, 0.10), (0.07, 0.82), (-0.07, 0.82)], body, lift=0.15, angle=ang, pivot=piv)
    c.poly([(0.0, 0.10), (0.07, 0.10), (0.07, 0.82), (0.0, 0.82)], scale(body, 0.82), lift=0, angle=ang, pivot=piv, alpha=0.6)
    c.poly([(-0.07, 0.10), (0.07, 0.10), (0.0, -0.03)], c.col((0.93, 0.78, 0.58)), lift=0.05, angle=ang, pivot=piv)
    c.poly([(-0.022, 0.025), (0.022, 0.025), (0.0, -0.03)], c.col((0.20, 0.20, 0.24)), lift=0, angle=ang, pivot=piv)
    c.poly([(-0.07, 0.82), (0.07, 0.82), (0.07, 0.86), (-0.07, 0.86)], c.col((0.80, 0.82, 0.86)), lift=0.1, angle=ang, pivot=piv)
    c.poly([(-0.07, 0.86), (0.07, 0.86), (0.07, 0.93), (-0.07, 0.93)], c.col((0.95, 0.55, 0.62)), lift=0.1, angle=ang, pivot=piv)


@prop("chart", aspect=1.0, place="table", nominal=0.36, category="office", words=("graph", "growth", "statistics", "stats", "kpi", "revenue", "profit", "business", "finance", "financial", "marketing", "seo", "sales", "charts", "investment", "economy"))
def chart(c, color):
    c.shadow(0.0, 0.01, 0.9, 0.06)
    accent = c.pick(color, (0.25, 0.50, 0.92))
    c.rect(0, 0.48, 0.98, 0.92, c.col((1.0, 1.0, 1.0)), r=0.04, lift=0.03)
    for k in range(4):
        c.line(-0.40, 0.2 + k * 0.17, 0.42, 0.2 + k * 0.17, 0.008, c.col((0.88, 0.9, 0.94)))
    for k, hh in enumerate((0.22, 0.34, 0.46, 0.62)):
        c.rect(-0.30 + k * 0.2, 0.14 + hh / 2, 0.13, hh, mix(accent, WHITE, 0.15 * (3 - k)), r=0.01, lift=0.12)
    c.path([(-0.30, 0.42), (-0.10, 0.54), (0.10, 0.6), (0.32, 0.82)], 0.035, c.col((1.0, 0.58, 0.14)))
    c.poly([(0.42, 0.90), (0.20, 0.83), (0.36, 0.69)], c.col((1.0, 0.58, 0.14)), lift=0)
    for u, v in ((-0.30, 0.42), (-0.10, 0.54), (0.10, 0.6)):
        c.circle(u, v, 0.035, c.col((1, 1, 1)), lift=0)
        c.circle(u, v, 0.02, c.col((1.0, 0.58, 0.14)), lift=0)


@prop("lightbulb", aspect=0.8, place="table", nominal=0.36, category="office", words=("idea", "bulb", "innovation", "ideas", "creative", "creativity", "solution", "solutions", "electricity", "electric"))
def lightbulb(c, color):
    glowc = c.pick(color, (1.0, 0.86, 0.30))
    c.glow(0, 0.68, 0.7, glowc, 0.35)
    for k in range(9):
        a = math.radians(-30 + k * 30 + 15)
        c.line(0.40 * math.cos(a), 0.68 + 0.40 * math.sin(a), 0.52 * math.cos(a), 0.68 + 0.52 * math.sin(a), 0.03, mix(glowc, WHITE, 0.2))
    c.circle(0, 0.68, 0.28, glowc, lift=0.15)
    c.poly([(-0.15, 0.52), (0.15, 0.52), (0.11, 0.34), (-0.11, 0.34)], scale(glowc, 0.92), lift=0.1)
    c.path([(-0.07, 0.40), (-0.05, 0.58), (0.0, 0.50), (0.05, 0.58), (0.07, 0.40)], 0.018, c.col((0.95, 0.55, 0.12)), smooth=False)
    for k, wd in enumerate((0.26, 0.24, 0.18)):
        c.rect(0, 0.30 - k * 0.06, wd, 0.045, c.col((0.62, 0.65, 0.72)), r=0.02, lift=0.15)
    c.ellipse(-0.1, 0.78, 0.07, 0.045, WHITE, angle=35, lift=0, alpha=0.5)
