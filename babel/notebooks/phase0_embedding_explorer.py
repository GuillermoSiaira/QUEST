"""
BABEL — Phase 0: Embedding Explorer
=====================================
Run this as a script or convert to Jupyter with: jupytext --to notebook phase0_embedding_explorer.py

GOAL: Check whether NatureLM-audio embeddings cluster by SEMANTIC PRIMITIVE
across different species. If alarm calls from vervets, crows and prairie dogs
cluster together (vs. contact calls, food calls, etc.), the cross-species
graph is buildable.

Steps:
  1. Load labeled audio files from data/raw/
  2. Encode with NatureLM-audio (or lightweight BEATs fallback)
  3. Reduce to 2D with UMAP
  4. Plot and compute silhouette score
  5. Save embeddings + metadata for Phase 1

Cost on GCP T4: ~$0.35/hour. Estimated runtime: 30–60 min for 500 clips.
"""

# %% [1] Setup & Config
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from babel.src.encoder import BabelEncoder
from babel.src.visualizer import reduce_embeddings, plot_embedding_space, compute_cluster_separation
from babel.src.primitives import get_all_primitives, describe_primitive

DATA_DIR = Path("babel/data/raw")
OUTPUT_DIR = Path("babel/data/embeddings")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Use lightweight=True on CPU, False on T4 GPU
LIGHTWEIGHT = not __import__("torch").cuda.is_available()
print(f"Mode: {'CPU/lightweight (BEATs)' if LIGHTWEIGHT else 'GPU/full (NatureLM-audio)'}")
print(f"Data dir: {DATA_DIR.resolve()}")


# %% [2] Load manifest files
def load_manifests(data_dir: Path) -> pd.DataFrame:
    """
    Scan data/raw/ for manifest.json files and consolidate.
    Each manifest entry: {path, species, primitive, source, ...}
    """
    records = []
    for manifest_path in data_dir.rglob("manifest.json"):
        with open(manifest_path) as f:
            entries = json.load(f)
        for entry in entries:
            # Normalize: keep only files that exist
            p = Path(entry.get("path", ""))
            if p.exists():
                records.append({
                    "path": str(p),
                    "species": entry.get("species", "unknown"),
                    "primitive": entry.get("primitive", "UNKNOWN"),
                    "call_type": entry.get("call_type", ""),
                    "source": entry.get("source", ""),
                })

    df = pd.DataFrame(records)
    print(f"\nLoaded {len(df)} audio files from {df['source'].nunique()} sources")
    print(f"Species: {sorted(df['species'].unique())}")
    print(f"Primitives: {sorted(df['primitive'].unique())}")
    return df


metadata = load_manifests(DATA_DIR)

if len(metadata) == 0:
    print("\n⚠ No data found. Run first:")
    print("  python babel/data/download_datasets.py --datasets auto")
    print("\nFalling back to SYNTHETIC demo data for pipeline validation...")

    # Synthetic data — validate the pipeline without real audio
    import torch
    import soundfile as sf
    import tempfile

    DEMO_DIR = Path(tempfile.mkdtemp())
    demo_records = []
    sr = 16_000

    synthetic_primitives = {
        "ALARM_AERIAL":        [("vervet_monkey", 8), ("crow", 6)],
        "ALARM_GROUND":        [("vervet_monkey", 8), ("prairie_dog", 6)],
        "CONTACT_AFFILIATION": [("bottlenose_dolphin", 6), ("elephant", 4)],
        "FOOD_CALL":           [("crow", 5), ("prairie_dog", 4)],
    }

    np.random.seed(42)
    for primitive, species_list in synthetic_primitives.items():
        # Each primitive gets a distinct base frequency cluster
        base_freq = 440 * (1 + list(synthetic_primitives.keys()).index(primitive) * 0.3)
        for species, count in species_list:
            for i in range(count):
                duration = np.random.uniform(0.5, 2.0)
                t = np.linspace(0, duration, int(sr * duration))
                freq = base_freq + np.random.normal(0, 20)
                wave = 0.3 * np.sin(2 * np.pi * freq * t)
                wave += 0.05 * np.random.randn(len(wave))  # noise
                out_path = DEMO_DIR / f"{primitive}_{species}_{i:02d}.wav"
                sf.write(str(out_path), wave, sr)
                demo_records.append({
                    "path": str(out_path),
                    "species": species,
                    "primitive": primitive,
                    "source": "synthetic_demo",
                })

    metadata = pd.DataFrame(demo_records)
    print(f"Generated {len(metadata)} synthetic clips for demo.")


# %% [3] Encode with NatureLM-audio
encoder = BabelEncoder(device="auto", lightweight=LIGHTWEIGHT)
encoder.load()

audio_paths = metadata["path"].tolist()
print(f"\nEncoding {len(audio_paths)} files...")
embeddings = encoder.encode_batch(audio_paths, verbose=True)

# Save raw embeddings
np.save(OUTPUT_DIR / "embeddings.npy", embeddings)
metadata.to_csv(OUTPUT_DIR / "metadata.csv", index=False)
print(f"\nSaved embeddings: {OUTPUT_DIR}/embeddings.npy ({embeddings.shape})")


# %% [4] Dimensionality reduction — UMAP
print("\nReducing to 2D with UMAP...")
coords_2d = reduce_embeddings(
    embeddings,
    method="umap",
    n_neighbors=min(15, len(embeddings) - 1),
    min_dist=0.1,
)
np.save(OUTPUT_DIR / "coords_2d.npy", coords_2d)
print(f"Saved 2D coords: {OUTPUT_DIR}/coords_2d.npy")


# %% [5] Plot
fig, ax = plot_embedding_space(
    coords_2d,
    metadata,
    title="BABEL Phase 0 — Semantic Primitive Clustering Across Species",
    output_path=OUTPUT_DIR / "phase0_embedding_map.png",
)


# %% [6] Cluster quality metrics
print("\nComputing cluster separation metrics...")
from sklearn.preprocessing import LabelEncoder as LE
label_enc = LE()
numeric_labels = label_enc.fit_transform(metadata["primitive"].fillna("UNKNOWN"))
metrics = compute_cluster_separation(coords_2d, numeric_labels)

# Save metrics
with open(OUTPUT_DIR / "phase0_metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)


# %% [7] Per-primitive breakdown
print("\n=== Per-Primitive Signal Count ===")
for prim in sorted(metadata["primitive"].unique()):
    subset = metadata[metadata["primitive"] == prim]
    species_counts = subset["species"].value_counts().to_dict()
    print(f"\n  {prim} ({len(subset)} total)")
    for sp, count in species_counts.items():
        print(f"    • {sp}: {count}")


# %% [8] Cross-species nearest-neighbor test
print("\n=== Cross-Species Nearest Neighbor Test ===")
print("For each signal, check if nearest neighbor in embedding space shares the same primitive.")

from sklearn.metrics.pairwise import cosine_distances

D = cosine_distances(embeddings)
np.fill_diagonal(D, np.inf)
nn_indices = np.argmin(D, axis=1)

correct_primitive = 0
cross_species = 0
total = len(embeddings)

for i in range(total):
    nn = nn_indices[i]
    same_prim = metadata.iloc[i]["primitive"] == metadata.iloc[nn]["primitive"]
    diff_spec = metadata.iloc[i]["species"] != metadata.iloc[nn]["species"]
    if same_prim:
        correct_primitive += 1
    if same_prim and diff_spec:
        cross_species += 1

print(f"\n  Nearest neighbor shares same primitive : {correct_primitive}/{total} ({correct_primitive/total:.1%})")
print(f"  ... AND is from a different species    : {cross_species}/{total} ({cross_species/total:.1%})")

if correct_primitive / total > 0.7:
    print("\n  ✓ Strong signal — cross-species primitive clustering is viable.")
elif correct_primitive / total > 0.5:
    print("\n  ~ Moderate signal — fine-tuning needed but project is feasible.")
else:
    print("\n  ✗ Weak signal — reconsider encoder or primitive taxonomy.")

print("\n=== Phase 0 Complete ===")
print(f"Results saved to: {OUTPUT_DIR.resolve()}")
print("Next: Phase 1 — build the semantic primitive graph with verified labels.")
