# -*- coding: utf-8 -*-
"""
トネッツモード記事用: 各コードの「そのコードの音だけ」を含む格子図をSVGで生成する。
元アプリの盤面（周辺の無関係な音も全部表示される）ではなく、記事に載せるための
自前の簡略図。格子座標の考え方は articles/puntone-tonnetz-guide.md 本文の説明
（△=maj、▽=min、斜め一直線=aug/dim、横一直線=sus4/sus2、ひし形=6th系）と
完全に一致させてある。
"""
import math
import os

SIN60 = math.sqrt(3) / 2

# 度数(半音, C=0基準) -> 格子オフセット(p, q)。本文で使っている図形と同じ対応。
# 0=root, 2=M2, 3=m3, 4=M3, 5=P4, 6=tritone(b5), 7=P5, 8=aug5, 9=M6, 10=m7, 11=M7
DEGREE_OFFSET = {
    0: (0, 0),
    2: (2, 0),
    3: (1, -1),
    4: (0, 1),
    5: (-1, 0),
    6: (2, -2),
    7: (1, 0),
    8: (0, 2),
    9: (-1, 1),
    10: (2, -1),
    11: (1, 1),
}

# 三角格子の隣接6方向（このどれかの差なら辺でつなぐ）
NEIGHBORS = {(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)}

# 各コード: (表示名, [(度数, 表示ラベル), ...])  ラベルはコードの文脈に応じた
# 正しい異名同音表記（例: dim7の第7音はB♭♭だが実用上Aと表記）。
CHORDS = [
    ("Csus2",   [(0, "C"), (2, "D"), (7, "G")]),
    ("Cdim",    [(0, "C"), (3, "E♭"), (6, "G♭")]),
    ("Cm7b5",   [(0, "C"), (3, "E♭"), (6, "G♭"), (10, "B♭")]),
    ("Cdim7",   [(0, "C"), (3, "E♭"), (6, "G♭"), (9, "A")]),
    ("Cm",      [(0, "C"), (3, "E♭"), (7, "G")]),
    ("Cm7",     [(0, "C"), (3, "E♭"), (7, "G"), (10, "B♭")]),
    ("CmM7",    [(0, "C"), (3, "E♭"), (7, "G"), (11, "B")]),
    ("Cm6",     [(0, "C"), (3, "E♭"), (7, "G"), (9, "A")]),
    ("C",        [(0, "C"), (4, "E"), (7, "G")]),
    ("C7",       [(0, "C"), (4, "E"), (7, "G"), (10, "B♭")]),
    ("CMaj7",    [(0, "C"), (4, "E"), (7, "G"), (11, "B")]),
    ("C6",       [(0, "C"), (4, "E"), (7, "G"), (9, "A")]),
    ("Caug",     [(0, "C"), (4, "E"), (8, "G♯")]),
    ("C7s5",     [(0, "C"), (4, "E"), (8, "G♯"), (10, "B♭")]),
    ("CMaj7s5",  [(0, "C"), (4, "E"), (8, "G♯"), (11, "B")]),
    ("Csus4",    [(0, "C"), (5, "F"), (7, "G")]),
    ("C7sus4",   [(0, "C"), (5, "F"), (7, "G"), (10, "B♭")]),
    ("CMaj7sus4", [(0, "C"), (5, "F"), (7, "G"), (11, "B")]),
]

SCALE = 78
RADIUS = 26
MARGIN = 40
BG = "#14161d"
NODE_FILL = "#e8c17d"
NODE_STROKE = "#a9793a"
ROOT_STROKE = "#4dabf7"
EDGE_COLOR = "#e8c17d"
TEXT_COLOR = "#241708"


def lattice_xy(p, q):
    return (p + q * 0.5, -q * SIN60)


def build_svg(name, degrees):
    pts = []
    for deg, label in degrees:
        p, q = DEGREE_OFFSET[deg]
        x, y = lattice_xy(p, q)
        pts.append({"p": p, "q": q, "x": x * SCALE, "y": y * SCALE, "label": label, "deg": deg})

    xs = [pt["x"] for pt in pts]
    ys = [pt["y"] for pt in pts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = (max_x - min_x) + MARGIN * 2
    height = (max_y - min_y) + MARGIN * 2
    off_x = MARGIN - min_x
    off_y = MARGIN - min_y
    for pt in pts:
        pt["cx"] = pt["x"] + off_x
        pt["cy"] = pt["y"] + off_y

    edges = []
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            dp = pts[i]["p"] - pts[j]["p"]
            dq = pts[i]["q"] - pts[j]["q"]
            if (dp, dq) in NEIGHBORS:
                edges.append((pts[i], pts[j]))

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {width:.1f} {height:.1f}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="\'Hiragino Sans\', \'Yu Gothic\', sans-serif">'
    )
    parts.append(f'<rect x="0" y="0" width="{width:.1f}" height="{height:.1f}" rx="12" fill="{BG}"/>')

    for a, b in edges:
        parts.append(
            f'<line x1="{a["cx"]:.1f}" y1="{a["cy"]:.1f}" x2="{b["cx"]:.1f}" y2="{b["cy"]:.1f}" '
            f'stroke="{EDGE_COLOR}" stroke-width="3" stroke-opacity="0.55" stroke-linecap="round"/>'
        )

    for pt in pts:
        is_root = pt["deg"] == 0
        stroke = ROOT_STROKE if is_root else NODE_STROKE
        stroke_w = 4 if is_root else 2
        parts.append(
            f'<circle cx="{pt["cx"]:.1f}" cy="{pt["cy"]:.1f}" r="{RADIUS}" '
            f'fill="{NODE_FILL}" stroke="{stroke}" stroke-width="{stroke_w}"/>'
        )
        parts.append(
            f'<text x="{pt["cx"]:.1f}" y="{pt["cy"]:.1f}" text-anchor="middle" '
            f'dominant-baseline="central" font-size="22" font-weight="700" '
            f'fill="{TEXT_COLOR}">{pt["label"]}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "images", "puntone-tonnetz-guide")
    out_dir = os.path.normpath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    for name, degrees in CHORDS:
        svg = build_svg(name, degrees)
        out_path = os.path.join(out_dir, f"chord-{name}.svg")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote", out_path)


if __name__ == "__main__":
    main()
