#!/bin/bash
# BABEL Phase 0 — GCP VM setup script
# Instance: n1-standard-4 + T4 GPU (~$0.35/hr)
# Run once after SSH into the VM.

set -e

echo "=== BABEL GCP Setup ==="

# 1. Update & install system deps
sudo apt-get update -q
sudo apt-get install -y ffmpeg libsndfile1 git python3-pip python3-venv

# 2. Create venv
python3 -m venv ~/babel-env
source ~/babel-env/bin/activate

# 3. Clone repo (replace with your repo URL)
REPO_URL="https://github.com/GuillermoSiaira/QUEST.git"
if [ ! -d "QUEST" ]; then
  git clone "$REPO_URL"
fi
cd QUEST
git checkout feat/babel

# 4. Install Python deps
pip install --upgrade pip
pip install -r babel/requirements.txt

# 5. Verify GPU
python3 -c "import torch; print('CUDA:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"

# 6. Download datasets (auto = Xeno-canto + HuggingFace, skips manual-only)
echo ""
echo "Downloading datasets..."
python3 babel/data/download_datasets.py --datasets auto --target babel/data/raw

# 7. Run Phase 0
echo ""
echo "Running Phase 0 embedding explorer..."
python3 babel/notebooks/phase0_embedding_explorer.py

echo ""
echo "=== Done. Check babel/data/embeddings/ for results ==="
echo "Copy results to Cloud Storage:"
echo "  gsutil cp -r babel/data/embeddings/ gs://YOUR_BUCKET/babel/phase0/"
