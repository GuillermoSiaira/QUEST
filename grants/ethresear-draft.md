# QUEST: A Macroprudential Oracle for Ethereum's Consensus Layer

> Draft para ethresear.ch — pendiente de publicación

**TL;DR:** We identify a structural gap in Lido's `safe_border.py` where slashing debt accumulates silently while MEV rewards mask technical insolvency. We call this the *Grey Zone*. QUEST is a live oracle (Sepolia) that publishes a Grey Zone Score every epoch (~384s), backed by a 3-layer decentralized storage stack and an EigenLayer AVS node. We discuss how this signal can be consumed by autonomous agents and QUEST-aware protocols to enable macroprudential coordination in DeFi.

---

## 1. The Problem: Silent Slashing Debt

Lido's `safe_border.py` oracle has a structural early-return condition: when the Consensus Layer rebase is positive, the function skips slashing debt verification entirely. The rationale is intuitive — if net rewards are positive, the protocol is healthy. But this logic breaks down under a specific condition we call the **Grey Zone**.

In the Grey Zone, MEV rewards and consensus layer issuance are large enough to produce a positive net rebase *even as slashing losses accumulate* among remaining validators. The protocol appears healthy to `safe_border.py`. Slashing liabilities compound. No coordination signal is emitted.

This is not a theoretical edge case. It is a structural feature of any sufficiently large liquid staking protocol operating under EIP-1559 burn dynamics and a competitive MEV market.

---

## 2. Formal Definition

Let:

- $L_s$ = gross slashing loss (ETH) in epoch $e$
- $R_{cl}$ = consensus layer rewards (ETH) in epoch $e$
- $R_{mev}$ = MEV rewards / burned ETH proxy in epoch $e$

We define the **Grey Zone Score**:

$$\text{GZS}(e) = \frac{L_s}{R_{cl} + R_{mev}}$$

With risk classification:

| Score | State | Interpretation |
|---|---|---|
| < 0.5 | `HEALTHY` | Normal operation |
| 0.5 – 1.0 | `GREY_ZONE` | Slashing masked by rewards; `safe_border.py` bypass possible |
| ≥ 1.0 | `CRITICAL` | Losses exceed total rewards |

Gross slashing loss is computed as the maximum of two penalty components per the Bellatrix consensus spec:

**Initial penalty (immediate):**
$$P_{initial} = \frac{\text{effective\_balance}}{32}$$

**Midterm penalty (proportional, future):**
$$P_{midterm} = \text{effective\_balance} \times \frac{3 \times \text{total\_slashed\_in\_window}}{\text{total\_active\_balance}}$$

$$L_s = \max(P_{initial}, P_{midterm})$$

where `PROPORTIONAL_SLASHING_MULTIPLIER_BELLATRIX = 3` per the consensus spec.

---

## 3. Architecture

QUEST is designed as a **permissionless macroprudential oracle** — it emits signals but does not coerce. Protocols opt-in, which improves their risk-adjusted reputation without requiring governance approval.

```
Ethereum Mainnet (Beacon + Execution Layer)
        ↓
risk-engine (Python / aiohttp) — polls every 60s
        ├─ Beacon REST: slashings, balances, participation rate
        └─ Alchemy: EIP-1559 burn, gas, Lido TVL
        ↓
EpochSnapshot → Grey Zone Score (lrt_risk_model.py)
        ├─ FastAPI (GCP Cloud Run) — public REST + WebSocket
        ├─ Firestore (hot, <100ms reads)
        ├─ IPFS / Pinata (content-addressed)
        └─ Filecoin / Lighthouse (verifiable storage proofs)
        ↓
AVS Node (Go / EigenLayer patterns)
        └─ QUESTCore.sol on Sepolia — every ~384s
```

**On-chain data structure (QUESTCore.sol):**

```solidity
struct EpochMetrics {
    uint64  epoch;
    uint256 greyZoneScore;       // scaled 1e18
    uint256 grossSlashingLossGwei;
    uint256 clRewardsGwei;
    uint256 burnedEthGwei;
    uint32  participationRate;   // scaled 1e4
    RiskLevel riskLevel;         // HEALTHY | GREY_ZONE | CRITICAL
    bytes32 dataHash;            // keccak256 for AVS verification
    uint64  reportedAt;
}
```

**Live contracts (Sepolia):**
- `QUESTCore.sol`: `0xE81C6B16ecbEC8E4Aadc963e82B27c10c4ab10e7`
- `QUESTAwareProtocol.sol` (reference): `0xD693C783AbDCe3B53b2C33D8fEB0ff4E70f12735`

**Live data:** 1,200+ epochs captured since March 2026. Public API: `quest-api-oo2ixbxsba-uc.a.run.app`. Dashboard: `quest-orcin-sigma.vercel.app`.

---

## 4. The PMC Signal: A 5-Dimensional Risk Vector

Beyond the scalar Grey Zone Score, QUEST publishes a **PMC (Polynomial Monetary Control) signal** — a vector $\theta \in [0, 10000]^5$ capturing orthogonal risk dimensions every epoch:

| Dimension | Meaning |
|---|---|
| $\theta_{risk}$ | Slashing / reward ratio |
| $\theta_{gas}$ | Gas market pressure |
| $\theta_{latency}$ | Beacon data propagation delay |
| $\theta_{finality}$ | Finality risk (participation rate) |
| $\theta_{incentives}$ | MEV / issuance imbalance |

This vector is designed to be composable: protocols can weight dimensions differently according to their specific risk tolerance. A lending protocol may weight $\theta_{risk}$ heavily; a DEX may weight $\theta_{gas}$ and $\theta_{latency}$.

This is analogous to how central banks publish multiple macroprudential indicators (capital adequacy ratios, liquidity coverage ratios) rather than a single number — different actors in the financial system consume different dimensions of the signal.

---

## 5. Agent Economy Implications

The macroprudential framing is deliberate. DeFi lacks the coordination layer that central banks and the BIS provide in traditional finance: a neutral signal emitter that protocols can optionally consume to adjust behavior before systemic risk materializes.

QUEST is designed to fill this gap. `QUESTAwareProtocol.sol` is a reference implementation demonstrating how a DeFi protocol can read the on-chain signal and activate a defensive mode autonomously — no governance vote, no multisig, no human in the loop.

This opens a design space for **macroprudentially-aware autonomous agents**:

1. An agent monitors GZS every epoch
2. When GZS crosses 0.5 (entering Grey Zone), the agent reduces exposure to LST-collateralized positions
3. When GZS returns to HEALTHY and trend is declining, the agent resumes normal operation
4. The agent's behavior is fully on-chain verifiable — no trust required

The key insight from macroeconomic theory: **systemic risk is a coordination problem, not an information problem**. The data on slashings and rewards is public. What was missing was a standardized, epoch-synchronized signal that agents could coordinate around. QUEST provides that Schelling point.

---

## 6. Current Limitations and Open Questions

**v1 limitations:**
- Single trusted operator (ECDSA, no cryptoeconomic security). Upgrading to full EigenLayer AVS with BLS multi-operator is Phase 5.
- `burned_eth` (EIP-1559) is used as a proxy for MEV rewards. Real MEV-Boost data integration is planned for Phase 5.
- Protocol attribution is live only for Lido (withdrawal vault: `0xb9d7934878b5fb9610b3fe8a5e441701f7ac8e18`). Rocket Pool, EtherFi, Swell, and Kelp require per-minipool/EigenPod registry resolution.

**Open questions for the community:**

1. **Signal normalization:** Should GZS be normalized per-protocol (Lido-specific score vs. aggregate)? Lido's weight in total staked ETH makes the aggregate score heavily Lido-driven today.

2. **Threshold governance:** The 0.5 and 1.0 thresholds are analytically derived but not empirically validated against historical slashing events. Has the community modeled optimal thresholds?

3. **ERC standardization:** We drafted ERC-8033 (oracle standard) and ERC-8004 (agent reputation). Are there overlapping efforts we should coordinate with?

4. **MEV-Boost integration:** What is the cleanest way to get per-epoch MEV reward data on-chain without introducing a new trust assumption?

5. **Agent coordination:** If multiple protocols adopt QUEST signals simultaneously, what are the second-order effects? Could synchronized defensive mode activation itself become a systemic risk?

---

## 7. Next Steps

- **Phase 5 (pending EigenLayer grant):** Full AVS with BLS operators, real MEV-Boost data, on-chain CID publication per epoch.
- **Phase 6 (pending Lido LEGO):** Per-protocol Grey Zone Scores for Lido, Rocket Pool, EtherFi, Swell, Kelp.
- **ERC proposals:** Opening discussion on ERC-8033 and ERC-8004 once the community has reviewed this post.

Code, contracts, and epoch data are open source (MIT): [github.com/GuillermoSiaira/QUEST](https://github.com/GuillermoSiaira/QUEST)

Feedback welcome — especially on the PMC signal design and the open questions above.

---

*Guillermo Siaira — economist and Solidity developer. guillermosiaira@gmail.com*
