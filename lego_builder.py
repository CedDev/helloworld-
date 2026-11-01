"""Logique métier du Lego Builder : pièces, couleurs, modèle et exports."""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass

LEGO_COLORS = {
    "Rouge": "#C4281C",
    "Bleu": "#0057A6",
    "Jaune": "#F2CD37",
    "Vert": "#237841",
    "Blanc": "#FFFFFF",
    "Noir": "#1B2A34",
    "Gris clair": "#A3A2A4",
    "Gris foncé": "#6D6E5C",
    "Orange": "#FE8A18",
    "Violet": "#81007B",
    "Rose": "#E4ADC8",
    "Marron": "#5F3109",
    "Bleu clair": "#B4D2E3",
    "Vert clair": "#C1E1B7",
}

# type -> (largeur, hauteur en studs, nature) ; hauteur brique = 1, plaque = 1/3
PIECES = {
    "Brique 1x1": (1, 1, "brick"),
    "Brique 1x2": (1, 2, "brick"),
    "Brique 1x3": (1, 3, "brick"),
    "Brique 1x4": (1, 4, "brick"),
    "Brique 2x2": (2, 2, "brick"),
    "Brique 2x3": (2, 3, "brick"),
    "Brique 2x4": (2, 4, "brick"),
    "Plaque 1x1": (1, 1, "plate"),
    "Plaque 1x2": (1, 2, "plate"),
    "Plaque 1x4": (1, 4, "plate"),
    "Plaque 2x2": (2, 2, "plate"),
    "Plaque 2x4": (2, 4, "plate"),
    "Rond 1x1": (1, 1, "round"),
    "Rond 2x2": (2, 2, "round"),
}

BRICK_HEIGHT = 1.0
PLATE_HEIGHT = 1.0 / 3.0


@dataclass
class Placement:
    id: str
    type: str
    color: str
    x: int
    y: int
    layer: int
    rot: int = 0


def piece_dims(piece_type: str, rot: int = 0) -> tuple[int, int, str]:
    w, h, kind = PIECES[piece_type]
    if rot == 90 and w != h:
        w, h = h, w
    return w, h, kind


def piece_height(kind: str) -> float:
    return PLATE_HEIGHT if kind == "plate" else BRICK_HEIGHT


def contains(p: Placement, x: int, y: int) -> bool:
    w, h, _ = piece_dims(p.type, p.rot)
    return p.x <= x < p.x + w and p.y <= y < p.y + h


def rects_overlap(ax: int, ay: int, aw: int, ah: int, bx: int, by: int, bw: int, bh: int) -> bool:
    return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)


def overlapping(model: list[Placement], x: int, y: int, w: int, h: int, layer: int) -> list[Placement]:
    return [
        p
        for p in model
        if p.layer == layer and rects_overlap(x, y, w, h, p.x, p.y, *piece_dims(p.type, p.rot)[:2])
    ]


def fits(model: list[Placement], piece_type: str, rot: int, x: int, y: int, layer: int, grid_w: int, grid_h: int) -> bool:
    w, h, _ = piece_dims(piece_type, rot)
    if x < 0 or y < 0 or x + w > grid_w or y + h > grid_h:
        return False
    return not overlapping(model, x, y, w, h, layer)


def add_piece(
    model: list[Placement],
    piece_type: str,
    color: str,
    x: int,
    y: int,
    layer: int,
    rot: int = 0,
    overwrite: bool = False,
) -> Placement | None:
    w, h, _ = piece_dims(piece_type, rot)
    if overwrite:
        for p in overlapping(model, x, y, w, h, layer):
            model.remove(p)
    if not fits(model, piece_type, rot, x, y, layer, grid_w=10**6, grid_h=10**6):
        return None
    p = Placement(id=uuid.uuid4().hex[:8], type=piece_type, color=color, x=x, y=y, layer=layer, rot=rot)
    model.append(p)
    return p


def remove_at(model: list[Placement], x: int, y: int, layer: int) -> Placement | None:
    for p in list(model):
        if p.layer == layer and contains(p, x, y):
            model.remove(p)
            return p
    return None


def to_json(model: list[Placement], meta: dict | None = None) -> str:
    return json.dumps(
        {"meta": meta or {}, "pieces": [asdict(p) for p in model]},
        indent=2,
        ensure_ascii=False,
    )


def from_json(text: str) -> list[Placement]:
    data = json.loads(text)
    model = []
    for d in data.get("pieces", []):
        model.append(
            Placement(
                id=d.get("id") or uuid.uuid4().hex[:8],
                type=d["type"],
                color=d["color"],
                x=int(d["x"]),
                y=int(d["y"]),
                layer=int(d.get("layer", 0)),
                rot=int(d.get("rot", 0)),
            )
        )
    return model


def parts_list(model: list[Placement]) -> list[dict]:
    counts: dict[tuple[str, str], int] = {}
    for p in model:
        counts[(p.type, p.color)] = counts.get((p.type, p.color), 0) + 1
    return [
        {"Pièce": t, "Couleur": c, "Quantité": q}
        for (t, c), q in sorted(counts.items())
    ]
