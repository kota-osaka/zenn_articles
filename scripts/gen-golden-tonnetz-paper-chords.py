# -*- coding: utf-8 -*-
"""
黄金トネッツ記事用: 表の「論文準拠」列を生成する。

- maj: 黄金三角形（鋭角、辺の比が 0.618:1:1）になる実例を盤面全体から探す。
- min: グノモン（鈍角、辺の比が 1:1:1.618）になる実例を盤面全体から探す。
- それ以外（dim/sus4/sus2/maj7/m7/7/m7b5/6/m6）: 論文はこれらの形を明示して
  いないため、範囲を限定せず盤面全体から最も辺の多い（＝最も密に閉じた）
  実例を「論文の考え方を延長した参考形」として採用する。
"""
import itertools
import os
import importlib.util
from collections import deque

spec = importlib.util.spec_from_file_location(
    "gtz", os.path.join(os.path.dirname(__file__), "gen-golden-tonnetz-images.py")
)
gtz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gtz)

BG = gtz.BG
SCALE = 200
R = gtz.NODE_R
MARGIN = 50

ROW_RANGE = (-2, 2)
COL_RANGE = (-4, 4)


def name(n):
    return gtz.NOTE_NAMES[gtz.pitch_class_of(gtz.semitone_at(*n))]


def build_edge_lookup():
    row_range, col_range = (-3, 3), (-5, 5)
    edges = gtz.build_edges(row_range, col_range)
    coord_to_id = {}
    for row in range(row_range[0], row_range[1] + 1):
        for col in range(col_range[0], col_range[1] + 1):
            for i in range(gtz.NODE_COUNT):
                x, y = gtz.node_xy(row, col, i)
                coord_to_id[(round(x, 3), round(y, 3))] = (row, col, i)
    edge_set = set()
    for a, b in edges:
        ka = (round(a[0], 3), round(a[1], 3))
        kb = (round(b[0], 3), round(b[1], 3))
        ida = coord_to_id.get(ka)
        idb = coord_to_id.get(kb)
        if ida is None or idb is None:
            continue
        edge_set.add(frozenset((ida, idb)))
    return edge_set


# Cメジャースケール(自然音)のピッチクラスのみを使う。コード例はCメジャー
# スケールの範囲内で作る、という前提のため、シャープの音は候補に含めない。
C_MAJOR_PCS = {(gtz.C_SEMITONE + off) % 12 for off in gtz.MAJOR_SCALE_OFFSETS}


def build_pc_index(nodes_iter):
    """ピッチクラス(Cメジャースケールの7音のみ)ごとにノードを索引化する。"""
    idx = {}
    for n in nodes_iter:
        pc = gtz.pitch_class_of(gtz.semitone_at(*n))
        if pc not in C_MAJOR_PCS:
            continue
        idx.setdefault(pc, []).append(n)
    return idx


def _wide_nodes():
    for row in range(ROW_RANGE[0], ROW_RANGE[1] + 1):
        for col in range(COL_RANGE[0], COL_RANGE[1] + 1):
            for i in range(gtz.NODE_COUNT):
                yield (row, col, i)


WIDE_PC_INDEX = build_pc_index(_wide_nodes())

# ユーザーが最初に示した参照画像の11ノード（row=-1、col=0/1）。
# E(単独,上)/G#,A#(対)/F,D(対)/G,C(対,中央)/F,D(対,繰り返し)/A,B(対,下)。
POOL = {
    (-1, 1, 0), (-1, 0, 1), (-1, 1, 1), (-1, 0, 3), (-1, 1, 2),
    (-1, 0, 5), (-1, 1, 4), (-1, 0, 7), (-1, 1, 6), (-1, 0, 8), (-1, 1, 8),
}

POOL_PC_INDEX = build_pc_index(POOL)

CHORD_TYPES = [
    ("maj", {0, 4, 7}),
    ("min", {0, 3, 7}),
    ("dim", {0, 3, 6}),
    ("sus4", {0, 5, 7}),
    ("sus2", {0, 2, 7}),
    ("maj7", {0, 4, 7, 11}),
    ("m7", {0, 3, 7, 10}),
    ("7", {0, 4, 7, 10}),
    ("m7b5", {0, 3, 6, 10}),
    ("6", {0, 4, 7, 9}),
    ("m6", {0, 3, 7, 9}),
]


def is_connected(nodes, edge_set):
    nodes = list(nodes)
    seen = {nodes[0]}
    q = deque([nodes[0]])
    local_adj = {n: set() for n in nodes}
    for a, b in itertools.combinations(nodes, 2):
        if frozenset((a, b)) in edge_set:
            local_adj[a].add(b)
            local_adj[b].add(a)
    while q:
        u = q.popleft()
        for v in local_adj[u]:
            if v not in seen:
                seen.add(v)
                q.append(v)
    return len(seen) == len(nodes)


def count_edges(nodes, edge_set):
    return sum(1 for a, b in itertools.combinations(nodes, 2) if frozenset((a, b)) in edge_set)


def dist(a, b):
    ax, ay = gtz.node_xy(*a)
    bx, by = gtz.node_xy(*b)
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def bbox_area(nodes):
    xs = [gtz.node_xy(*n)[0] for n in nodes]
    ys = [gtz.node_xy(*n)[1] for n in nodes]
    return (max(xs) - min(xs)) * (max(ys) - min(ys))


def is_root_position(root_node, other_nodes):
    """転回形でないこと＝ルートの絶対音高が、コード構成音の中で最も低いこと。"""
    root_abs = gtz.semitone_at(*root_node)
    return all(gtz.semitone_at(*n) > root_abs for n in other_nodes)


def find_all_candidates(offsets, edge_set, require_root_position=True, pc_index=None):
    """root_letterは音名(シャープ含む)。自然音に限定せず、pc_indexにある
    ピッチクラスなら何でもルート・構成音として使う。"""
    if pc_index is None:
        pc_index = WIDE_PC_INDEX
    results = []
    for root_pc in pc_index:
        root_letter = gtz.NOTE_NAMES[root_pc]
        target_pcs = sorted(((root_pc + off) % 12) for off in offsets)
        if any(pc not in pc_index for pc in target_pcs):
            continue
        root_index = target_pcs.index(root_pc)
        candidate_lists = [pc_index[pc] for pc in target_pcs]
        for combo in itertools.product(*candidate_lists):
            if len(set(combo)) != len(combo):
                continue
            if not is_connected(combo, edge_set):
                continue
            root_node = combo[root_index]
            others = [n for i, n in enumerate(combo) if i != root_index]
            if require_root_position and not is_root_position(root_node, others):
                continue
            ec = count_edges(combo, edge_set)
            results.append((ec, root_letter, combo))
    return results


def find_pool_first(offsets, edge_set, shape_target=None):
    """転回は常に禁止（ルート位置のみ）。ルート音・構成音はCメジャースケール
    (自然音)の範囲内から探す。
    shape_target指定時: POOL内で目標の形（黄金三角形/グノモン）が見つかればそれを使い、
    無ければ範囲外(盤面全体)を探す。
    shape_target未指定時: POOL内・範囲外を通じて実現可能な最大の辺数を求め、
    その辺数を達成する実例がPOOL内にあればそれを、無ければ範囲外の実例を使う
    （範囲外を使った場合はOUT-OF-POOLとして呼び出し元に伝える）。
    戻り値: (候補, in_pool: bool, was_rp: bool=常にTrue)。"""
    pool_candidates = find_all_candidates(offsets, edge_set, require_root_position=True,
                                           pc_index=POOL_PC_INDEX)

    if shape_target is not None:
        matches = [c for c in pool_candidates if shape_of_triad(c[2]) == shape_target]
        if matches:
            matches.sort(key=lambda c: (0 if c[1] == 'C' else 1, bbox_area(c[2])))
            return matches[0], True, True
        wide_candidates = find_all_candidates(offsets, edge_set, require_root_position=True,
                                               pc_index=WIDE_PC_INDEX)
        matches = [c for c in wide_candidates if shape_of_triad(c[2]) == shape_target]
        if matches:
            matches.sort(key=lambda c: (0 if c[1] == 'C' else 1, bbox_area(c[2])))
            return matches[0], False, True
        return None, None, None

    pool_max_ec = max((c[0] for c in pool_candidates), default=-1)
    n_max_possible = len(offsets) * (len(offsets) - 1) // 2
    if pool_candidates and pool_max_ec == n_max_possible:
        # プール内で理論上の最大辺数(完全に閉じた形)に達しているので、
        # 範囲外を探すまでもなくこれを採用する。
        pool_best = [c for c in pool_candidates if c[0] == pool_max_ec]
        pool_best.sort(key=lambda c: (-c[0], bbox_area(c[2])))
        return pool_best[0], True, True

    wide_candidates = find_all_candidates(offsets, edge_set, require_root_position=True,
                                           pc_index=WIDE_PC_INDEX)
    if not pool_candidates and not wide_candidates:
        return None, None, None
    max_ec = max([c[0] for c in pool_candidates] + [c[0] for c in wide_candidates])
    pool_best = [c for c in pool_candidates if c[0] == max_ec]
    if pool_best:
        pool_best.sort(key=lambda c: (-c[0], bbox_area(c[2])))
        return pool_best[0], True, True
    wide_best = [c for c in wide_candidates if c[0] == max_ec]
    wide_best.sort(key=lambda c: (-c[0], bbox_area(c[2])))
    return wide_best[0], False, True


def shape_of_triad(nodes):
    sides = sorted(round(dist(a, b), 3) for a, b in itertools.combinations(nodes, 2))
    return tuple(sides)


TRIANGLE_SIDES = (0.618, 1.0, 1.0)
GNOMON_SIDES = (1.0, 1.0, 1.618)


def build_svg(nodes, edge_set):
    xs = [gtz.node_xy(*p)[0] for p in nodes]
    ys = [gtz.node_xy(*p)[1] for p in nodes]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = (max_x - min_x) * SCALE + MARGIN * 2
    height = (max_y - min_y) * SCALE + MARGIN * 2

    def px(p):
        x, y = gtz.node_xy(*p)
        return ((x - min_x) * SCALE + MARGIN, (y - min_y) * SCALE + MARGIN)

    coords = {p: px(p) for p in nodes}
    real_edges = [(a, b) for a, b in itertools.combinations(nodes, 2) if frozenset((a, b)) in edge_set]

    parts = [
        f'<svg viewBox="0 0 {width:.1f} {height:.1f}" xmlns="http://www.w3.org/2000/svg" '
        f'overflow="hidden" font-family="\'Hiragino Sans\', \'Yu Gothic\', sans-serif">',
        f'<rect x="0" y="0" width="{width:.1f}" height="{height:.1f}" rx="16" fill="{BG}"/>',
    ]
    for a, b in real_edges:
        ax, ay = coords[a]
        bx, by = coords[b]
        parts.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
                      f'stroke="#e0a83c" stroke-width="4" stroke-linecap="round"/>')
    for p in nodes:
        coord = coords[p]
        fill, pitch_t = gtz.node_fill(gtz.semitone_at(*p))
        parts.append(f'<circle cx="{coord[0]:.1f}" cy="{coord[1]:.1f}" r="{R*SCALE:.1f}" fill="{fill}"/>')
        label_color = '#1a1108' if pitch_t > 0.65 else 'rgba(255,255,255,0.92)'
        parts.append(f'<text x="{coord[0]:.1f}" y="{coord[1]:.1f}" text-anchor="middle" '
                      f'dominant-baseline="central" font-size="22" font-weight="700" '
                      f'fill="{label_color}">{name(p)}</text>')
    parts.append('</svg>')
    return "\n".join(parts), width, height


def main():
    out_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'images', 'puntone-golden-tonnetz-guide'))
    os.makedirs(out_dir, exist_ok=True)
    edge_set = build_edge_lookup()

    for suffix, offsets in CHORD_TYPES:
        shape_target = TRIANGLE_SIDES if suffix == 'maj' else (GNOMON_SIDES if suffix == 'min' else None)
        chosen, in_pool, was_rp = find_pool_first(offsets, edge_set, shape_target)
        if chosen is None:
            print('NOT FOUND:', suffix)
            continue
        ec, root_letter, nodes = chosen
        root_abs = [gtz.semitone_at(*n) for n in nodes]
        fname = f'chord-{root_letter.replace("#", "s")}{suffix}-paper'
        svg, width, height = build_svg(nodes, edge_set)
        svg_path = os.path.join(out_dir, f'{fname}.svg')
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg)
        names = [name(n) for n in nodes]
        rp_flag = 'root-position' if was_rp else 'INVERSION(fallback)'
        pool_flag = 'IN-POOL' if in_pool else 'OUT-OF-POOL'
        print('wrote', fname, round(width), round(height), 'notes=', names,
              'edges=', ec, 'abs_semitones=', root_abs, rp_flag, pool_flag)


if __name__ == '__main__':
    main()
