# Macroprudential Signals for Autonomous Agents: A Utility Framework for Systemic Risk Coordination in DeFi

*Guillermo Siaira — guillermosiaira@gmail.com*

---

## TL;DR

In traditional finance, central banks emit macroprudential signals — capital adequacy ratios, stress test results, systemic risk indicators — that financial institutions consume voluntarily to calibrate their exposure. DeFi has no equivalent: agents optimize locally, and systemic risk accumulates silently until it crystallizes.

We propose a utility-theoretic framework that fills this gap. If DeFi agents encode a systemic risk signal into their utility functions, macroprudential coordination becomes **individually rational** rather than a collective-good problem requiring enforcement. We introduce the **Grey Zone Score (GZS)** — motivated by a specific structural gap in Lido's oracle — as a concrete instantiation of such a signal, and show that QUEST-aware agents reduce systemic exposure as a dominant strategy, without any external rule.

---

## 1. The Coordination Problem

DeFi agents — automated vaults, lending protocols, LST-collateralized positions, EigenLayer operators — optimize for local utility: yield, collateral efficiency, fee revenue. This is individually rational. The problem is structural: no agent has an incentive to reduce exposure in response to systemic risk signals that are diffuse, lagged, or simply absent.

This is the classic free-rider structure, and it is why coercive macroprudential regulation exists in traditional finance. In TradFi, a bank that ignores stress signals faces regulatory sanction. In DeFi, coercion is unavailable by design.

The standard response is governance — multisig thresholds, DAO votes, emergency pause mechanisms. But governance is slow, politically costly, and requires a human in the loop at precisely the moment when speed matters most.

We propose a different approach: **design agents whose utility functions already encode systemic risk, so that reducing exposure when the system is stressed is the individually optimal action — no governance required.**

---

## 2. The Motivating Case: Lido's Grey Zone

To ground this abstractly stated problem, consider a concrete structural gap in Lido Oracle's `safe_border.py`.

The oracle's core safety logic evaluates whether the protocol should enter "bunker mode" — a protective state that restricts withdrawals during periods of abnormal slashing. The key function, `_get_safe_border_epoch()`, contains the following early-return condition (paraphrased):

```python
if not is_bunker_mode:
    return default_border  # skips _get_associated_slashings_border_epoch()
```

The rationale is intuitive: if the protocol is not already in bunker mode and the consensus layer rebase is positive, slashing losses are presumably being absorbed by rewards. No further analysis is needed.

This logic breaks down under a specific condition we call the **Grey Zone**: a period where MEV rewards and CL issuance are large enough to produce a positive net rebase *while slashing losses accumulate among remaining validators*. The oracle sees a healthy protocol. The slashing debt is real. No coordination signal is emitted.

This is not a theoretical edge case. It is a structural feature of any sufficiently large liquid staking protocol operating in a competitive MEV environment: high MEV activity precisely correlates with the network conditions (high block value, validator competition) that also elevate slashing risk.

*Note: We submitted this finding to Lido's security program. The response characterized it as "research of interest" rather than an immediately exploitable vulnerability — which is accurate. The Grey Zone is a structural gap, not a zero-day. Its significance is macroprudential, not acute.*

---

## 3. The Grey Zone Score

We formalize the Grey Zone condition with a scalar metric:

$$\text{GZS}(e) = \frac{L_s}{R_{cl} + R_{el}}$$

Where:
- $L_s$ = gross slashing loss in epoch $e$, computed as the maximum of the immediate penalty ($\text{effective\_balance} / 32$) and the midterm proportional penalty per the Bellatrix consensus spec
- $R_{cl}$ = consensus layer rewards in epoch $e$ (balance delta across all validators)
- $R_{el}$ = execution layer activity proxy in epoch $e$ — in v1, the EIP-1559 base fee burn, used as a signal correlated with MEV activity. Real MEV-Boost data would improve precision; the proxy is sufficient for macroprudential order-of-magnitude detection.

**Interpretation:**

| GZS | State | Meaning |
|---|---|---|
| < 0.5 | `HEALTHY` | Normal operation |
| 0.5 – 1.0 | `GREY_ZONE` | Slashing masked by rewards; oracle bypass possible |
| ≥ 1.0 | `CRITICAL` | Losses exceed total rewards |

GZS is published every epoch (~384 seconds) by **QUEST**, a live monitor we run as part of this proposal ([dashboard](https://quest-orcin-sigma.vercel.app), [API](https://quest-api-oo2ixbxsba-uc.a.run.app), [code](https://github.com/GuillermoSiaira/QUEST)). The signal is designed to be consumed by agents, not humans — it is epoch-synchronized, scalar, and publicly verifiable.

---

## 4. A Utility Framework for Systemic-Risk-Aware Agents

### 4.1 The Core Idea

The standard DeFi agent maximizes expected return. We propose agents that maximize **risk-adjusted return**, where the risk term is parameterized by the systemic risk signal:

$$U = E(R) - \frac{\lambda}{2} \cdot \sigma^2(\text{GZS})$$

This is a mean-variance utility function in the Markowitz tradition. The non-standard element is $\sigma^2(\text{GZS})$: systemic variance is not constant, nor estimated from historical return data. It is a function of the current epoch's GZS — a forward-looking, oracle-provided measure of systemic stress.

### 4.2 Why Exponential?

We define:

$$\sigma^2(\text{GZS}) = \sigma_{base}^2 \cdot e^{k \cdot \text{GZS}}$$

A linear specification would imply that each unit increase in GZS adds equal systemic variance. But systemic risk doesn't work that way: near GZS = 1.0, the slashing/rewards ratio approaches 1, meaning the protocol's ability to absorb further slashing events is nearly exhausted. This is a regime shift, not a linear accumulation — the variance structure at the tail is qualitatively different from the variance structure in normal conditions.

The exponential form encodes this: variance accelerates as GZS approaches the critical threshold, reflecting the tail-risk structure of cascading liquidations. The parameter $k = \ln(10)$ is calibrated so that variance at GZS = 1.0 is 10× variance at GZS = 0.0.

### 4.3 Exposure as Output

Define the agent's **exposure ratio** — the fraction of its portfolio allocated to LST-collateralized positions — as:

$$\alpha = \max\left(0,\ \frac{U}{E(R)}\right) = \max\left(0,\ 1 - \frac{\lambda \cdot \sigma^2(\text{GZS})}{2 \cdot E(R)}\right)$$

This maps GZS to a continuous exposure target in $[0, 1]$. With reference calibration ($\sigma_{base} = 0.05$, $k = \ln 10$, $\lambda = 0.6$):

| GZS | Exposure |
|-----|----------|
| 0.0 | 90% |
| 0.5 | ~68% |
| 0.7 | ~50% |
| 1.0 | 0% |

The 50% exposure point falls near GZS ≈ 0.7, not at the midpoint 0.5 — a consequence of the exponential form that concentrates the reduction where tail risk is highest. These values are illustrative; optimal calibration across heterogeneous agents is an open question (§5).

---

## 5. The Coordination Result

### 5.1 Individual Rationality

An agent maximizing $U = E(R) - \frac{\lambda}{2}\sigma^2(\text{GZS})$ will reduce exposure as GZS rises by construction. At the GZS level where $\frac{\lambda}{2}\sigma^2(\text{GZS}) \geq E(R)$, utility is non-positive and the optimal exposure is zero.

No external rule is invoked. The agent's own utility function is the policy. This removes the coordination problem at the level of the individual agent: the macroprudential signal is already priced into the agent's optimal behavior.

### 5.2 The Inverted Free-Rider Structure

In TradFi, the free-rider problem in systemic risk is: reducing exposure is costly to the individual but beneficial to the system. Each agent prefers that others reduce exposure first, producing collective inaction.

In a world of QUEST-aware agents, this structure inverts. For any agent with $\lambda$ calibrated so that $c < d$ (where $c$ is foregone yield from reducing exposure and $d$ is expected loss from systemic cascading), reducing exposure is the **dominant strategy**: it is optimal regardless of what other agents do.

**Informal Nash sketch:** Two QUEST-aware agents $A, B$ with identical calibration face a binary choice at GZS above their individual threshold: `reduce` or `maintain`. Since reducing exposure is dominant for each agent independently, $(\text{reduce}, \text{reduce})$ is the unique Nash equilibrium. Coordination emerges from individual optimization — no communication, no governance vote, no enforcement required.

This is a deliberately minimal model. Heterogeneous $\lambda$, partial information, and correlated exit dynamics make the picture richer — and we do not claim to have resolved those cases. But the minimal model already establishes that the coordination failure is not inevitable: it is a consequence of the signal being absent from agent utility functions, not of some deeper impossibility.

---

## 6. Open Questions

We are genuinely uncertain about the following and would value community input:

1. **Signal design**: GZS is aggregate (network-wide). Should it be per-protocol? Lido's weight in total staked ETH makes the aggregate score Lido-dominated today. A per-protocol score would be more precise but requires solving the validator attribution problem for Rocket Pool, EtherFi, and others.

2. **Calibration**: The reference parameters ($\sigma_{base}$, $k$, $\lambda$) are analytically chosen, not empirically fitted. What is the appropriate method for calibrating $\lambda$ distributions across a heterogeneous agent population? Is there a mechanism design argument for a canonical $k$?

3. **The $R_{el}$ proxy**: We use EIP-1559 burn as a proxy for MEV activity. This is correlated but imprecise — burned ETH does not go to validators. Real MEV-Boost data would improve the signal. What is the cleanest on-chain path to per-epoch MEV attribution without introducing a new trust assumption?

4. **Threshold governance**: The 0.5 and 1.0 GZS thresholds are analytically motivated but not empirically validated against historical slashing events. Are there historical episodes where a calibrated GZS would have provided early warning?

5. **Agent exit dynamics**: If multiple QUEST-aware agents reduce LST exposure simultaneously, the exit is epoch-synchronized. Depending on liquidity, this could amplify rather than dampen volatility. What is the condition on the distribution of $\lambda$ under which simultaneous reduction is stabilizing?

---

## 7. Implementation Note

A live implementation exists at [github.com/GuillermoSiaira/QUEST](https://github.com/GuillermoSiaira/QUEST):

- **Risk engine** (Python): polls Beacon and Execution layer every epoch, computes GZS, stores to Firestore and Filecoin
- **Public API**: REST + WebSocket at `quest-api-oo2ixbxsba-uc.a.run.app`
- **Dashboard**: live visualization at `quest-orcin-sigma.vercel.app`
- **QUESTAgent.sol**: on-chain implementation of §4 using PRBMath UD60x18 fixed-point arithmetic for the exponential utility function, deployed on Sepolia

The implementation is v1 and centralized — a single operator computes and publishes the signal. Decentralized verification (multi-operator AVS) is the natural next step but is not the subject of this post.

---

## 8. Conclusion

The DeFi coordination problem for systemic risk is not unsolvable. It does not require coercion. It requires agents whose utility functions already encode the signal — so that the individually rational action and the systemically desirable action coincide.

The Grey Zone in Lido Oracle is one concrete case where such a signal was absent and the structural gap exists. GZS is our attempt to formalize it. The mean-variance framework in §4 is our proposal for how agents should consume it.

We are aware this is a minimal model applied to a complex system. We publish it here because the core question — how do autonomous agents coordinate around systemic risk without enforcement? — seems important and underexplored, and because the Ethereum community is better positioned than we are to stress-test the assumptions.

---

*Code and data: [github.com/GuillermoSiaira/QUEST](https://github.com/GuillermoSiaira/QUEST) (MIT)*
*Feedback welcome, especially on §6.*
