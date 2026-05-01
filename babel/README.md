# BABEL
### Bioacoustic Agent Bridging and Embedding Layer

> *"The AGI should be, among other things, a universal interpreter across species."*
> — QUEST Research Appendix VII, 2026

BABEL is a research sub-project of QUEST that builds a **cross-species semantic primitive graph** for animal communication. Where existing tools (NatureLM-audio, CETI) decode one species at a time, BABEL maps functional equivalences **across species** — the R2-D2 layer that was missing.

---

## The core idea

Every communicative act, regardless of species, realizes one of ~9 **semantic primitives**:

```
ALARM_AERIAL · ALARM_GROUND · ALARM_SNAKE
FOOD_CALL · CONTACT_AFFILIATION · DISTRESS
MATING · IDENTITY · LOCATION
```

A vervet monkey's eagle call, an American crow's alarm, and a prairie dog's hawk-whistle all realize `ALARM_AERIAL`. BABEL builds the graph that makes that equivalence explicit, computable, and queryable.

---

## Connection to QUEST

The heterogeneity oracle in QUEST measures **behavioral divergence** among economic agents (Olas Mech, Gnosis Chain). BABEL applies the same mathematical intuition to **communicative divergence** across biological species. The Morris-Shin diagnostic that measures agent homogeneity in prediction markets is the same structure that measures how differently species implement the same semantic primitive.

---

## Phases

| Phase | Goal | Cost | Status |
|---|---|---|---|
| **0** | Validate: do NatureLM embeddings cluster by semantic primitive cross-species? | ~$15 | 🔄 Active |
| **1** | Build labeled graph: 5 species × 9 primitives | ~$100 | Planned |
| **2** | Retrieval API: given signal X → equivalents in species B, C, D | ~$200 | Planned |
| **3** | R2-D2 demo: real-time audio → semantic interpretation + cross-species map | ~$200 | Planned |

---

## Quick start — Phase 0

```bash
# 1. Install deps
pip install -r babel/requirements.txt

# 2. Download datasets (Xeno-canto alarm/contact calls + ESP subset)
python babel/data/download_datasets.py --datasets auto

# 3. Run Phase 0 (works on CPU with synthetic data if no GPU available)
python babel/notebooks/phase0_embedding_explorer.py

# 4. Results in:
#    babel/data/embeddings/phase0_embedding_map.png
#    babel/data/embeddings/phase0_metrics.json
```

On GCP (T4 GPU):
```bash
bash babel/gcp/setup_vm.sh
```

---

## Structure

```
babel/
├── README.md
├── requirements.txt
├── data/
│   ├── download_datasets.py    ← Phase 0 data pipeline
│   └── raw/                    ← downloaded audio (gitignored)
├── notebooks/
│   └── phase0_embedding_explorer.py  ← main Phase 0 script
├── src/
│   ├── encoder.py              ← NatureLM-audio wrapper
│   ├── primitives.py           ← semantic primitive taxonomy
│   ├── graph.py                ← BabelGraph — the cross-species knowledge graph
│   └── visualizer.py           ← UMAP plots + cluster metrics
└── gcp/
    ├── setup_vm.sh             ← GCP T4 VM bootstrap
    └── cost_monitor.py         ← burn rate tracker
```

---

## Key datasets

| Dataset | Species | Labels | Access |
|---|---|---|---|
| Vervet alarm calls (Cheney & Seyfarth) | *C. pygerythrus* | eagle/leopard/snake | Request from authors |
| Prairie dog vocabulary (Slobodikoff) | *C. ludovicianus* | intruder shape/speed/color | Request from lab |
| Xeno-canto alarm/contact calls | Multiple birds | call type | Free API |
| Watkins Marine Mammal DB | Cetaceans | species-level | Free, manual |
| ESP/NatureLM training set | Multi-species | species + task | HuggingFace (non-commercial) |

---

## The AGI connection

The Total Turing Test (Harnad 1991; Saygin et al. 2000) argues that a genuinely general intelligence must be able to communicate across **any** cognitive architecture — not just human ones. BABEL is a step toward operationalizing that: a system that can bridge between communicative systems as divergent as sperm whale codas and vervet alarm barks, finding the common semantic skeleton beneath.

---

## References

- Küçükuncular (2025). *Ethical implications of AI-mediated interspecies communication*. AI & Ethics 5:6379–6391.
- Rutz et al. (2023). *Using machine learning to decode animal communication*. Science 381:152–155.
- Cheney & Seyfarth (1990). *How monkeys see the world*. U. Chicago Press.
- Slobodikoff et al. (2009). *Prairie dog communication*. Animal Behaviour.
- NatureLM-audio (2024). arXiv:2411.07186. Earth Species Project.
