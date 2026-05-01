"""
BABEL Phase 0 — CLAP semantic encoder (CPU, no GPU required)
=============================================================
Uses CLAP (Contrastive Language-Audio Pretraining, laion/clap-htsat-unfused)
as a local semantic encoder proxy for NatureLM-audio.

CLAP is trained on diverse audio + text pairs — embeddings are semantically
aligned, not just acoustically shaped. This tests whether language-aligned
audio representations capture cross-species primitive equivalences that
MFCCs (silhouette = -0.185) could not.
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
import torch
from transformers import ClapModel, ClapProcessor
import umap
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
import warnings
warnings.filterwarnings("ignore")

np.random.seed(42)
torch.manual_seed(42)

DATA_DIR   = Path("babel/data/raw/esp_hf")
OUTPUT_DIR = Path("babel/data/embeddings")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_ID = "laion/clap-htsat-unfused"
SR_CLAP  = 48_000  # CLAP expects 48kHz

# ── 1. Load manifest ───────────────────────────────────────────────────────────
with open(DATA_DIR / "manifest.json") as f:
    manifest = json.load(f)

df = pd.DataFrame(manifest)
print(f"Loaded {len(df)} files | {df['species'].nunique()} species | {df['primitive'].nunique()} primitives")
print(f"Species  : {sorted(df['species'].unique())}")
print(f"Primitives: {sorted(df['primitive'].unique())}\n")

# ── 2. Load CLAP ──────────────────────────────────────────────────────────────
print(f"Loading {MODEL_ID}  (~340MB, first run downloads)...")
processor = ClapProcessor.from_pretrained(MODEL_ID)
model     = ClapModel.from_pretrained(MODEL_ID)
model.eval()
print("Model ready.\n")

# ── 3. Extract embeddings ─────────────────────────────────────────────────────
def extract_embedding(path: str) -> np.ndarray:
    y, _ = librosa.load(path, sr=SR_CLAP, mono=True)
    if len(y) == 0:
        return np.zeros(512)
    inputs = processor(audio=y, return_tensors="pt", sampling_rate=SR_CLAP)
    with torch.no_grad():
        audio_out = model.audio_model(
            input_features=inputs["input_features"],
            is_longer=inputs.get("is_longer"),
        )
        pooled = audio_out.pooler_output          # (1, hidden_size)
        projected = model.audio_projection(pooled) # (1, 512)
    return projected.squeeze().numpy()

print("Extracting CLAP embeddings from all audio files...")
embeddings = []
valid_idx  = []

for i, row in tqdm(df.iterrows(), total=len(df), desc="CLAP"):
    try:
        emb = extract_embedding(row["path"])
        embeddings.append(emb)
        valid_idx.append(i)
    except Exception:
        pass

embeddings = np.array(embeddings)
df_valid   = df.loc[valid_idx].reset_index(drop=True)

scaler     = StandardScaler()
embeddings = scaler.fit_transform(embeddings)

print(f"\nEmbeddings shape: {embeddings.shape}")
np.save(OUTPUT_DIR / "clap_embeddings.npy", embeddings)
df_valid.to_csv(OUTPUT_DIR / "clap_metadata.csv", index=False)

# ── 4. UMAP ───────────────────────────────────────────────────────────────────
print("Running UMAP...")
reducer = umap.UMAP(
    n_components=2,
    n_neighbors=18,
    min_dist=0.08,
    metric="cosine",
    random_state=42,
)
coords = reducer.fit_transform(embeddings)
np.save(OUTPUT_DIR / "clap_coords_2d.npy", coords)

# ── 5. Silhouette ─────────────────────────────────────────────────────────────
le = LabelEncoder()
prim_labels = le.fit_transform(df_valid["primitive"])
sil = silhouette_score(coords, prim_labels)
print(f"Silhouette score (by primitive): {sil:.3f}")

spec_labels = le.fit_transform(df_valid["species"])
sil_spec = silhouette_score(coords, spec_labels)
print(f"Silhouette score (by species)  : {sil_spec:.3f}")

# ── 6. Plot ───────────────────────────────────────────────────────────────────
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
    (axes[0], "primitive", "Por Primitiva Semantica (CLAP)", PRIMITIVE_COLORS),
    (axes[1], "species",   "Por Especie (CLAP)",             SPECIES_COLORS),
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
            mpatches.Patch(color=c, label=p.replace("_", " ").title())
            for p, c in PRIMITIVE_COLORS.items()
            if p in df_valid["primitive"].values
        ]
        leg = ax.legend(handles=patches, loc="lower left", framealpha=0.25,
                        labelcolor="white", fontsize=8, title="Primitiva", title_fontsize=9)
        leg.get_title().set_color("white")
    else:
        handles = [
            plt.Line2D([0], [0], marker=SPECIES_MARKERS.get(s, "."),
                       color=SPECIES_COLORS.get(s, "#aaa"),
                       linestyle="None", markersize=9,
                       label=s.replace("_", " ").title())
            for s in df_valid["species"].unique()
        ]
        leg = ax.legend(handles=handles, loc="lower left", framealpha=0.25,
                        labelcolor="white", fontsize=8, title="Especie", title_fontsize=9)
        leg.get_title().set_color("white")

    ax.tick_params(colors="#555")
    for sp in ax.spines.values():
        sp.set_edgecolor("#222")

delta = sil - (-0.185)
sign  = "+" if delta >= 0 else ""
fig.suptitle(
    f"BABEL Phase 0 — CLAP Embeddings (semantic encoder) . UMAP . {len(df_valid)} signals\n"
    f"Silhouette primitiva = {sil:.3f}  |  Silhouette especie = {sil_spec:.3f}"
    f"  |  delta vs MFCC = {sign}{delta:.3f}",
    color="white", fontsize=13, y=1.01,
)
plt.tight_layout()

out = OUTPUT_DIR / "phase0_clap_map.png"
plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="#0d1117")
print(f"\nSaved: {out}")

# ── 7. Nearest-neighbor cross-species test ────────────────────────────────────
from sklearn.metrics.pairwise import cosine_distances
D = cosine_distances(embeddings)
np.fill_diagonal(D, np.inf)
nn = np.argmin(D, axis=1)

same_prim  = sum(df_valid.iloc[i]["primitive"] == df_valid.iloc[nn[i]]["primitive"]
                 for i in range(len(df_valid)))
cross_spec = sum(
    df_valid.iloc[i]["primitive"] == df_valid.iloc[nn[i]]["primitive"] and
    df_valid.iloc[i]["species"]   != df_valid.iloc[nn[i]]["species"]
    for i in range(len(df_valid))
)
total = len(df_valid)

print(f"\n=== Nearest-Neighbor Cross-Species Test ===")
print(f"  Same primitive as NN     : {same_prim}/{total} ({same_prim/total:.1%})")
print(f"  Same primitive + diff sp : {cross_spec}/{total} ({cross_spec/total:.1%})")
print(f"\n  MFCC baseline: sil=-0.185, cross-spec NN=0.2%")
print(f"  CLAP result  : sil={sil:.3f}, cross-spec NN={cross_spec/total:.1%}")

if sil > 0.5:
    print("\n  [STRONG] Cross-species semantic clustering confirmed. BabelGraph is buildable.")
elif sil > 0.25:
    print("\n  [MODERATE] Semantic signal present. Fine-tuning needed but project is viable.")
elif sil > 0.0:
    print("\n  [WEAK] Marginal improvement over MFCCs. NatureLM-audio on GCP is the next step.")
else:
    print("\n  [NEGATIVE] CLAP also fails. NatureLM-audio (animal-specific training) required.")

print("\n=== Phase 0 CLAP complete ===")
print(f"Output: {OUTPUT_DIR.resolve()}")
