"""
Phase 0 dataset downloader.

Downloads labeled animal communication datasets for the BABEL Phase 0 experiment.
Priority: species with KNOWN semantic labels (vervet, prairie dog, cetaceans).

Usage:
    python babel/data/download_datasets.py --target data/raw --datasets all
"""

import argparse
import json
import os
import requests
import zipfile
from pathlib import Path
from tqdm import tqdm


# ─── Dataset registry ──────────────────────────────────────────────────────────

DATASETS = {

    "xeno_canto_alarm": {
        "description": "Bird alarm calls from Xeno-canto API — multiple species, labeled by call type",
        "method": "xeno_canto_api",
        "query": "type:alarm",
        "species_list": ["Corvus brachyrhynchos", "Corvus corax", "Parus major"],
        "max_per_species": 50,
        "primitive_mapping": "ALARM_AERIAL",
        "license": "Creative Commons (various)",
    },

    "xeno_canto_contact": {
        "description": "Bird contact calls from Xeno-canto — affiliation/cohesion signals",
        "method": "xeno_canto_api",
        "query": "type:contact",
        "species_list": ["Corvus brachyrhynchos", "Parus major", "Sturnus vulgaris"],
        "max_per_species": 50,
        "primitive_mapping": "CONTACT_AFFILIATION",
        "license": "Creative Commons (various)",
    },

    "watkins_cetaceans": {
        "description": "Watkins Marine Mammal Sound Database — cetacean calls",
        "method": "watkins",
        "url": "https://cis.whoi.edu/science/B/whalesounds/",
        "species_list": ["Tursiops truncatus", "Physeter macrocephalus"],
        "note": "Manual download required — visit URL and download species ZIP files",
        "primitive_mapping": "CONTACT_AFFILIATION",
        "license": "Free for research",
    },

    "esp_huggingface": {
        "description": "Earth Species Project NatureLM training subset on HuggingFace",
        "method": "huggingface",
        "repo_id": "EarthSpeciesProject/NatureLM-audio-training",
        "subset": "small",
        "note": "Requires: pip install datasets huggingface_hub",
        "license": "Non-commercial research only",
    },

    "vervet_alarm": {
        "description": "Vervet monkey alarm calls — eagle / leopard / snake (Cheney & Seyfarth)",
        "method": "manual",
        "sources": [
            "https://www.tierstimmenarchiv.de (search: Chlorocebus pygerythrus)",
            "https://www.macaulaylibrary.org (search: vervet monkey alarm)",
            "Contact: cheney@sas.upenn.edu or seyfarth@sas.upenn.edu for original recordings",
        ],
        "primitive_mapping": {
            "eagle": "ALARM_AERIAL",
            "leopard": "ALARM_GROUND",
            "snake": "ALARM_SNAKE",
        },
        "note": "Gold standard dataset. Labels are ground-truth semantic primitives.",
        "license": "Request from authors",
    },

    "prairie_dog_vocabulary": {
        "description": "Prairie dog alarm calls with encoded intruder descriptors (Slobodikoff)",
        "method": "manual",
        "sources": [
            "Slobodikoff lab: http://www.nau.edu/biology/faculty/slobodikoff/",
            "Published supplementary: DOI 10.1016/j.anbehav.2009.04.009",
        ],
        "primitive_mapping": {
            "hawk": "ALARM_AERIAL",
            "coyote": "ALARM_GROUND",
            "human": "ALARM_GROUND",
            "food": "FOOD_CALL",
        },
        "note": "Most semantically rich known animal language. Contains shape/color/speed encoding.",
        "license": "Request from Slobodikoff lab",
    },
}


# ─── Downloaders ───────────────────────────────────────────────────────────────

def download_xeno_canto(dataset_config: dict, target_dir: Path):
    """Download recordings via Xeno-canto API v2."""
    api_base = "https://xeno-canto.org/api/2/recordings"
    target_dir.mkdir(parents=True, exist_ok=True)
    manifest = []

    for species in dataset_config["species_list"]:
        query = f"sp:\"{species}\" {dataset_config['query']}"
        params = {"query": query, "page": 1}
        resp = requests.get(api_base, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        recordings = data.get("recordings", [])[:dataset_config["max_per_species"]]

        print(f"  {species}: {len(recordings)} recordings found")
        species_dir = target_dir / species.replace(" ", "_").lower()
        species_dir.mkdir(exist_ok=True)

        for rec in tqdm(recordings, desc=f"  Downloading {species[:20]}"):
            audio_url = f"https:{rec['file']}"
            filename = f"{rec['id']}_{rec['en'].replace(' ', '_')}.mp3"
            out_path = species_dir / filename
            if out_path.exists():
                continue
            try:
                r = requests.get(audio_url, timeout=30, stream=True)
                with open(out_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                manifest.append({
                    "path": str(out_path),
                    "species": species,
                    "call_type": rec.get("type", ""),
                    "primitive": dataset_config["primitive_mapping"],
                    "source": "xeno_canto",
                    "xc_id": rec["id"],
                })
            except Exception as e:
                print(f"    Failed {rec['id']}: {e}")

    manifest_path = target_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  Manifest: {manifest_path} ({len(manifest)} records)")
    return manifest


def download_huggingface_subset(dataset_config: dict, target_dir: Path):
    """Download a small subset from HuggingFace ESP dataset."""
    try:
        from datasets import load_dataset
    except ImportError:
        print("  Install: pip install datasets")
        return

    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Loading {dataset_config['repo_id']} (streaming, first 200 samples)...")
    ds = load_dataset(dataset_config["repo_id"], streaming=True, split="train")
    manifest = []

    for i, sample in enumerate(ds):
        if i >= 200:
            break
        out_path = target_dir / f"esp_{i:04d}.wav"
        # Save audio array
        import soundfile as sf
        import numpy as np
        audio = np.array(sample["audio"]["array"])
        sr = sample["audio"]["sampling_rate"]
        sf.write(str(out_path), audio, sr)
        manifest.append({
            "path": str(out_path),
            "species": sample.get("species", "unknown"),
            "label": sample.get("label", ""),
            "source": "esp_huggingface",
        })

    manifest_path = target_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  Saved {len(manifest)} samples")
    return manifest


def print_manual_instructions(dataset_config: dict, name: str):
    print(f"\n  [{name}] Manual download required:")
    print(f"  {dataset_config['description']}")
    for src in dataset_config.get("sources", []):
        print(f"    → {src}")
    print(f"  Primitive mapping: {dataset_config.get('primitive_mapping')}")
    note = dataset_config.get("note", "")
    if note:
        print(f"  Note: {note}")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="BABEL Phase 0 dataset downloader")
    parser.add_argument("--target", default="babel/data/raw", help="Output directory")
    parser.add_argument(
        "--datasets", default="auto",
        help="Comma-separated dataset keys, or 'auto' (skip manual-only), or 'all'"
    )
    args = parser.parse_args()

    target = Path(args.target)
    target.mkdir(parents=True, exist_ok=True)

    auto_datasets = ["xeno_canto_alarm", "xeno_canto_contact", "esp_huggingface"]
    if args.datasets == "auto":
        to_download = auto_datasets
    elif args.datasets == "all":
        to_download = list(DATASETS.keys())
    else:
        to_download = [d.strip() for d in args.datasets.split(",")]

    print(f"\nBABEL Phase 0 — Dataset Download")
    print(f"Target: {target.resolve()}\n")

    for name in to_download:
        cfg = DATASETS.get(name)
        if not cfg:
            print(f"Unknown dataset: {name}")
            continue

        print(f"\n[{name}] {cfg['description']}")
        method = cfg["method"]
        ds_dir = target / name

        if method == "xeno_canto_api":
            download_xeno_canto(cfg, ds_dir)
        elif method == "huggingface":
            download_huggingface_subset(cfg, ds_dir)
        elif method == "manual":
            print_manual_instructions(cfg, name)
        elif method == "watkins":
            print_manual_instructions(cfg, name)
        else:
            print(f"  Unknown method: {method}")

    print("\n✓ Done. Run the Phase 0 notebook next:")
    print("  jupyter notebook babel/notebooks/phase0_embedding_explorer.ipynb")


if __name__ == "__main__":
    main()
