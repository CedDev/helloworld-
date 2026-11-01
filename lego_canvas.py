"""Composant HTML/JS interactif : grille 2D et vue 3D isométrique du modèle Lego."""
from __future__ import annotations

import json

from lego_builder import LEGO_COLORS, piece_dims, piece_height

CELL = 44
STUD = 12
GRID_W = 20
GRID_H = 20


def _render_pieces(model: list, view: str) -> str:
    if view == "2d":
        return _render_2d(model)
    return _render_3d(model)


def _render_2d(model: list) -> str:
    layer = model.meta["layer"] if hasattr(model, "meta") else 0
    parts = []
    for p in model:
        if p["layer"] != layer:
            continue
        w, h, kind = piece_dims(p["type"], p["rot"])
        color = LEGO_COLORS.get(p["color"], "#999999")
        x0, y0 = p["x"] * CELL, p["y"] * CELL
        parts.append(
            f'<rect x="{x0}" y="{y0}" width="{w * CELL - 4}" height="{h * CELL - 4}" rx="6" '
            f'fill="{color}" stroke="#222" stroke-width="2" class="piece" '
            f'data-x="{p["x"]}" data-y="{p["y"]}">'
            f"<title>{p['type']} — {p['color']} ({p['x']}, {p['y']})</title></rect>"
        )
        for sx in range(w):
            for sy in range(h):
                cx, cy = x0 + sx * CELL + CELL / 2, y0 + sy * CELL + CELL / 2
                parts.append(
                    f'<circle cx="{cx}" cy="{cy}" r="{STUD / 2 - 2}" fill="none" stroke="#00000030" stroke-width="1.5" />'
                )
    return "".join(parts)


def _render_3d(model: list) -> str:
    proj = []
    for p in model:
        w, h, kind = piece_dims(p["type"], p["rot"])
        bh = piece_height(kind)
        color = LEGO_COLORS.get(p["color"], "#999999")
        # base de la pièce (couche z = layer)
        z0 = p["layer"] * 1.0
        proj.append((z0, _iso_block(p["x"], p["y"], w, h, z0, z0 + bh, color, p["type"], round_=kind == "round")))
    proj.sort(key=lambda t: t[0])
    return "".join(s for _, s in proj)


def _iso_block(x, y, w, h, z0, z1, color, label, round_=False) -> str:
    def iso(px, py, pz):
        return ((px - py) * 0.866 * CELL / 2 + GRID_W * CELL / 2, (px + py) * 0.5 * CELL / 2 - pz * CELL * 0.6 + 80)

    top = [iso(x, y, z1), iso(x + w, y, z1), iso(x + w, y + h, z1), iso(x, y + h, z1)]
    right = [iso(x + w, y, z1), iso(x + w, y + h, z1), iso(x + w, y + h, z0), iso(x + w, y, z0)]
    left = [iso(x, y + h, z1), iso(x + w, y + h, z1), iso(x + w, y + h, z0), iso(x, y + h, z0)]
    pts = lambda poly: " ".join(f"{a:.1f},{b:.1f}" for a, b in poly)
    out = [
        f'<polygon points="{pts(left)}" fill="{shade(color, -25)}" stroke="#111" stroke-width="1" />',
        f'<polygon points="{pts(right)}" fill="{shade(color, -12)}" stroke="#111" stroke-width="1" />',
        f'<polygon points="{pts(top)}" fill="{color}" stroke="#111" stroke-width="1" />',
    ]
    # studs sur le dessus
    for sx in range(w):
        for sy in range(h):
            cx, cy = iso(x + sx + 0.5, y + sy + 0.5, z1)
            out.append(
                f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{STUD * 0.32:.1f}" ry="{STUD * 0.18:.1f}" '
                f'fill="{shade(color, 12)}" stroke="#00000040" stroke-width="1" />'
            )
    return "".join(out)


def shade(hex_color: str, amt: int) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (max(0, min(255, int(h[i : i + 2], 16) + amt)) for i in (0, 2, 4))
    return f"#{r:02X}{g:02X}{b:02X}"


CANVAS_HTML = """
<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  body { margin:0; font-family: sans-serif; background:#eef1f5; }
  svg { display:block; cursor:crosshair; }
  .gridline { stroke:#d5dae1; stroke-width:1; }
  .piece:hover { filter:brightness(1.15); }
</style></head><body>
<svg id="cv" width="__W__" height="__H__"></svg>
<script>
const CELL = __CELL__, GW = __GW__, GH = __GH__;
const svg = document.getElementById('cv');
const NS = 'http://www.w3.org/2000/svg';
for (let x = 0; x <= GW; x++) {
  const l = document.createElementNS(NS, 'line');
  l.setAttribute('x1', x*CELL); l.setAttribute('y1', 0);
  l.setAttribute('x2', x*CELL); l.setAttribute('y2', GH*CELL);
  l.setAttribute('class', 'gridline'); svg.appendChild(l);
}
for (let y = 0; y <= GH; y++) {
  const l = document.createElementNS(NS, 'line');
  l.setAttribute('x1', 0); l.setAttribute('y1', y*CELL);
  l.setAttribute('x2', GW*CELL); l.setAttribute('y2', y*CELL);
  l.setAttribute('class', 'gridline'); svg.appendChild(l);
}
const layer = document.createElementNS(NS, 'g');
layer.innerHTML = __PIECES__;
svg.appendChild(layer);
if (__CLICKABLE__) {
  svg.addEventListener('click', (e) => {
    const r = svg.getBoundingClientRect();
    const x = Math.floor((e.clientX - r.left) / CELL);
    const y = Math.floor((e.clientY - r.top) / CELL);
    if (x < 0 || y < 0 || x >= GW || y >= GH) return;
    window.parent.location.search = '?click=' + x + ',' + y;
  });
}
</script></body></html>
"""


def render_canvas(model_dicts: list[dict], view: str, layer: int) -> str:
    class M(list):
        pass

    m = M(model_dicts)
    m.meta = {"layer": layer}
    width = GRID_W * CELL
    height = GRID_H * CELL
    if view == "3d":
        height = max(height, 700)
        width = max(width, 900)
    pieces_svg = _render_pieces(m, view)
    return (
        CANVAS_HTML.replace("__W__", str(width))
        .replace("__H__", str(height))
        .replace("__CELL__", str(CELL))
        .replace("__GW__", str(GRID_W))
        .replace("__GH__", str(GRID_H))
        .replace("__CLICKABLE__", "true" if view == "2d" else "false")
        .replace("__PIECES__", json.dumps(pieces_svg))
    )
