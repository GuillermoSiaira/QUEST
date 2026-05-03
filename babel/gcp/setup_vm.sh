#!/bin/bash
# BABEL Phase 0 — GCP T4 setup + NatureLM runner
# Instance: n1-standard-4 + T4 GPU (16GB VRAM) ~$0.35/hr preemptible
# Run once after SSH into the VM.

set -e
echo "=== BABEL GCP Setup ==="

# 1. System deps
sudo apt-get update -q
sudo apt-get install -y ffmpeg libsndfile1 git python3-pip python3-venv

# 2. Venv
python3 -m venv ~/babel-env
source ~/babel-env/bin/activate

# 3. Clone repo + checkout branch
if [ ! -d "QUEST" ]; then
  git clone https://github.com/GuillermoSiaira/QUEST.git
fi
cd QUEST
git checkout feat/babel

# 4. Deps (torch CUDA + bitsandbytes para 8-bit quantization)
pip install --upgrade pip
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r babel/requirements.txt
pip install bitsandbytes accelerate

# 5. Verificar GPU
python3 -c "import torch; print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE')"

# 6. Generar audio dataset (si no existe)
if [ ! -f "babel/data/raw/esp_hf/manifest.json" ]; then
  echo "Generando dataset de audio..."
  python3 babel/data/download_hf.py
fi

# 7. Correr Phase 0 NatureLM
echo ""
echo "=== Corriendo Phase 0 NatureLM-audio ==="
python3 babel/notebooks/phase0_naturelm.py

# 8. Copiar resultados a Cloud Storage
echo ""
echo "=== Copiando resultados ==="
gsutil cp babel/data/embeddings/phase0_naturelm_map.png gs://babel-results-$(date +%Y%m%d)/
gsutil cp babel/data/embeddings/naturelm_embeddings.npy gs://babel-results-$(date +%Y%m%d)/
echo "Listo. Resultados en gs://babel-results-$(date +%Y%m%d)/"
