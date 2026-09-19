# -*- coding: utf-8 -*-
"""
黄金トネッツ（Golden Tonnetz）記事用の図をSVGで生成する。

格子の定義は theremin/src/core/golden-tonnetz-grid.js をPythonへそのまま
移植したもの（正五角形＋対角線が作る五芒星を行×列に並べた周期格子。
1セル9ノード、行=半音下、列=全音上）。色・線もtheremin/styles.cssの
.golden-tonnetz-mode配下の式をそのまま使い、アプリ実機と同じ見た目にする。
"""
import colorsys
import math
import os

COS36 = math.cos(math.radians(36))
COS72 = math.cos(math.radians(72))
SIN36 = math.sin(math.radians(36))
SIN72 = math.sin(math.radians(72))

CELL_W = 1.0
CELL_H = 2 * SIN72

NODE_X = [0, 0.5, 1 - COS36, COS36, COS72, 1 - COS72, 1 - COS36, COS36, 0.5]
NODE_Y = [
    0, SIN72 - SIN36, SIN36, SIN36, SIN72, SIN72,
    2 * SIN72 - SIN36, 2 * SIN72 - SIN36, SIN36 + SIN72,
]
NODE_PITCH_CLASS = [1, 7, -1, 4, -3, 6, -1, 4, 8]
NODE_COUNT = len(NODE_X)

PENTA = [
    [(0, 1, 0), (2, 0, 0), (3, 1, 0), (8, 0, 0), (8, 1, 0)],
    [(0, 1, 0), (0, 2, 0), (4, 2, 0), (5, 0, 0), (8, 1, 0)],
    [(0, 1, 1), (1, 0, 0), (1, 1, 0), (6, 0, 0), (7, 1, 0)],
    [(0, 1, 1), (0, 2, 1), (1, 1, 0), (4, 2, 0), (5, 0, 0)],
]

# NOTE_NAMESはA基準（theremin/src/core/tonnetz-grid.js）。
NOTE_NAMES = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']
C_SEMITONE = NOTE_NAMES.index('C')
MAJOR_SCALE_OFFSETS = [0, 2, 4, 5, 7, 9, 11]

# 88鍵(A0〜C8)ぶんの絶対半音範囲。アプリ本体(golden-tonnetz-board.js)と揃え、
# 明度(pitch)の見た目をスクリーンショットと一致させる。
SEMITONE_MIN = -39
SEMITONE_MAX = 48

NODE_R = 0.12
BG = '#111418'
EDGE_STROKE = 'rgba(224, 168, 60, 0.35)'
EDGE_WIDTH = 0.008


def node_xy(row, col, i):
    return (col + NODE_X[i]) * CELL_W, row * CELL_H + NODE_Y[i]


def semitone_at(row, col, i):
    return NODE_PITCH_CLASS[i] + 2 * col - row


def pitch_class_of(semitone):
    return (semitone + 3) % 12


def hue_of(semitone):
    return (semitone % 12) * 30


def is_in_major_scale(semitone, root_semitone):
    pc = pitch_class_of(semitone)
    return any((root_semitone + off) % 12 == pc for off in MAJOR_SCALE_OFFSETS)


def build_nodes(row_range, col_range):
    nodes = {}
    for row in range(row_range[0], row_range[1] + 1):
        for col in range(col_range[0], col_range[1] + 1):
            for i in range(NODE_COUNT):
                x, y = node_xy(row, col, i)
                nodes[(row, col, i)] = {
                    'x': x, 'y': y, 'semitone': semitone_at(row, col, i),
                }
    return nodes


def sort_pentagon(pts):
    cx = sum(p[0] for p in pts) / 5
    cy = sum(p[1] for p in pts) / 5
    return sorted(pts, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))


def line_intersect(p1, p2, p3, p4):
    d = (p1[0] - p2[0]) * (p3[1] - p4[1]) - (p1[1] - p2[1]) * (p3[0] - p4[0])
    t = ((p1[0] - p3[0]) * (p3[1] - p4[1]) - (p1[1] - p3[1]) * (p3[0] - p4[0])) / d
    return (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))


def star_of(pts):
    diagonals = [(pts[i], pts[(i + 2) % 5]) for i in range(5)]
    star_pts = [
        line_intersect(pts[(i + 4) % 5], pts[(i + 1) % 5], pts[i], pts[(i + 2) % 5])
        for i in range(5)
    ]
    return diagonals, star_pts


def build_edges(row_range, col_range):
    def in_range(row, col):
        return row_range[0] <= row <= row_range[1] and col_range[0] <= col <= col_range[1]

    seen = set()
    edges = []

    def add_edge(a, b):
        ra, rb = (round(a[0], 3), round(a[1], 3)), (round(b[0], 3), round(b[1], 3))
        key = (ra, rb) if ra <= rb else (rb, ra)
        if key in seen:
            return
        seen.add(key)
        edges.append((a, b))

    for row in range(row_range[0] - 1, row_range[1] + 1):
        for col in range(col_range[0] - 2, col_range[1] + 1):
            for tile in PENTA:
                if not all(in_range(row + dr, col + dc) for (_, dc, dr) in tile):
                    continue
                pts = sort_pentagon([node_xy(row + dr, col + dc, i) for (i, dc, dr) in tile])
                for i in range(5):
                    add_edge(pts[i], pts[(i + 1) % 5])
                diagonals, star_pts = star_of(pts)
                for a, b in diagonals:
                    add_edge(a, b)
                inner_diagonals, _ = star_of(sort_pentagon(star_pts))
                for a, b in inner_diagonals:
                    add_edge(a, b)

    for row in range(row_range[0], row_range[1] + 1):
        for col in range(col_range[0], col_range[1]):
            add_edge(node_xy(row, col, 3), node_xy(row, col + 1, 2))
            add_edge(node_xy(row, col, 7), node_xy(row, col + 1, 6))

    return edges


def node_fill(semitone):
    hue = hue_of(semitone)
    pitch_t = max(0.0, min(1.0, (semitone - SEMITONE_MIN) / (SEMITONE_MAX - SEMITONE_MIN)))
    lightness = 0.32 + pitch_t * 0.46
    r, g, b = colorsys.hls_to_rgb(hue / 360, lightness, 0.78)
    return f'rgb({round(r*255)},{round(g*255)},{round(b*255)})', pitch_t


def build_svg(row_range, col_range, scale=170, key_root=None, view_box=None, label_scale=1.0):
    nodes = build_nodes(row_range, col_range)
    edges = build_edges(row_range, col_range)

    if view_box:
        min_x, min_y, w_units, h_units = view_box
    else:
        xs = [n['x'] for n in nodes.values()]
        ys = [n['y'] for n in nodes.values()]
        margin = 0.5
        min_x, min_y = min(xs) - margin, min(ys) - margin
        w_units = (max(xs) - min(xs)) + margin * 2
        h_units = (max(ys) - min(ys)) + margin * 2

    width = w_units * scale
    height = h_units * scale

    parts = [
        f'<svg viewBox="0 0 {width:.1f} {height:.1f}" xmlns="http://www.w3.org/2000/svg" '
        f'overflow="hidden" '
        f'font-family="\'Hiragino Sans\', \'Yu Gothic\', sans-serif">',
        f'<rect x="0" y="0" width="{width:.1f}" height="{height:.1f}" fill="{BG}"/>',
    ]

    def px(x, y):
        return (x - min_x) * scale, (y - min_y) * scale

    for a, b in edges:
        ax, ay = px(*a)
        bx, by = px(*b)
        parts.append(
            f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
            f'stroke="{EDGE_STROKE}" stroke-width="{EDGE_WIDTH * scale:.2f}" stroke-linecap="round"/>'
        )

    r_px = NODE_R * scale
    font_px = 0.105 * scale * label_scale
    for (row, col, i), n in nodes.items():
        cx, cy = px(n['x'], n['y'])
        if not (-r_px <= cx <= width + r_px and -r_px <= cy <= height + r_px):
            continue
        semitone = n['semitone']
        fill, pitch_t = node_fill(semitone)
        active = key_root is None or is_in_major_scale(semitone, key_root)
        opacity = 1.0 if active else 0.32
        extra = '' if active else ' filter="grayscale(0.7)"'
        parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r_px:.1f}" fill="{fill}" '
            f'fill-opacity="{opacity}"{extra}/>'
        )
        label_color = '#1a1108' if pitch_t > 0.65 else 'rgba(255,255,255,0.92)'
        label_opacity = 1.0 if active else 0.45
        parts.append(
            f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'font-size="{font_px:.1f}" font-weight="700" fill="{label_color}" '
            f'fill-opacity="{label_opacity}">{NOTE_NAMES[pitch_class_of(semitone)]}</text>'
        )

    parts.append('</svg>')
    return '\n'.join(parts)


def main():
    out_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'images', 'puntone-golden-tonnetz-guide'))
    os.makedirs(out_dir, exist_ok=True)

    # 横1オクターブ(列方向+2半音/列なので6列=12半音)・縦3行ぶんに寄せる
    # （記事に載せるスクリーンショット代わりの図なので、実機の操作イメージに近い
    # くらいまで拡大する）。
    row_range, col_range = (-1, 1), (-3, 3)

    # 1. 盤面の全体像（アプリ本体と同じ配色で、1オクターブ×3行ぶんに拡大）。
    svg = build_svg(row_range, col_range, scale=170)
    with open(os.path.join(out_dir, 'golden-tonnetz-board.svg'), 'w', encoding='utf-8') as f:
        f.write(svg)

    # 2. 調ノブ（Cメジャーに絞り込み、圏外の音を暗くする）デモ。
    svg = build_svg(row_range, col_range, scale=170, key_root=C_SEMITONE)
    with open(os.path.join(out_dir, 'golden-tonnetz-keyfilter.svg'), 'w', encoding='utf-8') as f:
        f.write(svg)

    print('wrote 2 svg files to', out_dir)


if __name__ == '__main__':
    main()
