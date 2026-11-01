# helloworld-

## 🧱 Lego Builder

Application Streamlit pour créer des modèles Lego pièce par pièce.

### Lancer l'app

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Fonctionnalités

- **Grille 20x20 cliquable** : cliquez sur une case pour poser (ou retirer) la pièce sélectionnée
- **14 pièces** : briques, plaques et ronds (1x1 à 2x4), avec rotation 0°/90°
- **14 couleurs Lego officielles** approximées
- **Construction en couches** : empilez vos pièces verticalement (brique = 1, plaque = 1/3)
- **Vue 2D** (grille cliquable) et **vue 3D isométrique**
- **Export** : modèle en JSON, liste de pièces en CSV, **import** de modèles JSON
- **Inventaire** automatique des pièces utilisées

### Fichiers

- `app.py` — application Streamlit
- `lego_builder.py` — logique métier (pièces, collisions, export JSON/CSV)
- `lego_canvas.py` — rendu SVG 2D / 3D isométrique du modèle
- `test_lego_builder.py` — tests unitaires (`pytest test_lego_builder.py`)

### Format du modèle JSON

```json
{
  "meta": {"name": "mon-modele", "grid": [20, 20]},
  "pieces": [
    {"id": "abc12345", "type": "Brique 2x4", "color": "Rouge", "x": 2, "y": 3, "layer": 0, "rot": 0}
  ]
}
```
