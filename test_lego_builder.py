"""Tests de la logique Lego Builder."""
import json

from lego_builder import (
    add_piece,
    contains,
    fits,
    from_json,
    overlapping,
    parts_list,
    piece_dims,
    piece_height,
    remove_at,
    to_json,
)

GRID_W = GRID_H = 20


def test_dims_rotation():
    assert piece_dims("Brique 1x4", 0) == (1, 4, "brick")
    assert piece_dims("Brique 1x4", 90) == (4, 1, "brick")
    assert piece_dims("Brique 2x2", 90) == (2, 2, "brick")
    assert piece_height("plate") == 1 / 3
    assert piece_height("brick") == 1.0


def test_add_and_overlap():
    model = []
    p = add_piece(model, "Brique 2x4", "Rouge", 0, 0, 0)
    assert p is not None and len(model) == 1
    # chevauche la brique 2x4 en (1,1)
    assert add_piece(model, "Brique 1x1", "Bleu", 1, 1, 0) is None
    assert len(model) == 1
    # même empreinte mais couche différente : OK
    assert add_piece(model, "Brique 1x1", "Bleu", 1, 1, 1) is not None
    # hors empreinte : OK
    assert add_piece(model, "Brique 1x1", "Vert", 5, 5, 0) is not None
    assert len(model) == 3


def test_fits_grid_bounds():
    model = []
    assert fits(model, "Brique 2x4", 0, GRID_W - 1, 0, 0, GRID_W, GRID_H) is False
    assert fits(model, "Brique 2x4", 0, GRID_W - 2, 0, 0, GRID_W, GRID_H) is True


def test_remove_at():
    model = []
    add_piece(model, "Brique 2x3", "Jaune", 2, 2, 0)
    removed = remove_at(model, 3, 4, 0)
    assert removed is not None and removed.type == "Brique 2x3"
    assert remove_at(model, 3, 4, 0) is None
    assert model == []


def test_contains_and_overlapping():
    model = []
    p = add_piece(model, "Plaque 2x2", "Noir", 4, 4, 0)
    assert contains(p, 4, 4) and contains(p, 5, 5) and not contains(p, 6, 6)
    assert len(overlapping(model, 5, 5, 1, 1, 0)) == 1
    assert len(overlapping(model, 5, 5, 1, 1, 1)) == 0


def test_json_roundtrip():
    model = []
    add_piece(model, "Rond 2x2", "Blanc", 0, 0, 0)
    add_piece(model, "Brique 1x4", "Rouge", 3, 3, 2, rot=90)
    text = to_json(model, {"name": "test"})
    data = json.loads(text)
    assert data["meta"]["name"] == "test"
    model2 = from_json(text)
    assert len(model2) == 2
    assert model2[1].rot == 90 and model2[1].layer == 2
    assert to_json(model2) == to_json(model)


def test_parts_list():
    model = []
    add_piece(model, "Brique 1x1", "Rouge", 0, 0, 0)
    add_piece(model, "Brique 1x1", "Rouge", 1, 0, 0)
    add_piece(model, "Brique 1x1", "Bleu", 2, 0, 0)
    parts = parts_list(model)
    assert {"Pièce": "Brique 1x1", "Couleur": "Rouge", "Quantité": 2} in parts
    assert {"Pièce": "Brique 1x1", "Couleur": "Bleu", "Quantité": 1} in parts
