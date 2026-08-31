# ⚡ Scarcity & Resilience Thesis — Dashboard

🌐 **Language / Idioma:** English | [Español](README_ES.md)

**[→ View live dashboard](https://josevilar-qbioai.github.io/escasez-macro-dashboard/)**

Macro validation dashboard for the *Scarcity and Resilience* investment thesis, updated automatically with Yahoo Finance data.

---

## What it shows

### ⚡ SCARCITY Score
Composite indicator 0–100% calculated from **12 binary signals** grouped by thesis pillar. Measures in real time whether the macro environment is favourable to the investment hypothesis.

| Status | Score | Meaning |
|--------|-------|---------|
| 🟢 THESIS RUNNING | ≥ 65% | All pillars aligned |
| 🟡 MIXED SIGNALS | 40–64% | Partially favourable environment |
| 🔴 WEAK THESIS | < 40% | Defensive mode |

### 🔴🟢 SOX / Copper Correlation
Technological paradigm-shift detector. Compares the monthly momentum of semiconductors (SOX) with copper:

| Status | Condition | Action |
|--------|-----------|--------|
| 🟢 CONSTRUCTION ERA | SOX ↑ and Copper ↑ | Full thesis running |
| 🔴 DIVERGENCE · ALERT | SOX ↑ / Copper ↓ | AI miniaturising — reduce metals |
| 🟡 PHYSICAL SCARCITY | SOX ↓ / Copper ↑ | Strong metals, wait for SOX rebound |
| 🔴 CONTRACTION | SOX ↓ and Copper ↓ | Defensive mode |

### 📊 Signals by pillar

**AI Self-Replication**
- 📡 SOX Semiconductors — proxy K and γ, forward AI capex
- 💻 NASDAQ Tech — global tech momentum
- 🤖 ROBO Robotics — Wave 2: physical automation
- ⚛ QTUM Quantum Computing — Wave 3/4: post-silicon

**Digital Scarcity**
- ₿ BTC momentum — programmed store of value
- ₿ BTC vs NASDAQ — Bitcoin relative strength

**Energy / Grid**
- ⚛️ Uranium (Cameco) — firm 24/7 energy for AI
- ⚡ XLU Utilities — PPAs with hyperscalers

**Physical Scarcity**
- 🟠 Copper — electrification and robotics
- 🥇 Gold — hedge against fiat debasement

**Resilience**
- 📈 Spread 10Y−13W — yield curve health
- 😰 VIX — implied market volatility

---

## Mathematical model

```
V(t) = Capital × (1+r)ᵗ × Φ_L(t) / Φ_L(0)

Φ_L(t) = 1 + K / (1 + e^(−γ·(t−t₀)))
```

Where `Φ_L(t)` is the logistic technology-adoption function that captures the non-linear growth acceleration when AI enters the self-replication phase.

---

## Updates

The dashboard is regenerated automatically on every push via GitHub Actions. Macro data is downloaded from Yahoo Finance.

---

*Jose Vilar · UOC Data Science · 2026*
