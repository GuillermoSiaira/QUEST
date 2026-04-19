# Filecoin Open Grant — Application
**QUEST: Decentralized Epoch Archive for Ethereum Consensus Risk**

---

## How to Apply

**URL:** https://github.com/filecoin-project/devgrants/issues/new?template=open-grant-proposal.md  
**Category:** Open Grant (up to $50K, applications accepted on a rolling basis)  
**Grant type:** Open Grant Proposal  
**Wallet (FIL/USDC):** 0xBb3272F387dE5A2c2e3906d24EfaC460a7013f2C

---

## Application (ready to paste as GitHub issue)

**Title:**
```
Open Grant Proposal: QUEST — Decentralized Epoch Archive for Ethereum Consensus Risk Data
```

---

### Project Name
QUEST — Macroprudential Oracle for Ethereum

### Proposer
GuillermoSiaira — guillermosiaira@gmail.com  
GitHub: https://github.com/GuillermoSiaira/QUEST

### Project Description

QUEST is a macroprudential oracle that monitors systemic risk in the Ethereum consensus layer.
Every epoch (~6.4 minutes), it captures a full snapshot of the Beacon chain state — slashings,
validator rewards, participation rate, Grey Zone Score — and persists it across three independent
storage layers simultaneously:

1. **Firestore** — hot storage for real-time API access
2. **IPFS via Pinata** — content-addressed, publicly accessible via `gateway.pinata.cloud`
3. **Filecoin via Lighthouse** — storage proof, verifiable on-chain

The Filecoin layer is critical: it provides cryptoeconomic proof that each epoch snapshot existed
at a specific point in time and has not been tampered with. This transforms QUEST from a monitoring
tool into a **verifiable historical record** of Ethereum's systemic health — the kind of audit
trail that regulators, researchers, and DeFi protocols can rely on.

**Live proof:** Every epoch since 2026-04-19 is stored on Filecoin. Example:
- Epoch 442200 → `files.lighthouse.storage/viewFile/QmUiWmbAnE8xQTzvtiUwTA29iiDYMFSNT3CmS5KL7LPdQL`
- Full viewer: `quest-orcin-sigma.vercel.app/epoch/442200`

### Value to the Filecoin Ecosystem

QUEST demonstrates a concrete, production use case for Filecoin as infrastructure for
financial risk data:

1. **Domain-specific archival at scale** — Ethereum produces ~225 epochs/day. QUEST archives
   each one as an independently verifiable JSON snapshot. At current rate: ~82,000 files/year,
   each 0.7–1 KB, growing indefinitely as long as Ethereum runs.

2. **Verifiable public goods** — The Grey Zone Score is a macroprudential signal. Having it
   backed by Filecoin storage proofs makes it auditable by third parties without trusting
   QUEST's infrastructure.

3. **Reference implementation** — QUEST is the first oracle to use Filecoin as an audit
   layer for consensus-layer risk data. The pattern (off-chain computation → Filecoin proof →
   on-chain CID publication) is replicable by any oracle or data provider.

4. **EigenLayer integration path** — QUEST is being upgraded to an EigenLayer AVS. The Filecoin
   CID will be published on-chain in `QUESTCore.sol` each epoch, creating a trustless link
   between the Filecoin storage proof and the Ethereum state.

### Deliverables

**M1 — Historical backfill (4 weeks, $8K)**
- Pin all 1,200+ existing epochs (2026-03-XX to 2026-04-19) to Filecoin via Lighthouse
- Script: `scripts/backfill_filecoin.py` — iterates Firestore, uploads missing epochs, updates `filecoin_cid`
- Output: 100% of QUEST history on Filecoin, verifiable via the epoch viewer

**M2 — On-chain CID publication (4 weeks, $12K)**
- Extend `QUESTCore.sol`: `publishEpochCID(epoch, ipfsCid, filecoinCid)` — callable by AVS operator
- AVS node publishes CID on-chain after each Filecoin upload
- Creates trustless audit trail: Ethereum block → Filecoin CID → epoch snapshot

**M3 — Public archive dashboard (4 weeks, $10K)**
- Extend `/epoch/[n]` viewer with Filecoin deal status (storage provider, deal expiry, on-chain proof)
- Add `/archive` page: searchable index of all epochs with storage proof links
- API endpoint: `GET /api/epoch/{n}/proof` — returns IPFS CID, Filecoin CID, deal status, on-chain tx

**Total requested: $30,000**

### Development Roadmap

| Milestone | Deliverable | Duration | Cost |
|---|---|---|---|
| M1 | Historical backfill — 1,200+ epochs to Filecoin | 4 weeks | $8,000 |
| M2 | On-chain CID publication in QUESTCore.sol | 4 weeks | $12,000 |
| M3 | Archive dashboard + proof API endpoint | 4 weeks | $10,000 |

### Budget Breakdown

| Item | Cost |
|---|---|
| Development (solo, 3 months) | $24,000 |
| Lighthouse storage costs (ongoing, ~$0.01/epoch) | $3,000 |
| Infrastructure (Cloud Run, Firestore) | $3,000 |
| **Total** | **$30,000** |

### Team

**Guillermo Siaira** — solo builder  
- Built QUEST end-to-end: risk engine, FastAPI backend, AVS node (Go), smart contracts (Solidity/Foundry), Next.js dashboard
- All components running in production (GCP Cloud Run + Vercel)
- Contact: guillermosiaira@gmail.com

### Additional Information

- **Live dashboard:** https://quest-orcin-sigma.vercel.app
- **GitHub:** https://github.com/GuillermoSiaira/QUEST
- **Forum post (EigenLayer):** https://forum.eigenlayer.xyz/t/quest-macroprudential-oracle-avs-for-ethereum-strategic-grant-proposal/14793
- **QUESTCore.sol (Sepolia):** https://sepolia.etherscan.io/address/0xE81C6B16ecbEC8E4Aadc963e82B27c10c4ab10e7
- **Example Filecoin proof:** https://files.lighthouse.storage/viewFile/QmUiWmbAnE8xQTzvtiUwTA29iiDYMFSNT3CmS5KL7LPdQL

---

## Checklist antes de publicar

- [ ] Ir a https://github.com/filecoin-project/devgrants/issues/new?template=open-grant-proposal.md
- [ ] Pegar el contenido de "Application" arriba
- [ ] Verificar que el link de Filecoin proof sea del epoch más reciente
- [ ] Submit como GitHub issue
