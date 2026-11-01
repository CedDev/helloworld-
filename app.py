"""Lego Builder — créez des modèles Lego pièce par pièce sur une grille."""
from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import streamlit as st

from lego_builder import (
    LEGO_COLORS,
    PIECES,
    add_piece,
    fits,
    from_json,
    parts_list,
    piece_dims,
    piece_height,
    remove_at,
    to_json,
)
from lego_canvas import GRID_H, GRID_W, render_canvas

st.set_page_config(page_title="Lego Builder", page_icon="🧱", layout="wide")

if "model" not in st.session_state:
    st.session_state.model = []
if "layer" not in st.session_state:
    st.session_state.layer = 0


def model_dicts() -> list[dict]:
    return [asdict(p) for p in st.session_state.model]


def sync_click_from_url() -> None:
    click = st.query_params.get("click")
    if not click:
        return
    st.query_params.clear()
    try:
        x, y = (int(v) for v in click.split(","))
    except ValueError:
        return
    if x < 0 or x >= GRID_W or y < 0 or y >= GRID_H:
        return
    if st.session_state.get("tool", "➕ Ajouter") == "➕ Ajouter":
        piece = st.session_state.get("piece_type", "Brique 2x4")
        color = st.session_state.get("color", "Rouge")
        rot = st.session_state.get("rot", 0)
        if fits(st.session_state.model, piece, rot, x, y, st.session_state.layer, GRID_W, GRID_H):
            add_piece(st.session_state.model, piece, color, x, y, st.session_state.layer, rot)
        else:
            w, h, _ = piece_dims(piece, rot)
            st.session_state["last_error"] = f"Chevauchement ou hors grille en ({x}, {y}) — empreinte {w}x{h}."
    else:
        remove_at(st.session_state.model, x, y, st.session_state.layer)


sync_click_from_url()

st.title("🧱 Lego Builder")
st.caption("Composez votre modèle Lego pièce par pièce, couche par couche.")

with st.sidebar:
    st.header("🧰 Boîte à outils")
    st.session_state.tool = st.radio("Outil", ["➕ Ajouter", "➖ Supprimer"], horizontal=True)
    st.session_state.piece_type = st.selectbox("Pièce", list(PIECES.keys()))
    st.session_state.color = st.selectbox("Couleur", list(LEGO_COLORS.keys()))
    st.session_state.rot = st.radio("Rotation", [0, 90], horizontal=True, format_func=lambda r: f"{r}°")
    w, h, kind = piece_dims(st.session_state.piece_type, st.session_state.rot)
    st.caption(f"Empreinte : {w} x {h} studs — hauteur {'1/3' if kind == 'plate' else '1'} brique")

    st.divider()
    st.header("🧱 Couches")
    n_layers = max([p.layer for p in st.session_state.model], default=-1) + 1
    st.session_state.layer = st.number_input(
        "Couche active",
        min_value=0,
        max_value=max(0, n_layers),
        value=min(st.session_state.layer, max(0, n_layers)),
        step=1,
    )
    if st.button("➕ Nouvelle couche au-dessus"):
        st.session_state.layer = n_layers
        st.rerun()

    st.divider()
    st.header("🗑️ Modèle")
    if st.button("Tout effacer", type="secondary"):
        st.session_state.model = []
        st.session_state.layer = 0
        st.rerun()

left, right = st.columns([3, 2])

with left:
    st.radio("Vue", ["2D", "3D"], key="view", horizontal=True)
    html = render_canvas(model_dicts(), st.session_state.view, st.session_state.layer)
    h = 700 if st.session_state.view == "3D" else GRID_H * 44 + 10
    st.components.v1.html(html, height=h, scrolling=True)
    st.caption(
        "💡 Cliquez sur la grille (vue 2D) pour poser/retirer la pièce sélectionnée, "
        "ou utilisez les coordonnées ci-dessous."
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        px = st.number_input("X", min_value=0, max_value=GRID_W - 1, value=0, key="px")
    with c2:
        py = st.number_input("Y", min_value=0, max_value=GRID_H - 1, value=0, key="py")
    with c3:
        if st.button("➕ Poser ici", use_container_width=True):
            if fits(
                st.session_state.model,
                st.session_state.piece_type,
                st.session_state.rot,
                px,
                py,
                st.session_state.layer,
                GRID_W,
                GRID_H,
            ):
                add_piece(
                    st.session_state.model,
                    st.session_state.piece_type,
                    st.session_state.color,
                    px,
                    py,
                    st.session_state.layer,
                    st.session_state.rot,
                )
            else:
                w2, h2, _ = piece_dims(st.session_state.piece_type, st.session_state.rot)
                st.error(f"Impossible : chevauchement ou hors grille ({w2}x{h2} en ({px},{py})).")
    with c4:
        if st.button("➖ Retirer ici", use_container_width=True):
            remove_at(st.session_state.model, px, py, st.session_state.layer)
    if "last_error" in st.session_state:
        st.warning(st.session_state.pop("last_error"))

with right:
    tab_list, tab_export, tab_import = st.tabs(["📋 Pièces posées", "💾 Export / Import", "📊 Inventaire"])

    with tab_list:
        if st.session_state.model:
            rows = [
                {
                    "Pièce": p.type,
                    "Couleur": p.color,
                    "X": p.x,
                    "Y": p.y,
                    "Couche": p.layer,
                    "Rot": f"{p.rot}°",
                }
                for p in sorted(st.session_state.model, key=lambda p: (p.layer, p.y, p.x))
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Aucune pièce pour le moment. Choisissez une pièce et cliquez sur la grille !")

    with tab_export:
        st.download_button(
            "⬇️ Télécharger le modèle (JSON)",
            data=to_json(st.session_state.model, {"name": "mon-modele", "grid": [GRID_W, GRID_H]}),
            file_name="modele_lego.json",
            mime="application/json",
        )
        csv = pd.DataFrame(parts_list(st.session_state.model)).to_csv(index=False)
        st.download_button(
            "⬇️ Télécharger la liste de pièces (CSV)",
            data=csv,
            file_name="liste_pieces.csv",
            mime="text/csv",
        )
        with st.expander("Aperçu JSON"):
            st.code(to_json(st.session_state.model, {"grid": [GRID_W, GRID_H]}), language="json")

    with tab_import:
        uploaded = st.file_uploader("Importer un modèle JSON", type=["json"])
        if uploaded is not None:
            try:
                st.session_state.model = from_json(uploaded.read().decode("utf-8"))
                st.success(f"{len(st.session_state.model)} pièces importées.")
                st.rerun()
            except Exception as exc:
                st.error(f"Fichier invalide : {exc}")

st.divider()
total = len(st.session_state.model)
hauteur = max(
    (p.layer + piece_height(piece_dims(p.type, p.rot)[2]) for p in st.session_state.model),
    default=0.0,
)
st.caption(f"🧱 {total} pièce(s) posée(s) — hauteur du modèle : {hauteur:.2f} briques équivalentes.")
