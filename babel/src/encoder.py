"""
NatureLM-audio wrapper — converts raw audio into semantic embeddings.
Model: EarthSpeciesProject/NatureLM-audio (BEATs + Llama 3.1 8B)
"""

import torch
import librosa
import numpy as np
from pathlib import Path
from typing import Union
from transformers import AutoProcessor, AutoModel


NATURELM_MODEL_ID = "EarthSpeciesProject/NatureLM-audio"
SAMPLE_RATE = 16_000
EMBEDDING_DIM = 1024


class BabelEncoder:
    """
    Wraps NatureLM-audio to extract embeddings from animal vocalizations.
    Falls back to BEATs-only if the full model is too heavy for the instance.
    """

    def __init__(self, device: str = "auto", lightweight: bool = False):
        self.device = self._resolve_device(device)
        self.lightweight = lightweight
        self.model = None
        self.processor = None

    def load(self):
        print(f"Loading encoder on {self.device}...")
        if self.lightweight:
            # BEATs-only for CPU/small GPU instances (~300MB)
            from transformers import BertModel, AutoFeatureExtractor
            self.processor = AutoFeatureExtractor.from_pretrained(
                "microsoft/BEATs-iter3-AS2M"
            )
            self.model = AutoModel.from_pretrained(
                "microsoft/BEATs-iter3-AS2M"
            ).to(self.device)
        else:
            # Full NatureLM-audio (~16GB, needs T4 or better)
            self.processor = AutoProcessor.from_pretrained(NATURELM_MODEL_ID)
            self.model = AutoModel.from_pretrained(
                NATURELM_MODEL_ID,
                torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
            ).to(self.device)
        self.model.eval()
        print("Encoder ready.")
        return self

    def encode(self, audio_path: Union[str, Path]) -> np.ndarray:
        """
        Load an audio file and return its embedding vector.
        Returns: np.ndarray of shape (EMBEDDING_DIM,)
        """
        waveform, sr = librosa.load(str(audio_path), sr=SAMPLE_RATE, mono=True)
        inputs = self.processor(
            waveform,
            sampling_rate=SAMPLE_RATE,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
            # Use mean-pooled last hidden state as embedding
            embedding = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()

        return embedding.astype(np.float32)

    def encode_batch(self, audio_paths: list, verbose: bool = True) -> np.ndarray:
        """
        Encode a list of audio files. Returns (N, EMBEDDING_DIM) array.
        """
        from tqdm import tqdm
        embeddings = []
        iterator = tqdm(audio_paths, desc="Encoding") if verbose else audio_paths
        for path in iterator:
            try:
                emb = self.encode(path)
                embeddings.append(emb)
            except Exception as e:
                print(f"  Skipped {path}: {e}")
                embeddings.append(np.zeros(EMBEDDING_DIM, dtype=np.float32))
        return np.array(embeddings)

    @staticmethod
    def _resolve_device(device: str) -> str:
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
            return "cpu"
        return device
