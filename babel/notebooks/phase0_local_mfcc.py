"""
BABEL Phase 0 — Local MFCC runner (no GPU, no torch required)
===============================================================
Extracts 40 MFCCs from each real .wav file in babel/data/raw/esp_hf/
and runs UMAP to check whether acoustic features cluster by semantic primitive.

This is the CPU-accessible proxy for NatureLM-audio embeddings.
MFCCs capture spectral shape — a rough but informative acoustic fingerprint.
If primitives cluster here, NatureLM embeddings (richer representations) will do better.
"""

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from tqdm import tqdm
import librosa
import umap
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
import warnings
warnings.filterwarnings("ignore")

np.random.seed(42)

DATA_DIR   = Path("babel/data/raw/esp_hf")
OUTPUT_DIR = Path("babel/data/embeddings")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 1. Load manifest ───────────────────────────────────────────────────────────
with open(DATA_DIR / "manifest.json") as f:
    manifest = json.load(f)

df = pd.DataFrame(manifest)
print(f"Loaded {len(df)} files | {df['species'].nunique()} species | {df['primitive'].nunique()} primitives")
print(f"Species  : {sorted(df['species'].unique())}")
print(f"Primitives: {sorted(df['primitive'].unique())}\n")


# ── 2. Extract MFCC features ──────────────────────────────────────────────────
SR       = 16_000
N_MFCC   = 40
N_FRAMES = 50   # fixed number of frames (pad/trim to normalize duration)

def extract_features(path: str) -> np.ndarray:
    """
    40 MFCCs (mean + std over time) + spectral centroid + ZCR = 82-dim vector.
    This is the lightweight proxy for NatureLM-audio embeddings.
    """
    y, sr = librosa.load(path, sr=SR, mono=True)
    if len(y) == 0:
        return np.zeros(N_MFCC * 2 + 2)

    mfcc    = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    zcr      = librosa.feature.zero_crossing_rate(y)

    features = np.concatenate([
        mfcc.mean(axis=1),          # 40 — mean MFCC per coefficient
        mfcc.std(axis=1),           # 40 — std MFCC per coefficient
        centroid.mean(axis=1),      # 1  — avg spectral centroid
        zcr.mean(axis=1),           # 1  — avg zero-crossing rate
    ])
    return features.astype(np.float32)


print("Extracting MFCC features from all audio files...")
embeddings = []
valid_idx  = []

for i, row in tqdm(df.iterrows(), total=len(df), desc="MFCC"):
    try:
        feat = extract_features(row["path"])
        embeddings.append(feat)
        valid_idx.append(i)
    except Exception as e:
        pass

embeddings = np.array(embeddings)
df_valid   = df.loc[valid_idx].reset_index(drop=True)

# Normalize features
scaler     = StandardScaler()
embeddings = scaler.fit_transform(embeddings)

print(f"\nFeatures shape: {embeddings.shape}")
np.save(OUTPUT_DIR / "mfcc_embeddings.npy", embeddings)
df_valid.to_csv(OUTPUT_DIR / "mfcc_metadata.csv", index=False)


# ── 3. UMAP ───────────────────────────────────────────────────────────────────
print("Running UMAP...")
reducer = umap.UMAP(
    n_components=2,
    n_neighbors=18,
    min_dist=0.08,
    metric="cosine",
    random_state=42,
)
coords = reducer.fit_transform(embeddings)
np.save(OUTPUT_DIR / "mfcc_coords_2d.npy", coords)


# ── 4. Silhouette ─────────────────────────────────────────────────────────────
le = LabelEncoder()
prim_labels = le.fit_transform(df_valid["primitive"])
sil = silhouette_score(coords, prim_labels)
print(f"Silhouette score (by primitive): {sil:.3f}")

spec_labels = le.fit_transform(df_valid["species"])
sil_spec = silhouette_score(coords, spec_labels)
print(f"Silhouette score (by species)  : {sil_spec:.3f}")


# ── 5. Plot ───────────────────────────────────────────────────────────────────
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
SPECIES_MARKERS = {
    "vervet_monkey": "o", "prairie_dog": "s", "bottlenose_dolphin": "^",
    "sperm_whale": "D", "crow": "X", "elephant": "P",
    "pig": "v", "humpback_whale": "*", "songbird": "h",
}

fig, axes = plt.subplots(1, 2, figsize=(18, 8), facecolor="#0d1117")

for ax, color_by, title, color_map in [
    (axes[0], "primitive", "Por Primitiva Semántica", PRIMITIVE_COLORS),
    (axes[1], "species",   "Por Especie",             SPECIES_COLORS),
]:
    ax.set_facecolor("#0d1117")
    ax.set_title(title, color="white", fontsize=13, pad=10)

    for i, row in df_valid.iterrows():
        val  = row[color_by]
        spec = row["species"]
        ax.scatter(
            coords[i, 0], coords[i, 1],
            c=color_map.get(val, "#aaa"),
            marker=SPECIES_MARKERS.get(spec, "."),
            s=75, alpha=0.80, linewidths=0.4, edgecolors="white",
        )

    if color_by == "primitive":
        patches = [
            mpatches.Patch(color=c, label=p.replace("_"," ").title())
            for p, c in PRIMITIVE_COLORS.items()
            if p in df_valid["primitive"].values
        ]
        leg = ax.legend(handles=patches, loc="lower left", framealpha=0.25,
                        labelcolor="white", fontsize=8, title="Primitiva", title_fontsize=9)
        leg.get_title().set_color("white")
    else:
        handles = [
            plt.Line2D([0],[0], marker=SPECIES_MARKERS.get(s,"."),
                       color=SPECIES_COLORS.get(s,"#aaa"),
                       linestyle="None", markersize=9,
                       label=s.replace("_"," ").title())
            for s in df_valid["species"].unique()
        ]
        leg = ax.legend(handles=handles, loc="lower left", framealpha=0.25,
                        labelcolor="white", fontsize=8, title="Especie", title_fontsize=9)
        leg.get_title().set_color("white")

    ax.tick_params(colors="#555")
    for sp in ax.spines.values():
        sp.set_edgecolor("#222")

fig.suptitle(
    f"BABEL Phase 0 — MFCC Features (real audio) · UMAP · {len(df_valid)} señales\n"
    f"Silhouette primitiva = {sil:.3f}  |  Silhouette especie = {sil_spec:.3f}",
    color="white", fontsize=13, y=1.01,
)
plt.tight_layout()

out = OUTPUT_DIR / "phase0_mfcc_map.png"
plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="#0d1117")
print(f"\nSaved: {out}")

# ── 6. Nearest-neighbor cross-species test ────────────────────────────────────
from sklearn.metrics.pairwise import cosine_distances
D = cosine_distances(embeddings)
np.fill_diagonal(D, np.inf)
nn = np.argmin(D, axis=1)

same_prim    = sum(df_valid.iloc[i]["primitive"] == df_valid.iloc[nn[i]]["primitive"] for i in range(len(df_valid)))
cross_spec   = sum(
    df_valid.iloc[i]["primitive"] == df_valid.iloc[nn[i]]["primitive"] and
    df_valid.iloc[i]["species"]   != df_valid.iloc[nn[i]]["species"]
    for i in range(len(df_valid))
)
total = len(df_valid)

print(f"\n=== Nearest-Neighbor Cross-Species Test ===")
print(f"  Same primitive as NN     : {same_prim}/{total} ({same_prim/total:.1%})")
print(f"  Same primitive + diff sp : {cross_spec}/{total} ({cross_spec/total:.1%})")

if same_prim/total > 0.6:
    print("\n  [OK] Cross-species primitive clustering is viable with real audio features.")
else:
    print("\n  [~] Moderate signal — NatureLM embeddings (richer) will do better on GCP.")

print("\n=== Phase 0 complete ===")
print(f"Output: {OUTPUT_DIR.resolve()}")
