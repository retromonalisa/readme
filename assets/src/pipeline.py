#!/usr/bin/env python3
"""Pixel-art pipeline strip for the featured project card (light + dark).

dataset -> train -> deploy on the sensor -> field test, drawn in the same
pixel style and font as the banner.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from banner import text_runs, text_width, path_d  # noqa: E402

W, H = 1040, 248
U = 6       # icon pixel size
ICON = 14   # icon grid is 14x14 cells

PALETTES = {
    "dark": dict(
        bg="#141033", border="#2c2366", bright="#ece8ff", dim="#8f86c9",
        arrow="#4b3fa0", packet="#3dffb5",
        keys=dict(p="#c4bbff", p2="#8b7fe0", s="#6a5fc0", bg="#141033", acc="#ffc978",
                  det="#3dffb5", dark="#0b0a1f", hi="#ffffff", grid="#2c2366", cloud="#6a5fc0"),
    ),
    "light": dict(
        bg="#f3f9ff", border="#c4def5", bright="#1b1446", dim="#5a6a96",
        arrow="#a9c6e8", packet="#ff2e88",
        keys=dict(p="#2f2a7a", p2="#5b6fc4", s="#8aa6d6", bg="#f3f9ff", acc="#ffb000",
                  det="#ff2e88", dark="#1c1f2e", hi="#ffffff", grid="#d3e5f7", cloud="#b9d6f2"),
    ),
}

STATIONS = [("DATASET", "83K IMAGES"), ("TRAIN", "DETECTOR"),
            ("DEPLOY", "ON-SENSOR"), ("FIELD TEST", "OUTDOORS")]


class Grid(dict):
    def fill(self, x, y, w, h, k):
        for i in range(w):
            for j in range(h):
                self[(x + i, y + j)] = k

    def outline(self, x, y, w, h, k):
        for i in range(w):
            self[(x + i, y)] = self[(x + i, y + h - 1)] = k
        for j in range(h):
            self[(x, y + j)] = self[(x + w - 1, y + j)] = k

    def bitmap(self, rows, x, y, k):
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch == "#":
                    self[(x + c, y + r)] = k


def icon_dataset():
    g = Grid()
    g.outline(4, 0, 10, 8, "s")                       # back card
    g.fill(2, 2, 10, 8, "bg"); g.outline(2, 2, 10, 8, "s")  # middle card
    g.fill(0, 5, 10, 9, "bg"); g.outline(0, 5, 10, 9, "p")  # front card
    g.fill(2, 7, 2, 2, "acc")                         # sun
    for r, (a, b) in {9: (6, 6), 10: (5, 7), 11: (4, 8), 12: (1, 8)}.items():
        for c in range(a, b + 1):
            g[(c, r)] = "p2"
    g[(2, 11)] = g[(3, 11)] = "p2"
    return g


def icon_train():
    g = Grid()
    for r in range(0, 13):
        g[(0, r)] = "s"
    for c in range(0, 14):
        g[(c, 13)] = "s"
    for c in (4, 8, 12):
        for r in (4, 8):
            g[(c, r)] = "grid"
    rows = [1, 1, 2, 3, 5, 6, 7, 8, 8, 9, 9, 10, 10]   # a loss curve, falling then flattening
    prev = None
    for i, r in enumerate(rows):
        c = i + 1
        top = r if prev is None or r - prev <= 1 else prev + 1
        for rr in range(top, r + 1):
            g[(c, rr)] = "det"
        prev = r
    return g


def icon_sensor():
    g = Grid()
    g.fill(2, 2, 10, 10, "p")
    for c in (3, 5, 8, 10):
        g[(c, 0)] = g[(c, 1)] = g[(c, 12)] = g[(c, 13)] = "s"
    for r in (3, 5, 8, 10):
        g[(0, r)] = g[(1, r)] = g[(12, r)] = g[(13, r)] = "s"
    g.fill(5, 4, 4, 6, "dark")
    g.fill(4, 5, 6, 4, "dark")
    g.fill(6, 6, 2, 2, "det")    # the "eye": inference happens right here
    g[(5, 5)] = "hi"
    g[(3, 3)] = "acc"            # pin-1 marker
    return g


def icon_field():
    g = Grid()
    g.bitmap([".###.", "#####"], 9, 0, "cloud")
    g.fill(1, 2, 5, 1, "det")                 # label tab
    g.outline(1, 3, 13, 9, "det")             # detection box
    g.bitmap(["###...###", ".#.....#.", ".#######.", "...###...", "...#.#..."], 3, 5, "p")   # drone
    for c in range(0, 14):
        g[(c, 13)] = "s"                      # ground
    return g


ICONS = [icon_dataset, icon_train, icon_sensor, icon_field]


def grid_paths(g, ox, oy, colors):
    by = {}
    for (c, r), k in sorted(g.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        by.setdefault(k, {}).setdefault(r, []).append(c)
    out = []
    for k, rows in by.items():
        rects = []
        for r, cols in rows.items():
            cols.sort()
            start = prev = cols[0]
            for c in cols[1:] + [None]:
                if c is not None and c == prev + 1:
                    prev = c
                    continue
                rects.append((ox + start * U, oy + r * U, (prev - start + 1) * U, U))
                if c is not None:
                    start = prev = c
        out.append(f'<path fill="{colors[k]}" d="{path_d(rects)}"/>')
    return out


def stepped(x0, y0, x1, y1, n=8):
    return (f"M{x0+n} {y0}H{x1-n}V{y0+4}H{x1-4}V{y0+n}H{x1}V{y1-n}H{x1-4}V{y1-4}H{x1-n}V{y1}"
            f"H{x0+n}V{y1-4}H{x0+4}V{y1-n}H{x0}V{y0+n}H{x0+4}V{y0+4}H{x0+n}Z")


def build(theme):
    P = PALETTES[theme]
    o = []
    add = o.append
    add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-labelledby="t d" shape-rendering="crispEdges">')
    add('<title id="t">seraphim-sky pipeline</title>')
    add('<desc id="d">Four pixel-art steps joined by arrows: dataset (83k images), train the '
        'detector, deploy it on the camera sensor, field test outdoors.</desc>')
    margin, gap = 145, 250
    centers = [margin + gap * i for i in range(4)]
    half = ICON * U // 2
    run = gap - 2 * (half + 16) - 36      # packet travel, ends just before the arrow head
    run -= run % (2 * U)
    add("<style>"
        f"@keyframes run{{from{{transform:translateX(0)}}to{{transform:translateX({run}px)}}}}"
        "@keyframes fade{0%,90%{opacity:1}100%{opacity:0}}"
        f".pk{{animation:run 1.6s steps({run // (2 * U)}) infinite,fade 1.6s steps(1,end) infinite}}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
        "</style>")
    add(f'<path fill="{P["border"]}" d="{stepped(0, 0, W, H)}"/>')
    add(f'<path fill="{P["bg"]}" d="{stepped(5, 5, W - 5, H - 5)}"/>')

    hu = 3
    hdr = "SERAPHIM-SKY · PIPELINE"
    add(f'<path fill="{P["dim"]}" d="{path_d(text_runs(hdr, 36, 24, hu)[0])}"/>')

    top = 62
    for i, (cx, build_icon, (l1, l2)) in enumerate(zip(centers, ICONS, STATIONS)):
        o += grid_paths(build_icon(), cx - half, top, P["keys"])
        for text, y, u, col in ((l1, top + 2 * half + 20, 4, P["bright"]),
                                (l2, top + 2 * half + 56, 3, P["dim"])):
            tw = text_width(text, u)
            add(f'<path fill="{col}" d="{path_d(text_runs(text, cx - tw // 2, y, u)[0])}"/>')
        if i < 3:  # arrow to the next station, with a moving data "packet"
            x0 = cx + half + 16
            x1 = centers[i + 1] - half - 16
            ay = top + half - U // 2
            dashes = [(x, ay, 2 * U, U) for x in range(x0, x1 - 3 * U - 2 * U, 4 * U)]
            head = [(x1 - 3 * U, ay - 2 * U, U, 5 * U), (x1 - 2 * U, ay - U, U, 3 * U), (x1 - U, ay, U, U)]
            add(f'<path fill="{P["arrow"]}" d="{path_d(dashes + head)}"/>')
            add(f'<rect class="pk" style="animation-delay:-{i * 0.5:.1f}s" x="{x0}" y="{ay - U // 2 * 1 - 3}" '
                f'width="{2 * U}" height="{2 * U}" fill="{P["packet"]}"/>')
    add("</svg>")
    return "\n".join(o) + "\n"


if __name__ == "__main__":
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    for theme in ("light", "dark"):
        p = out_dir / f"pipeline-{theme}.svg"
        svg = build(theme)
        p.write_text(svg)
        print(p, len(svg.encode()), "bytes")
