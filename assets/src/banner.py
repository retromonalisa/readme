#!/usr/bin/env python3
"""Generate the pixel-art profile banners (light + dark) as self-contained SVGs.

Everything is drawn from rectangles on a pixel grid, including the text (a tiny
5x7 bitmap font below), so the art renders identically everywhere and needs no
web fonts or external requests -- GitHub serves README images in a sandbox.
"""
import math
import random
import sys
from pathlib import Path

W, H = 1280, 360
U = 5  # scene pixel size

# --- 5x7 bitmap font (variable width) -------------------------------------
FONT = {
    # lowercase
    "a": [".....", ".....", ".###.", "....#", ".####", "#...#", ".####"],
    "d": ["....#", "....#", ".##.#", "#..##", "#...#", "#...#", ".####"],
    "e": [".....", ".....", ".###.", "#...#", "#####", "#....", ".###."],
    "i": ["..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."],
    "l": [".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "m": [".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"],
    "n": [".....", ".....", "#.##.", "##..#", "#...#", "#...#", "#...#"],
    "o": [".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."],
    "r": [".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."],
    "s": [".....", ".....", ".###.", "#....", ".###.", "....#", "####."],
    "t": [".#...", ".#...", "###..", ".#...", ".#...", ".#..#", "..##."],
    # uppercase
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    # digits / punctuation
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
    ".": ["..", "..", "..", "..", "..", "##", "##"],
    "-": ["....", "....", "....", "####", "....", "....", "...."],
    "·": ["..", "..", "..", "##", "##", "..", ".."],
}
SPACE = 3  # columns


def text_runs(s, x, y, u, tracking=1):
    """Return ([(x, y, w, h, row)], width) for string s drawn at (x, y)."""
    runs, cx = [], x
    for i, ch in enumerate(s):
        if ch == " ":
            cx += SPACE * u
            continue
        g = FONT[ch]
        gw = len(g[0])
        for r, row in enumerate(g):
            c = 0
            while c < gw:
                if row[c] != "#":
                    c += 1
                    continue
                start = c
                while c < gw and row[c] == "#":
                    c += 1
                runs.append((cx + start * u, y + r * u, (c - start) * u, u, r))
        cx += gw * u + (tracking * u if i < len(s) - 1 else 0)
    return runs, cx - x


def text_width(s, u, tracking=1):
    return text_runs(s, 0, 0, u, tracking)[1]


def path_d(rects):
    return "".join(f"M{x} {y}h{w}v{h}h-{w}z" for x, y, w, h, *_ in rects)


def sprite(rows, x, y, u):
    """Bitmap rows (one char per cell, '.' = empty) -> {char: [rects]}."""
    out = {}
    for r, row in enumerate(rows):
        c = 0
        while c < len(row):
            ch = row[c]
            if ch == ".":
                c += 1
                continue
            start = c
            while c < len(row) and row[c] == ch:
                c += 1
            out.setdefault(ch, []).append((x + start * u, y + r * u, (c - start) * u, u))
    return out


# --- art ------------------------------------------------------------------
DRONE = [
    ".RRRRRRRR..........RRRRRRRR.",
    "....MM................MM....",
    "...MMMM..............MMMM...",
    "....AAAAAAAAAAAAAAAAAAAA....",
    ".........HHHHHHHHHH.........",
    "........BBBBBLBBBBBB........",
    ".........BBBBBBBBBB.........",
    ".........A..GGGG..A.........",
    "........AA..GCCG..AA........",
]
ROTOR_B = [  # second rotor frame: short blur, alternates with row 0 above
    "...QQQQ..............QQQQ...",
]

CLOUDS = {
    "big": [
        "......####..........",
        "....########..###...",
        "...###############..",
        ".##################.",
        "####################",
        ".SSSSSSSSSSSSSSSSSS.",
    ],
    "mid": [
        "....###.....",
        "..#######...",
        ".##########.",
        "############",
        ".SSSSSSSSSS.",
    ],
    "small": [
        "..###...",
        ".######.",
        "########",
        ".SSSSSS.",
    ],
}

TREE = [
    "..#..",
    ".###.",
    ".###.",
    "#####",
    ".###.",
    "#####",
    "..#..",
]

PALETTES = {
    "dark": dict(
        bands=["#0b0a1f", "#100e2c", "#17123d", "#211650", "#2f1a60", "#43206b", "#5c2672"],
        stars=["#ffffff", "#fff1c1", "#c9c3ff"],
        cloud="#2a2160", cloud_shade="#211a50", cloud_op=0.9,
        hill_back="#1b1338", hill_front="#0d0821", tree="#0d0821",
        title_rows=["#fff6c2", "#ffe39a", "#ffc978", "#ffa76f", "#ff8577", "#ff6994", "#f055b6"],
        title_shadow="#07051a", title_shadow_op=1,
        subtitle="#c4bbff",
        hud="#ffffff", hud_op=0.72,
        rec="#ff4d6d",
        box="#3dffb5", label_fg="#08261b",
        drone=dict(R="#ffffff", Q="#ffffff", M="#8d87bd", A="#c2bde8", B="#eceaff",
                   H="#ffffff", L="#ff4d6d", G="#6f689c", C="#12102b"),
        rotor_op=0.55,
        scan="#000000", scan_op=0.10,
        vignette="#000000", vignette_op=0.45,
        orb="moon",
    ),
    "light": dict(
        bands=["#4fb0f2", "#62bbf5", "#77c6f8", "#8dd1fa", "#a6dcfc", "#c0e8fd", "#dcf3ff"],
        stars=None,
        cloud="#ffffff", cloud_shade="#cfe7fa", cloud_op=1,
        hill_back="#86c79f", hill_front="#4e9b6f", tree="#2f7550",
        title_rows=["#1b1446", "#221a5a", "#2b1f6e", "#352381", "#432591", "#53269e", "#6527a8"],
        title_shadow="#ffffff", title_shadow_op=0.85,
        subtitle="#1d3566",
        hud="#0f1d3d", hud_op=0.7,
        rec="#ff2d55",
        box="#ff2e88", label_fg="#ffffff",
        drone=dict(R="#1c1f2e", Q="#1c1f2e", M="#1c1f2e", A="#3a3f58", B="#2b2f45",
                   H="#555c7d", L="#ff2d55", G="#555b78", C="#0b0d16"),
        rotor_op=0.45,
        scan="#0a2a4a", scan_op=0.04,
        vignette="#0a2a4a", vignette_op=0.10,
        orb="sun",
    ),
}

TITLE = "retromonalisa"
SUBTITLE = "TEACHING CAMERAS TO WATCH THE SKY"
LABEL = "drone 0.73"


def band_layout():
    # boundaries sit at y % 10 == 5 so the 10px checker pattern lines up
    return [55, 115, 165, 205, 245, 275]


def hill_columns(base, waves, u=U):
    cols = W // u
    hs = []
    for i in range(cols):
        h = base + sum(a * math.sin(i * f + p) for a, f, p in waves)
        hs.append(max(1, round(h)))
    return hs


def hill_path(hs, u=U):
    d = f"M0 {H}"
    prev = None
    for i, h in enumerate(hs):
        y = H - h * u
        x = i * u
        if prev is None:
            d += f"V{y}"
        elif y != prev:
            d += f"H{x}V{y}"
        prev = y
    d += f"H{W}V{H}Z"
    return d


def orb_cells(kind):
    cells = {}
    if kind == "moon":
        r = 4.6
        for yy in range(-5, 6):
            for xx in range(-5, 6):
                inside = xx * xx + yy * yy <= r * r
                bite = (xx - 2.6) ** 2 + (yy + 1.4) ** 2 <= (r - 0.6) ** 2
                if inside and not bite:
                    cells[(xx, yy)] = "#fff1c1"
    else:
        r = 4.2
        for yy in range(-5, 6):
            for xx in range(-5, 6):
                if xx * xx + yy * yy <= r * r:
                    cells[(xx, yy)] = "#ffd84d"
        for xx, yy in [(0, -7), (0, 7), (-7, 0), (7, 0), (-5, -5), (5, -5), (-5, 5), (5, 5)]:
            cells[(xx, yy)] = "#ffe680"
    return cells


def build(theme):
    P = PALETTES[theme]
    rnd = random.Random(7)  # deterministic art
    o = []
    add = o.append

    add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-labelledby="t d" shape-rendering="crispEdges">')
    add('<title id="t">retromonalisa</title>')
    add('<desc id="d">Pixel-art camera view of a '
        + ("night" if theme == "dark" else "daytime")
        + ' sky. The name retromonalisa sits above the line "teaching cameras to watch the sky", '
        'and a small quadcopter on the right is boxed and labelled "drone 0.73", like an '
        'on-sensor detection overlay.</desc>')

    # ---- defs
    add("<defs>")
    n = 8
    clip = (f"M{n} 0H{W-n}V4H{W-4}V{n}H{W}V{H-n}H{W-4}V{H-4}H{W-n}V{H}H{n}V{H-4}H4V{H-n}H0V{n}H4V4H{n}Z")
    add(f'<clipPath id="frame"><path d="{clip}"/></clipPath>')
    bands = P["bands"]
    for k, c in enumerate(bands[1:], start=1):
        add(f'<pattern id="dz{k}" width="10" height="10" patternUnits="userSpaceOnUse">'
            f'<rect width="5" height="5" fill="{c}"/><rect x="5" y="5" width="5" height="5" fill="{c}"/></pattern>')
    add(f'<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
        f'<rect width="4" height="2" fill="{P["scan"]}" fill-opacity="{P["scan_op"]}"/></pattern>')
    add(f'<radialGradient id="vig" cx="50%" cy="45%" r="75%">'
        f'<stop offset="60%" stop-color="{P["vignette"]}" stop-opacity="0"/>'
        f'<stop offset="100%" stop-color="{P["vignette"]}" stop-opacity="{P["vignette_op"]}"/></radialGradient>')
    add("</defs>")

    # ---- motion (steps() keeps it chunky / retro); respects reduced-motion
    add("<style>"
        "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}"
        "@keyframes sway{0%,100%{transform:translateX(0)}50%{transform:translateX(-40px)}}"
        "@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}"
        "@keyframes blinkb{0%,100%{opacity:0}50%{opacity:1}}"
        "@keyframes tw{0%,100%{opacity:1}50%{opacity:.25}}"
        "@keyframes drift{from{transform:translateX(0)}to{transform:translateX(60px)}}"
        ".sway{animation:sway 9s steps(16) infinite}"
        ".bob{animation:bob 1.4s steps(1,end) infinite}"
        ".ra{animation:blink .18s steps(1,end) infinite}"
        ".rb{animation:blinkb .18s steps(1,end) infinite}"
        ".led{animation:blink 1.2s steps(1,end) infinite}"
        ".rec{animation:blink 1.6s steps(1,end) infinite}"
        ".tw{animation:tw 2.4s steps(1,end) infinite}"
        ".c1{animation:drift 28s steps(12) infinite alternate}"
        ".c2{animation:drift 36s steps(12) infinite alternate-reverse}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
        "</style>")

    add('<g clip-path="url(#frame)">')

    # ---- sky: posterised bands with a 2-row checker dither at each seam
    bs = band_layout()
    edges = [0] + [b + 5 for b in bs] + [H]
    for k, c in enumerate(bands):
        add(f'<rect y="{edges[k]}" width="{W}" height="{edges[k+1]-edges[k]}" fill="{c}"/>')
    for k, b in enumerate(bs, start=1):
        add(f'<rect y="{b-5}" width="{W}" height="10" fill="url(#dz{k})"/>')

    # ---- stars (night only)
    title_box = (60, 84, 900, 238)  # keep the text rows clear
    keep_clear = [(900, 60, 1180, 200),   # drone + label
                  (24, 20, 200, 72),      # REC
                  (990, 20, 1262, 72),    # project tag
                  (760, 18, 840, 84)]     # moon
    if P["stars"]:
        stars = []
        while len(stars) < 70:
            x = rnd.randrange(2, W // U - 2) * U
            y = rnd.randrange(2, 52) * U
            inb = lambda bx: bx[0] <= x <= bx[2] and bx[1] <= y <= bx[3]
            if any(inb(b) for b in keep_clear) or inb(title_box):
                continue
            stars.append((x, y))
        for i, (x, y) in enumerate(stars):
            c = P["stars"][i % len(P["stars"])]
            op = 0.35 + 0.65 * rnd.random()
            cls = ' class="tw"' if i % 4 == 0 else ""
            delay = f' style="animation-delay:-{rnd.random()*2.4:.2f}s"' if cls else ""
            if i % 11 == 0:  # a few brighter "plus" stars
                add(f'<path{cls}{delay} fill="{c}" d="M{x} {y-U}h{U}v{3*U}h-{U}zM{x-U} {y}h{3*U}v{U}h-{3*U}z"/>')
            else:
                add(f'<rect{cls}{delay} x="{x}" y="{y}" width="{U}" height="{U}" fill="{c}" fill-opacity="{op:.2f}"/>')

    # ---- moon / sun
    ox, oy = 800, 50
    for (xx, yy), c in orb_cells(P["orb"]).items():
        add(f'<rect x="{ox+xx*U}" y="{oy+yy*U}" width="{U}" height="{U}" fill="{c}"/>')

    # ---- clouds (two drifting layers)
    placements = [("big", 210, 44, "c1"), ("small", 560, 70, "c2"), ("mid", 1000, 215, "c1"),
                  ("small", 30, 230, "c2"), ("mid", 620, 240, "c1")]
    for name, x, y, cls in placements:
        rects = sprite(CLOUDS[name], x, y, U)
        add(f'<g class="{cls}" fill-opacity="{P["cloud_op"]}">')
        if "#" in rects:
            add(f'<path fill="{P["cloud"]}" d="{path_d(rects["#"])}"/>')
        if "S" in rects:
            add(f'<path fill="{P["cloud_shade"]}" d="{path_d(rects["S"])}"/>')
        add("</g>")

    # ---- hills + trees
    back = hill_columns(15, [(2.2, 0.045, 0.3), (1.4, 0.11, 1.7), (0.8, 0.23, 0.2)])
    front = hill_columns(8.5, [(1.8, 0.03, 2.1), (1.2, 0.09, 0.4), (0.6, 0.19, 1.1)])
    add(f'<path fill="{P["hill_back"]}" d="{hill_path(back)}"/>')
    tree_cols = [14, 31, 37, 88, 120, 127, 176, 205, 212, 240]
    trects = []
    for col in tree_cols:
        top = H - back[col] * U - len(TREE) * U + U
        trects += sprite(TREE, (col - 2) * U, top, U)["#"]
    add(f'<path fill="{P["hill_back"]}" d="{path_d(trects)}"/>')
    add(f'<path fill="{P["hill_front"]}" d="{hill_path(front)}"/>')

    # ---- title: per-row colour bands give the retro "chrome" look
    tx, ty, tu = 80, 98, 10
    runs, tw = text_runs(TITLE, tx, ty, tu)
    shadow = [(x + U, y + U, w, h) for x, y, w, h, _ in runs]
    add(f'<path fill="{P["title_shadow"]}" fill-opacity="{P["title_shadow_op"]}" d="{path_d(shadow)}"/>')
    for r, c in enumerate(P["title_rows"]):
        rr = [q for q in runs if q[4] == r]
        if rr:
            add(f'<path fill="{c}" d="{path_d(rr)}"/>')

    # ---- subtitle, left-aligned under the title
    su = 4
    sruns, sw = text_runs(SUBTITLE, tx, ty + 7 * tu + 30, su)
    add(f'<path fill="{P["subtitle"]}" d="{path_d(sruns)}"/>')

    # ---- drone + detection overlay
    dx, dy, du = 1000, 128, U
    pad = 3 * U
    sw_ = len(DRONE[0]) * du
    sh_ = len(DRONE) * du
    bx0, by0 = dx - pad, dy - pad
    bw, bh = sw_ + 2 * pad, sh_ + 2 * pad
    lu = 3
    lw = text_width(LABEL, lu)
    tab_w, tab_h = lw + 2 * 5, 7 * lu + 2 * 4
    add('<g class="sway"><g class="bob">')
    parts = sprite(DRONE, dx, dy, du)
    rotor_b = sprite(ROTOR_B, dx, dy, du)
    for ch, rects in parts.items():
        if ch == "R":
            add(f'<path class="ra" fill="{P["drone"]["R"]}" fill-opacity="{P["rotor_op"]}" d="{path_d(rects)}"/>')
        elif ch == "L":
            add(f'<path class="led" fill="{P["drone"]["L"]}" d="{path_d(rects)}"/>')
        else:
            add(f'<path fill="{P["drone"][ch]}" d="{path_d(rects)}"/>')
    add(f'<path class="rb" fill="{P["drone"]["Q"]}" fill-opacity="{min(1, P["rotor_op"] + 0.3):.2f}" '
        f'd="{path_d(rotor_b["Q"])}"/>')
    # box (four bars keep the edges crisp)
    t = 4
    box = [(bx0, by0, bw, t), (bx0, by0 + bh - t, bw, t), (bx0, by0, t, bh), (bx0 + bw - t, by0, t, bh)]
    add(f'<path fill="{P["box"]}" d="{path_d(box)}"/>')
    add(f'<rect x="{bx0}" y="{by0 - tab_h}" width="{tab_w}" height="{tab_h}" fill="{P["box"]}"/>')
    lruns, _ = text_runs(LABEL, bx0 + 5, by0 - tab_h + 4, lu)
    add(f'<path fill="{P["label_fg"]}" d="{path_d(lruns)}"/>')
    add("</g></g>")

    # ---- HUD: viewfinder corners, REC, project tag
    hc, hl, ht, inset = P["hud"], 40, U, 18
    corners = []
    for (cx, cy, sx, sy) in [(inset, inset, 1, 1), (W - inset, inset, -1, 1),
                             (inset, H - inset, 1, -1), (W - inset, H - inset, -1, -1)]:
        x0 = cx if sx > 0 else cx - hl
        y0 = cy if sy > 0 else cy - ht
        corners.append((x0, y0, hl, ht))
        x1 = cx if sx > 0 else cx - ht
        y1 = cy if sy > 0 else cy - hl
        corners.append((x1, y1, ht, hl))
    add(f'<g fill="{hc}" fill-opacity="{P["hud_op"]}">')
    add(f'<path d="{path_d(corners)}"/>')
    hu = 3
    rec_runs, rw = text_runs("REC", 66, 36, hu)
    add(f'<path d="{path_d(rec_runs)}"/>')
    tag = "SERAPHIM-SKY"
    tag_w = text_width(tag, hu)
    tag_runs, _ = text_runs(tag, W - 44 - tag_w, 36, hu)
    add(f'<path d="{path_d(tag_runs)}"/>')
    add("</g>")
    add(f'<path class="rec" fill="{P["rec"]}" d="M48 39h9v3h3v9h-3v3h-9v-3h-3v-9h3z"/>')

    # ---- CRT finish
    add(f'<rect width="{W}" height="{H}" fill="url(#scan)"/>')
    add(f'<rect width="{W}" height="{H}" fill="url(#vig)"/>')
    add("</g></svg>")
    return "\n".join(o) + "\n", dict(title_w=tw, subtitle_w=sw, label_w=lw)


if __name__ == "__main__":
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    for theme in ("light", "dark"):
        svg, info = build(theme)
        p = out_dir / f"banner-{theme}.svg"
        p.write_text(svg)
        print(p, len(svg.encode()), "bytes", info)
