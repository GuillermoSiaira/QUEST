"""
BABEL Phase 0 - NatureLM-audio semantic encoder (GCP T4)
=======================================================
Runs EarthSpeciesProject/NatureLM-audio over the real .wav files in
babel/data/raw/esp_hf/ and evaluates whether bioacoustic embeddings cluster
by semantic primitive across species.

Expected environment:
  - GCP T4, 16GB VRAM
  - Python 3.10, CUDA 12
  - pip install bitsandbytes accelerate
"""

import json
import os
from pathlib import Path
import warnings

import librosa
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_distances
from sklearn.preprocessing import LabelEncoder, StandardScaler
from tqdm import tqdm
from transformers import AutoModel, AutoProcessor
import umap

warnings.filterwarnings("ignore")

np.random.seed(42)
torch.manual_seed(42)

DATA_DIR = Path("babel/data/raw/esp_hf")
OUTPUT_DIR = Path("babel/data/embeddings")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_ID = "EarthSpeciesProject/NatureLM-audio"
SAMPLE_RATE = 16_000
EXPECTED_EMBEDDING_DIM = 1024

MFCC_BASELINE_SIL = -0.185
CLAP_BASELINE_SIL = -0.313


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


def hf_token_kwargs() -> dict:
    token = os.getenv("HF_TOKEN")
    return {"token": token} if token else {}


def load_naturelm():
    print(f"Loading {MODEL_ID} with 8-bit quantization...")
    processor = AutoProcessor.from_pretrained(MODEL_ID, **hf_token_kwargs())
    try:
        model = AutoModel.from_pretrained(
            MODEL_ID,
            load_in_8bit=True,
            device_map="auto",
            **hf_token_kwargs(),
        )
        model.eval()
        print("[OK] Model ready in 8-bit mode.\n")
        return processor, model, "cuda_8bit"
    except Exception as exc:
        print(f"[~] 8-bit load failed: {exc}")
        print("[~] Falling back to CPU fp32. This will be slow.")
        model = AutoModel.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float32,
            device_map="cpu",
            **hf_token_kwargs(),
        )
        model.eval()
        print("[OK] Model ready on CPU fp32.\n")
        return processor, model, "cpu_fp32"


def move_inputs_to_model(inputs, model):
    device = getattr(model, "device", None)
    if device is None:
        try:
            device = next(model.parameters()).device
        except StopIteration:
            device = torch.device("cpu")
    return {k: v.to(device) if hasattr(v, "to") else v for k, v in inputs.items()}


def pool_outputs(outputs) -> np.ndarray:
    if hasattr(outputs, "last_hidden_state") and outputs.last_hidden_state is not None:
        emb = outputs.last_hidden_state.mean(dim=1).squeeze()
    elif hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
        emb = outputs.pooler_output.squeeze()
    elif hasattr(outputs, "hidden_states") and outputs.hidden_states is not None:
        emb = outputs.hidden_states[-1].mean(dim=1).squeeze()
    else:
        first = outputs[0] if isinstance(outputs, (tuple, list)) else None
        if first is None:
            raise ValueError("Model output does not expose a usable embedding tensor.")
        emb = first.mean(dim=1).squeeze() if first.ndim >= 3 else first.squeeze()

    emb = emb.detach().float().cpu().numpy().astype(np.float32)
    if emb.ndim > 1:
        emb = emb.reshape(-1)
    return emb


def normalize_embedding_dim(emb: np.ndarray) -> np.ndarray:
    if emb.shape[0] == EXPECTED_EMBEDDING_DIM:
        return emb
    if emb.shape[0] > EXPECTED_EMBEDDING_DIM:
        return emb[:EXPECTED_EMBEDDING_DIM]
    padded = np.zeros(EXPECTED_EMBEDDING_DIM, dtype=np.float32)
    padded[:emb.shape[0]] = emb
    return padded


def extract_embedding(path: str, processor, model) -> np.ndarray:
    y, _ = librosa.load(path, sr=SAMPLE_RATE, mono=True)
    if len(y) == 0:
        return np.zeros(EXPECTED_EMBEDDING_DIM, dtype=np.float32)

    inputs = processor(
        y,
        sampling_rate=SAMPLE_RATE,
        return_tensors="pt",
    )
    inputs = move_inputs_to_model(inputs, model)

    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True)

    return normalize_embedding_dim(pool_outputs(outputs))


def plot_umap(df_valid: pd.DataFrame, coords: np.ndarray, sil: float, sil_spec: float) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(18, 8), facecolor="#0d1117")

    for ax, color_by, title, color_map in [
        (axes[0], "primitive", "Por Primitiva Semantica (NatureLM)", PRIMITIVE_COLORS),
        (axes[1], "species", "Por Especie (NatureLM)", SPECIES_COLORS),
    ]:
        ax.set_facecolor("#0d1117")
        ax.set_title(title, color="white", fontsize=13, pad=10)

        for i, row in df_valid.iterrows():
            val = row[color_by]
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
                            labelcolor="white", fontsize=8, title="Primitiva",
                            title_fontsize=9)
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
                            labelcolor="white", fontsize=8, title="Especie",
                            title_fontsize=9)
            leg.get_title().set_color("white")

        ax.tick_params(colors="#555")
        for sp in ax.spines.values():
            sp.set_edgecolor("#222")

    fig.suptitle(
        f"BABEL Phase 0 - NatureLM-audio Embeddings . UMAP . {len(df_valid)} signals\n"
        f"Silhouette primitiva = {sil:.3f}  |  Silhouette especie = {sil_spec:.3f}",
        color="white", fontsize=13, y=1.01,
    )
    plt.tight_layout()

    out = OUTPUT_DIR / "phase0_naturelm_map.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="#0d1117")
    return out


def nearest_neighbor_cross_species(embeddings: np.ndarray, df_valid: pd.DataFrame):
    D = cosine_distances(embeddings)
    np.fill_diagonal(D, np.inf)
    nn = np.argmin(D, axis=1)

    same_prim = sum(
        df_valid.iloc[i]["primitive"] == df_valid.iloc[nn[i]]["primitive"]
        for i in range(len(df_valid))
    )
    cross_spec = sum(
        df_valid.iloc[i]["primitive"] == df_valid.iloc[nn[i]]["primitive"] and
        df_valid.iloc[i]["species"] != df_valid.iloc[nn[i]]["species"]
        for i in range(len(df_valid))
    )
    return same_prim, cross_spec, len(df_valid)


def main():
    with open(DATA_DIR / "manifest.json") as f:
        manifest = json.load(f)

    df = pd.DataFrame(manifest)
    print(f"Loaded {len(df)} files | {df['species'].nunique()} species | {df['primitive'].nunique()} primitives")
    print(f"Species  : {sorted(df['species'].unique())}")
    print(f"Primitives: {sorted(df['primitive'].unique())}\n")

    processor, model, load_mode = load_naturelm()

    print("Extracting NatureLM-audio embeddings from all audio files...")
    embeddings = []
    valid_idx = []

    for i, row in tqdm(df.iterrows(), total=len(df), desc="NatureLM"):
        try:
            emb = extract_embedding(row["path"], processor, model)
            embeddings.append(emb)
            valid_idx.append(i)
        except Exception:
            pass

    embeddings = np.array(embeddings, dtype=np.float32)
    df_valid = df.loc[valid_idx].reset_index(drop=True)

    scaler = StandardScaler()
    embeddings = scaler.fit_transform(embeddings)

    print(f"\nEmbeddings shape: {embeddings.shape} | load_mode={load_mode}")
    np.save(OUTPUT_DIR / "naturelm_embeddings.npy", embeddings)
    df_valid.to_csv(OUTPUT_DIR / "naturelm_metadata.csv", index=False)

    print("Running UMAP...")
    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=18,
        min_dist=0.08,
        metric="cosine",
        random_state=42,
    )
    coords = reducer.fit_transform(embeddings)
    np.save(OUTPUT_DIR / "naturelm_coords_2d.npy", coords)

    le = LabelEncoder()
    prim_labels = le.fit_transform(df_valid["primitive"])
    sil = silhouette_score(coords, prim_labels)
    print(f"Silhouette score (by primitive): {sil:.3f}")

    spec_labels = le.fit_transform(df_valid["species"])
    sil_spec = silhouette_score(coords, spec_labels)
    print(f"Silhouette score (by species)  : {sil_spec:.3f}")

    out = plot_umap(df_valid, coords, sil, sil_spec)
    print(f"\nSaved: {out}")

    same_prim, cross_spec, total = nearest_neighbor_cross_species(embeddings, df_valid)

    print("\n=== Nearest-Neighbor Cross-Species Test ===")
    print(f"  Same primitive as NN     : {same_prim}/{total} ({same_prim/total:.1%})")
    print(f"  Same primitive + diff sp : {cross_spec}/{total} ({cross_spec/total:.1%})")

    print("\n=== Phase 0 Encoder Comparison ===")
    print(f"  MFCC baseline : sil={MFCC_BASELINE_SIL:.3f}, cross-spec NN=0.2%")
    print(f"  CLAP baseline : sil={CLAP_BASELINE_SIL:.3f}, cross-spec NN=0.5%")
    print(f"  NatureLM      : sil={sil:.3f}, cross-spec NN={cross_spec/total:.1%}")

    if sil > 0.5:
        print("\n  [STRONG] Cross-species semantic clustering confirmed. BabelGraph is buildable.")
    elif sil > 0.25:
        print("\n  [MODERATE] Semantic signal present. Fine-tuning may improve alignment.")
    elif sil > 0.0:
        print("\n  [WEAK] Marginal positive semantic signal. Contrastive primitive tuning likely needed.")
    else:
        print("\n  [NEGATIVE] NatureLM does not separate primitives in this Phase 0 setup.")

    print("\n=== Phase 0 NatureLM complete ===")
    print(f"Output: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
