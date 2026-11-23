#!/usr/bin/env python3
"""Procedural news poster for make.fun competition news-image-20261123.

Draws a one-page poster summing up the world news of Monday 23 November
2026 as a single 1024x1024 PNG, rendered entirely in code with the Python
standard library (a minimal PNG encoder + shape primitives + a 5x7 bitmap
font defined below). No network, no external files, fully deterministic:
two runs produce byte-identical output.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import struct
import zlib

W = H = 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 231)      # warm off-white page
CARD = (255, 255, 255)       # panel cards
CARD_EDGE = (216, 209, 194)  # card border
NAVY = (20, 33, 61)          # header / footer band, headlines
NAVY_SOFT = (43, 62, 102)
GOLD = (232, 196, 104)       # header subtitle / rules
INK = (32, 30, 26)           # body text
GREY = (74, 70, 62)          # caption text
TICKER_BG = (237, 230, 214)  # ticker strip
RED = (176, 58, 46)
TEAL = (42, 127, 98)
ORANGE = (192, 86, 33)
BLUE = (43, 94, 167)
CRIMSON = (169, 50, 38)
INDIGO = (91, 74, 138)
SKY = (127, 184, 217)
LIGHT_GREY = (200, 198, 190)

# ------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 pixels ('#' on, '.' off).
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01110"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "11001", "10101", "10011", "10011", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00010", "00100", "00100", "00100"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "01100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "01100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00001", "00010", "00100", "01000", "10000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10010", "01000", "10101", "10010", "01101"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "01110", "00000", "01110", "00000", "00000"),
    "*": ("00000", "01010", "00100", "01110", "00100", "01010", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "\u2022": ("00000", "00000", "01110", "01110", "01110", "00000", "00000"),
}

# ------------------------------------------------------------ canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        r, g, b = c
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = r, g, b

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            if t == 1:
                self.set(x0, y0, c)
            else:
                self.fill_rect(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, c)

    def ring(self, cx, cy, r, c, t=3):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            dx2 = int(max(0, (r - t) * (r - t) - dy * dy) ** 0.5) if abs(dy) < r - t else 0
            self.fill_rect(cx - dx, cy + dy, dx - dx2 + 1, 1, c)
            self.fill_rect(cx + dx2, cy + dy, dx - dx2 + 1, 1, c)

    def polygon(self, pts, c):
        # scanline fill for a simple polygon
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[i]), y, int(xs[i + 1]) - int(xs[i]) + 1, 1, c)

    def triangle(self, x0, y0, x1, y1, x2, y2, c):
        self.polygon([(x0, y0), (x1, y1), (x2, y2)], c)


# ------------------------------------------------------------ text
def clean(text):
    return (text.replace("\u2019", "'").replace("\u2018", "'")
                .replace("\u201c", '"').replace("\u201d", '"')
                .replace("\u2014", "-").replace("\u2013", "-")
                .upper())


def text_width(text, scale):
    return len(text) * 6 * scale - scale if text else 0


def draw_text(cv, x, y, text, scale, color, align="left"):
    text = clean(text)
    if align == "center":
        x -= text_width(text, scale) // 2
    elif align == "right":
        x -= text_width(text, scale)
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT["?"])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    cv.fill_rect(cx + col * scale, y + row * scale,
                                 scale, scale, color)
        cx += 6 * scale
    return cx


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns a list of lines fitting max_width."""
    text = clean(text)
    max_chars = max(1, max_width // (6 * scale))
    lines = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for wd in words:
            trial = wd if not cur else cur + " " + wd
            if len(trial) <= max_chars:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                while len(wd) > max_chars:
                    lines.append(wd[:max_chars])
                    wd = wd[max_chars:]
                cur = wd
        if cur:
            lines.append(cur)
    return lines


# ------------------------------------------------------------ pictograms
def icon_globe(cv, cx, cy, s, accent):
    r = s // 2
    cv.circle(cx, cy, r, SKY)
    cv.ring(cx, cy, r, NAVY, 3)
    cv.line(cx - r + 6, cy - r // 3, cx + r - 6, cy - r // 3, CARD, 3)
    cv.line(cx - r + 4, cy + r // 3, cx + r - 4, cy + r // 3, CARD, 3)
    cv.circle(cx - r // 3, cy - r // 6, r // 5, (58, 143, 84))
    cv.circle(cx + r // 4, cy + r // 4, r // 6, (58, 143, 84))
    cv.line(cx - r + 8, cy - r + 4, cx + r - 6, cy + r - 8, CRIMSON, 4)


def icon_ship(cv, cx, cy, s, accent):
    # hull
    cv.polygon([(cx - s // 2, cy + s // 6), (cx + s // 2, cy + s // 6),
                (cx + s // 2 - 8, cy + s // 3), (cx - s // 2 + 8, cy + s // 3)],
               NAVY)
    # containers
    cv.fill_rect(cx - s // 3, cy - s // 6, s // 5, s // 3, RED)
    cv.fill_rect(cx - s // 3 + s // 5 + 3, cy - s // 6, s // 5, s // 3, GOLD)
    cv.fill_rect(cx - s // 3 + 2 * (s // 5 + 3), cy - s // 6, s // 5, s // 3, TEAL)
    # mast + burst
    cv.line(cx + s // 4, cy - s // 6, cx + s // 4, cy - s // 2, NAVY, 3)
    bx, by = cx + s // 4, cy - s // 2 - 6
    cv.line(bx - 10, by, bx + 10, by, ORANGE, 3)
    cv.line(bx, by - 10, bx, by + 10, ORANGE, 3)
    cv.line(bx - 7, by - 7, bx + 7, by + 7, ORANGE, 3)
    cv.line(bx - 7, by + 7, bx + 7, by - 7, ORANGE, 3)
    # waves
    for k, wy in enumerate((cy + s // 3 + 8, cy + s // 3 + 18)):
        for x in range(cx - s // 2, cx + s // 2, 16):
            cv.line(x, wy + (4 if k else 0), x + 8, wy - (4 if k else 0), BLUE, 3)


def icon_building(cv, cx, cy, s, accent):
    bw, bh = int(s * 0.62), int(s * 0.72)
    x0, y0 = cx - bw // 2, cy - bh // 2
    cv.fill_rect(x0, y0, bw, bh, (120, 138, 163))
    cv.rect(x0, y0, bw, bh, NAVY, 3)
    for r in range(4):
        for c in range(3):
            wx = x0 + 8 + c * (bw - 16) // 3
            wy = y0 + 10 + r * (bh - 20) // 4
            cv.fill_rect(wx, wy, (bw - 16) // 3 - 6, (bh - 20) // 4 - 6, GOLD)
    # crack
    cv.line(cx + 4, y0, cx - 6, y0 + bh // 3, CRIMSON, 3)
    cv.line(cx - 6, y0 + bh // 3, cx + 8, y0 + 2 * bh // 3, CRIMSON, 3)
    cv.line(cx + 8, y0 + 2 * bh // 3, cx - 2, y0 + bh, CRIMSON, 3)
    # smoke
    cv.circle(cx - s // 4, y0 - 12, 9, LIGHT_GREY)
    cv.circle(cx + s // 6, y0 - 20, 12, LIGHT_GREY)


def icon_truck(cv, cx, cy, s, accent):
    bw, bh = int(s * 0.58), int(s * 0.42)
    x0, y0 = cx - s // 2, cy - bh // 2
    cv.fill_rect(x0, y0, bw, bh, CARD)
    cv.rect(x0, y0, bw, bh, NAVY, 3)
    cv.line(x0 + 4, y0 + 4, x0 + bw - 4, y0 + 4, RED, 3)
    cv.line(x0 + 4, y0 + bh - 4, x0 + bw - 4, y0 + bh - 4, RED, 3)
    # cab
    cv.polygon([(x0 + bw, y0 + 6), (x0 + bw + s // 4, y0 + 6),
                (x0 + bw + s // 4, y0 + bh), (x0 + bw, y0 + bh)], BLUE)
    cv.fill_rect(x0 + bw + 4, y0 + 10, s // 6, bh // 3, SKY)
    # wheels
    for wx in (x0 + bw // 4, x0 + bw - 6, x0 + bw + s // 6):
        cv.circle(wx, y0 + bh + 8, 9, INK)
        cv.circle(wx, y0 + bh + 8, 3, CARD)
    # burst above cargo
    bx, by = x0 + bw // 2, y0 - 14
    cv.line(bx - 8, by, bx + 8, by, ORANGE, 3)
    cv.line(bx, by - 8, bx, by + 8, ORANGE, 3)


def icon_chart(cv, cx, cy, s, accent):
    x0, y0 = cx - s // 2, cy - s // 2
    # axes
    cv.line(x0, y0 + s - 8, x0 + s, y0 + s - 8, NAVY, 3)
    cv.line(x0, y0, x0, y0 + s - 8, NAVY, 3)
    # declining line
    pts = [(x0 + 6, y0 + 10), (x0 + s // 3, y0 + s // 3),
           (x0 + 2 * s // 3, y0 + s // 2 + 4), (x0 + s - 12, y0 + s - 18)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], RED, 4)
    for p in pts:
        cv.circle(p[0], p[1], 4, RED)
    # arrow head at the end
    ex, ey = pts[-1]
    cv.triangle(ex - 2, ey - 12, ex + 12, ey - 2, ex - 12, ey + 2, RED)


def icon_cuffs(cv, cx, cy, s, accent):
    r = s // 5
    cv.ring(cx - r - 4, cy + 8, r, NAVY, 6)
    cv.ring(cx + r + 4, cy + 8, r, NAVY, 6)
    cv.fill_rect(cx - r - 4, cy - r - 2, 2 * r + 8, 8, NAVY)
    cv.circle(cx - r - 4, cy + 8, 4, GOLD)
    cv.circle(cx + r + 4, cy + 8, 4, GOLD)
    # small chain links above the bar
    cv.ring(cx, cy - r - 8, 7, GOLD, 3)


ICONS = {
    "globe": icon_globe,
    "ship": icon_ship,
    "building": icon_building,
    "truck": icon_truck,
    "chart": icon_chart,
    "cuffs": icon_cuffs,
}

# ------------------------------------------------------------ content
PANELS = [
    ("CLIMATE", "Climate talks collapse",
     "COP31 in Antalya ends with no deal, the longest talks on record.",
     TEAL, "globe"),
    ("MIDDLE EAST", "Tankers hit in Strait of Hormuz",
     "Iran widens strikes; a Bahrain industrial site is hit, two hurt.",
     ORANGE, "ship"),
    ("UKRAINE", "Deadly strike near Kyiv",
     "A Russian strike hits an apartment block in Dymer, near Kyiv.",
     BLUE, "building"),
    ("GAZA", "Three killed in Gaza truck strike",
     "World Central Kitchen: the truck was not theirs; three are killed.",
     CRIMSON, "truck"),
    ("MARKETS", "Asian chip stocks slide",
     "South Korea's Kospi falls 3.3% as AI doubts roil Wall Street.",
     RED, "chart"),
    ("AMERICAS", "Cartel leader captured",
     "Mexico captures Sinaloa cartel's 'Chapo Isidro', the Justice Dept. "
     "says.",
     INDIGO, "cuffs"),
]

TICKER = ("KYIV: SEA DRONES HIT RUSSIAN SHIPS IN BENGHAZI \u2022 "
          "UN CHIEF URGES GLOBAL AI RULES")


# ------------------------------------------------------------ layout
def draw_panel(cv, x, y, w, h, kicker, headline, caption, accent, icon):
    cv.fill_rect(x, y, w, h, CARD)
    cv.rect(x, y, w, h, CARD_EDGE, 2)
    cv.fill_rect(x, y, 8, h, accent)          # left accent bar
    # pictogram, left column
    ix0, iw = x + 16, 100
    icx = ix0 + iw // 2
    icy = y + h // 2
    ICONS[icon](cv, icx, icy, 88, accent)
    # text, right column
    tx = x + 128
    tw = x + w - 16 - tx
    draw_text(cv, tx, y + 12, kicker, 3, accent)
    hl = wrap_text(headline, tw, 4)
    hy = y + 40
    for line in hl:
        draw_text(cv, tx, hy, line, 4, NAVY)
        hy += 30
    cap = wrap_text(caption, tw, 3)
    cy = hy + 8
    for line in cap:
        draw_text(cv, tx, cy, line, 3, GREY)
        cy += 23


def draw_poster():
    cv = Canvas(W, H, PAPER)
    # header band
    cv.fill_rect(0, 0, W, 132, NAVY)
    draw_text(cv, W // 2, 22, "23 NOVEMBER 2026", 9, CARD, align="center")
    cv.fill_rect(W // 2 - 180, 90, 360, 3, GOLD)
    draw_text(cv, W // 2, 98, "THE WORLD IN ONE DAY", 4, GOLD, align="center")
    # panels: 2 columns x 3 rows
    px, py, pw, ph, gap = 24, 148, 480, 234, 16
    for i, (kicker, headline, caption, accent, icon) in enumerate(PANELS):
        col, row = i % 2, i // 2
        draw_panel(cv, px + col * (pw + gap), py + row * (ph + gap),
                   pw, ph, kicker, headline, caption, accent, icon)
    # ticker strip
    ty = 894
    cv.fill_rect(0, ty, W, 36, TICKER_BG)
    cv.fill_rect(0, ty, W, 2, GOLD)
    cv.fill_rect(0, ty + 34, W, 2, GOLD)
    draw_text(cv, W // 2, ty + 11, TICKER, 2, NAVY, align="center")
    # footer band
    fy = 942
    cv.fill_rect(0, fy, W, H - fy, NAVY)
    draw_text(cv, W // 2, fy + 16, "EVENTS REPORTED ON 23 NOVEMBER 2026",
              3, CARD, align="center")
    draw_text(cv, W // 2, fy + 48, "DRAWN ENTIRELY IN CODE - PYTHON STANDARD LIBRARY ONLY",
              2, GOLD, align="center")
    return cv


# ------------------------------------------------------------ PNG encoder
def png_bytes(cv):
    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: None
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(draw_poster())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
