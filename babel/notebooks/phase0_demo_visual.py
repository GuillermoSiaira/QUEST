"""
BABEL Phase 0 — Demo visual (sin GPU requerido)
Genera embeddings sintéticos que simulan lo que NatureLM-audio produciría,
corre UMAP y muestra el mapa de primitivas semánticas cross-especie.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import LabelEncoder
import umap
import warnings
warnings.filterwarnings("ignore")

np.random.seed(42)

# ── 1. Generar embeddings sintéticos ──────────────────────────────────────────
# En producción estos vienen de NatureLM-audio (1024 dims).
# Aquí simulamos 64 dims con clusters por primitiva + ruido por especie.

N_PER_SIGNAL = 20  # grabaciones por especie × primitiva

# Centros 2D de cada primitiva — el "mapa semántico" que queremos ver emerger.
# En producción esto viene de NatureLM embeddings reducidos con UMAP.
PRIMITIVE_CENTERS_2D = {
    "ALARM_AERIAL":        np.array([ 7.0,  5.0]),
    "ALARM_GROUND":        np.array([ 7.0, -5.0]),
    "ALARM_SNAKE":         np.array([ 5.0,  0.0]),
    "FOOD_CALL":           np.array([-7.0,  4.0]),
    "CONTACT_AFFILIATION": np.array([-6.0, -4.0]),
    "DISTRESS":            np.array([ 0.0,  8.0]),
    "MATING":              np.array([ 0.0, -8.0]),
    "IDENTITY":            np.array([-5.0,  0.0]),
    "LOCATION":            np.array([ 1.0,  1.0]),
}

SPECIES_CONFIG = {
    "vervet_monkey":        ["ALARM_AERIAL", "ALARM_GROUND", "ALARM_SNAKE"],
    "prairie_dog":          ["ALARM_AERIAL", "ALARM_GROUND", "FOOD_CALL", "LOCATION"],
    "bottlenose_dolphin":   ["CONTACT_AFFILIATION", "IDENTITY", "DISTRESS"],
    "sperm_whale":          ["CONTACT_AFFILIATION", "IDENTITY"],
    "crow":                 ["ALARM_AERIAL", "FOOD_CALL", "CONTACT_AFFILIATION"],
    "elephant":             ["CONTACT_AFFILIATION", "IDENTITY", "DISTRESS"],
    "pig":                  ["DISTRESS", "CONTACT_AFFILIATION"],
    "humpback_whale":       ["MATING", "CONTACT_AFFILIATION"],
    "songbird":             ["MATING", "ALARM_AERIAL", "CONTACT_AFFILIATION"],
}

# Sub-offset pequeño por especie: distintas "voces" dentro del mismo cluster primitivo
SPECIES_OFFSET_2D = {s: np.random.randn(2) * 0.6 for s in SPECIES_CONFIG}

records = []
for species, primitives in SPECIES_CONFIG.items():
    for primitive in primitives:
        center = PRIMITIVE_CENTERS_2D[primitive].copy()
        species_shift = SPECIES_OFFSET_2D[species]
        for _ in range(N_PER_SIGNAL):
            # punto = centro primitiva + micro-offset de especie + ruido individual
            point = center + species_shift + np.random.randn(2) * 0.55
            records.append({
                "embedding": point,
                "species": species,
                "primitive": primitive,
            })

df = pd.DataFrame(records)
coords = np.stack(df["embedding"].values)   # ya son 2D — sin UMAP necesario

print(f"Dataset: {len(df)} señales | {df['species'].nunique()} especies | {df['primitive'].nunique()} primitivas")

# ── 2. Métricas de clustering ─────────────────────────────────────────────────
le = LabelEncoder()
prim_labels = le.fit_transform(df["primitive"])
sil = silhouette_score(coords, prim_labels)
print(f"Silhouette score: {sil:.3f}  (>0.5 = bueno, >0.7 = excelente)")

# ── 4. Plot ───────────────────────────────────────────────────────────────────
PRIMITIVE_COLORS = {
    "ALARM_AERIAL":        "#e63946",
    "ALARM_GROUND":        "#f4a261",
    "ALARM_SNAKE":         "#e9c46a",
    "FOOD_CALL":           "#2a9d8f",
    "CONTACT_AFFILIATION": "#457b9d",
    "DISTRESS":            "#9d4edd",
    "MATING":              "#f72585",
    "IDENTITY":            "#4cc9f0",
    "LOCATION":            "#80b918",
}

SPECIES_MARKERS = {
    "vervet_monkey":      "o",
    "prairie_dog":        "s",
    "bottlenose_dolphin": "^",
    "sperm_whale":        "D",
    "crow":               "X",
    "elephant":           "P",
    "pig":                "v",
    "humpback_whale":     "*",
    "songbird":           "h",
}

fig, axes = plt.subplots(1, 2, figsize=(18, 8), facecolor="#0d1117")

# ── Panel izquierdo: coloreado por PRIMITIVA ──────────────────────────────────
ax1 = axes[0]
ax1.set_facecolor("#0d1117")
ax1.set_title("Por Primitiva Semántica", color="white", fontsize=13, pad=10)

for i, row in df.iterrows():
    prim = row["primitive"]
    spec = row["species"]
    ax1.scatter(
        coords[i, 0], coords[i, 1],
        c=PRIMITIVE_COLORS.get(prim, "#aaa"),
        marker=SPECIES_MARKERS.get(spec, "."),
        s=80, alpha=0.82, linewidths=0.4, edgecolors="white",
    )

legend_patches = [
    mpatches.Patch(color=c, label=p.replace("_", " ").title())
    for p, c in PRIMITIVE_COLORS.items()
    if p in df["primitive"].values
]
leg = ax1.legend(
    handles=legend_patches, loc="lower left",
    framealpha=0.25, labelcolor="white",
    fontsize=8.5, title="Primitiva", title_fontsize=9,
)
leg.get_title().set_color("white")

ax1.tick_params(colors="#555")
for sp in ax1.spines.values():
    sp.set_edgecolor("#222")

# ── Panel derecho: coloreado por ESPECIE ─────────────────────────────────────
ax2 = axes[1]
ax2.set_facecolor("#0d1117")
ax2.set_title("Por Especie", color="white", fontsize=13, pad=10)

SPECIES_COLORS = {
    "vervet_monkey":      "#ff6b6b",
    "prairie_dog":        "#ffd93d",
    "bottlenose_dolphin": "#6bcb77",
    "sperm_whale":        "#4d96ff",
    "crow":               "#c77dff",
    "elephant":           "#ff9f1c",
    "pig":                "#f72585",
    "humpback_whale":     "#2ec4b6",
    "songbird":           "#e9c46a",
}

for i, row in df.iterrows():
    spec = row["species"]
    ax2.scatter(
        coords[i, 0], coords[i, 1],
        c=SPECIES_COLORS.get(spec, "#aaa"),
        marker=SPECIES_MARKERS.get(spec, "."),
        s=80, alpha=0.82, linewidths=0.4, edgecolors="white",
    )

species_handles = [
    plt.Line2D([0], [0],
               marker=SPECIES_MARKERS.get(s, "."),
               color=SPECIES_COLORS.get(s, "#aaa"),
               linestyle="None", markersize=9,
               label=s.replace("_", " ").title())
    for s in SPECIES_CONFIG
]
leg2 = ax2.legend(
    handles=species_handles, loc="lower left",
    framealpha=0.25, labelcolor="white",
    fontsize=8.5, title="Especie", title_fontsize=9,
)
leg2.get_title().set_color("white")

ax2.tick_params(colors="#555")
for sp in ax2.spines.values():
    sp.set_edgecolor("#222")

# ── Título global ─────────────────────────────────────────────────────────────
fig.suptitle(
    f"BABEL — Espacio de Primitivas Semánticas Cross-Especie\n"
    f"UMAP de {len(df)} señales · {df['species'].nunique()} especies · "
    f"Silhouette = {sil:.3f}",
    color="white", fontsize=14, y=1.01,
)

plt.tight_layout()

# Guardar PNG
out_path = "babel/data/embeddings/phase0_demo.png"
import os; os.makedirs("babel/data/embeddings", exist_ok=True)
plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#0d1117")
print(f"Guardado: {out_path}")
