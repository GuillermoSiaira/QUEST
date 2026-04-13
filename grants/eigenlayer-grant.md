# EigenLayer Foundation — Grant Application
**QUEST: Macroprudential Oracle AVS for Ethereum**

---

## Dónde presentar

| Canal | URL | Para qué |
|---|---|---|
| Forum post | https://forum.eigenlayer.xyz | Post público — categoría "Project Showcase" |
| Discord | https://discord.gg/eigenlayer | Canal `#grants` o `#builders` — contacto directo con el Grants Team |
| Docs (monitorear) | https://docs.eigenfoundation.org/category/grants | Portal oficial cuando abra |

**Flujo recomendado:**
1. Publicar el one-pager en el forum
2. En Discord: linkear el post y preguntar por el proceso de Strategic Grants
3. Wallet para recibir EIGEN: `0xBb3272F387dE5A2c2e3906d24EfaC460a7013f2C`

---

## One-Pager (listo para publicar)

```
Title: QUEST — Macroprudential Oracle AVS for Ethereum [Strategic Grant Proposal]
```

### Problem

Ethereum's consensus layer has a structural blind spot: individual protocols optimize
for their own UX while creating systemic hidden risk. The clearest example is Lido's
oracle: when MEV rewards exceed slashing losses, the rebase is positive, Bunker Mode
stays off, and withdrawals finalize at 1:1 — even while slashing debt accumulates
silently among remaining stakers. This is Algorithmic Moral Hazard — protocols won't
self-regulate at the cost of their own liquidity.

No on-chain coordination layer exists to signal this risk before it becomes a
liquidation cascade.

### Solution

QUEST is a macroprudential oracle AVS — the on-chain equivalent of a Bank for
International Settlements (BIS) for Ethereum. It computes a Grey Zone Score
(gross_slashing_loss / (cl_rewards + burned_eth)) from live Beacon chain data and
publishes it on-chain as a PMC signal (θ) every epoch (~384s).

DeFi protocols implement IERC8004QuestAware to receive these signals and adjust
defensively before systemic risk materializes — without coercion, purely opt-in.

### What's Already Built

| Component | Status |
|---|---|
| Risk engine (Python, Beacon REST + Alchemy) | ✅ Running on Cloud Run |
| QUESTCore.sol — on-chain oracle | ✅ Sepolia 0xE81C6B16ecbEC8E4Aadc963e82B27c10c4ab10e7 |
| QUESTAwareProtocol.sol — ERC-8004 reference impl | ✅ Sepolia 0xD693C783AbDCe3B53b2C33D8fEB0ff4E70f12735 |
| AVS node (Go) — submits epoch metrics on-chain | ✅ Running on Cloud Run |
| Dashboard (Vercel) — live Grey Zone Score | ✅ Public |

Current architecture: trusted oracle v1 (single ECDSA operator). The grant funds
the upgrade to a proper EigenLayer AVS with a BLS operator set and cryptoeconomic
security.

### Milestone Plan

**M1 — EigenLayer SDK integration (8 weeks)**
Port quest-avs-node from trusted operator to EigenLayer AVS SDK. Implement
ServiceManager, BLS key registration, operator slashing conditions.

**M2 — Operator testnet (4 weeks)**
Launch with 3–5 independent operators on Sepolia. Validate consensus on Grey
Zone Score across operators.

**M3 — Mainnet AVS (4 weeks)**
Deploy QUESTServiceManager on mainnet. Open operator registration. Publish
ERC-8033 signal certified by restaked ETH.

### Why EigenLayer

QUEST needs cryptoeconomic security to be trustworthy as systemic infrastructure —
a single operator is a single point of failure. EigenLayer's restaking model is the
only credible path to decentralized certification of a consensus-layer risk signal.
The security model maps directly: operators stake on the correctness of Grey Zone
Score calculations.

**Contact:** GuillermoSiaira — guillermosiaira@gmail.com
**Wallet:** 0xBb3272F387dE5A2c2e3906d24EfaC460a7013f2C

---

## Links de soporte (adjuntar o linkear en el post)

| Recurso | URL |
|---|---|
| QUESTCore en Etherscan | https://sepolia.etherscan.io/address/0xE81C6B16ecbEC8E4Aadc963e82B27c10c4ab10e7 |
| QUESTAwareProtocol en Etherscan | https://sepolia.etherscan.io/address/0xD693C783AbDCe3B53b2C33D8fEB0ff4E70f12735 |
| Dashboard (live Grey Zone Score) | https://quest-dashboard.vercel.app (confirmar URL) |
| API pública | https://quest-api-299259685359.us-central1.run.app |

---

## Checklist antes de publicar

- [ ] Crear cuenta en forum.eigenlayer.xyz
- [ ] Confirmar URL del dashboard de Vercel
- [ ] Agregar link al repo de GitHub (si está público) o dejarlo privado
- [ ] Revisar que la wallet 0xBb3272F387... tenga nombre/ENS si querés (opcional)
- [ ] Publicar el one-pager en el forum
- [ ] Postear en Discord con link al forum

---

## Otros grants a presentar (siguiente ronda)

### Ethereum Foundation ESP
- URL: https://esp.ethereum.foundation
- Fit: infraestructura de monitoreo de riesgo sistémico para Ethereum
- Ángulo: QUEST como herramienta de salud del consenso layer

### Lido Grants Program
- URL: https://research.lido.fi (categoría Grants)
- Fit: el bug que justifica QUEST es literalmente una vulnerabilidad del oracle de Lido
- Ángulo: QUEST como capa de seguridad externa para detectar Grey Zone antes de que Bunker Mode falle
- Documentación existente: `_LIDO_ORACLE_BUG_BOUNTY_REPORT_DRAFT.pdf`
