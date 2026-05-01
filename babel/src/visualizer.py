"""
Embedding visualization — compress high-dim embeddings to 2D and plot clusters.
Used in Phase 0 to check if semantic primitives separate across species.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path
from typing import Optional


PRIMITIVE_COLORS = {
    "ALARM_AERIAL":       "#e63946",
    "ALARM_GROUND":       "#f4a261",
    "ALARM_SNAKE":        "#e9c46a",
    "FOOD_CALL":          "#2a9d8f",
    "CONTACT_AFFILIATION":"#457b9d",
    "DISTRESS":           "#9d4edd",
    "MATING":             "#f72585",
    "IDENTITY":           "#4cc9f0",
    "LOCATION":           "#80b918",
    "UNKNOWN":            "#adb5bd",
}

SPECIES_MARKERS = {
    "vervet_monkey":      "o",
    "prairie_dog":        "s",
    "bottlenose_dolphin": "^",
    "sperm_whale":        "D",
    "elephant":           "P",
    "crow":               "X",
    "pig":                "v",
    "cow":                "<",
    "songbird":           "*",
    "unknown":            ".",
}


def reduce_embeddings(
    embeddings: np.ndarray,
    method: str = "umap",
    n_neighbors: int = 15,
    min_dist: float = 0.1,
    random_state: int = 42,
) -> np.ndarray:
    """
    Reduce (N, D) embeddings to (N, 2) for plotting.
    method: 'umap' (preferred) or 'tsne' (fallback, slower)
    """
    if method == "umap":
        from umap import UMAP
        reducer = UMAP(
            n_components=2,
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            random_state=random_state,
        )
    else:
        from sklearn.manifold import TSNE
        reducer = TSNE(n_components=2, random_state=random_state, perplexity=30)

    return reducer.fit_transform(embeddings)


def plot_embedding_space(
    coords_2d: np.ndarray,
    metadata: pd.DataFrame,
    title: str = "BABEL — Semantic Primitive Embedding Space",
    output_path: Optional[Path] = None,
    figsize: tuple = (12, 9),
):
    """
    Plot 2D embeddings colored by primitive and shaped by species.

    metadata must have columns: 'primitive', 'species', 'label' (optional)
    """
    fig, ax = plt.subplots(figsize=figsize, facecolor="#0f0f14")
    ax.set_facecolor("#0f0f14")

    primitives = metadata["primitive"].fillna("UNKNOWN")
    species = metadata["species"].fillna("unknown")

    for i in range(len(coords_2d)):
        prim = primitives.iloc[i]
        spec = species.iloc[i]
        color = PRIMITIVE_COLORS.get(prim, PRIMITIVE_COLORS["UNKNOWN"])
        marker = SPECIES_MARKERS.get(spec, SPECIES_MARKERS["unknown"])

        ax.scatter(
            coords_2d[i, 0], coords_2d[i, 1],
            c=color, marker=marker,
            s=90, alpha=0.85, linewidths=0.5, edgecolors="white",
        )

    # Legend — primitives (color)
    prim_patches = [
        mpatches.Patch(color=c, label=p)
        for p, c in PRIMITIVE_COLORS.items()
        if p in primitives.values
    ]
    legend1 = ax.legend(
        handles=prim_patches, title="Primitive",
        loc="upper left", framealpha=0.3,
        labelcolor="white", title_fontsize=9, fontsize=8,
    )
    legend1.get_title().set_color("white")
    ax.add_artist(legend1)

    # Legend — species (marker)
    spec_handles = [
        plt.Line2D([0], [0], marker=m, color="white", linestyle="None",
                   markersize=8, label=s)
        for s, m in SPECIES_MARKERS.items()
        if s in species.values
    ]
    legend2 = ax.legend(
        handles=spec_handles, title="Species",
        loc="upper right", framealpha=0.3,
        labelcolor="white", title_fontsize=9, fontsize=8,
    )
    legend2.get_title().set_color("white")

    ax.set_title(title, color="white", fontsize=13, pad=12)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {output_path}")

    return fig, ax


def compute_cluster_separation(
    coords_2d: np.ndarray,
    labels: np.ndarray,
) -> dict:
    """
    Compute silhouette score and inter/intra-cluster distances.
    Higher silhouette → better separation → cross-species primitive clustering works.
    """
    from sklearn.metrics import silhouette_score, davies_bouldin_score

    unique = np.unique(labels)
    if len(unique) < 2:
        return {"silhouette": None, "davies_bouldin": None}

    sil = silhouette_score(coords_2d, labels)
    db = davies_bouldin_score(coords_2d, labels)

    results = {
        "silhouette": round(float(sil), 4),       # range [-1, 1], higher is better
        "davies_bouldin": round(float(db), 4),    # lower is better
        "n_clusters": len(unique),
        "n_samples": len(labels),
    }

    print("\n=== Cluster Separation Metrics ===")
    print(f"  Silhouette score : {sil:.4f}  (>0.5 = good, >0.7 = excellent)")
    print(f"  Davies-Bouldin   : {db:.4f}  (lower is better)")
    print(f"  Clusters         : {len(unique)}")
    print(f"  Samples          : {len(labels)}")

    if sil > 0.5:
        print("\n  ✓ Strong cross-species clustering — semantic primitives are separable")
    elif sil > 0.25:
        print("\n  ~ Partial clustering — fine-tuning classifier needed")
    else:
        print("\n  ✗ Weak clustering — encoder may not capture cross-species semantics")

    return results
