# ⚡ Tesis Escasez y Resiliencia — Dashboard

🌐 **Language / Idioma:** [English](README.md) | Español

**[→ Ver el dashboard en vivo](https://josevilar-qbioai.github.io/escasez-macro-dashboard/)**

Dashboard de validación macro de la tesis de inversión *Cartera Escasez y Resiliencia*, actualizado automáticamente con datos de Yahoo Finance.

---

## Qué muestra

### ⚡ Score ESCASEZ
Indicador compuesto 0–100% calculado a partir de **12 señales binarias** agrupadas por pilar de la tesis. Mide en tiempo real si el entorno macro es favorable a la hipótesis de inversión.

| Estado | Score | Significado |
|--------|-------|-------------|
| 🟢 TESIS EN MARCHA | ≥ 65% | Todos los pilares alineados |
| 🟡 SEÑALES MIXTAS | 40–64% | Entorno parcialmente favorable |
| 🔴 TESIS DÉBIL | < 40% | Modo defensivo |

### 🔴🟢 Correlación SOX / Cobre
Detector de cambio de paradigma tecnológico. Compara el momentum mensual de los semiconductores (SOX) con el del cobre:

| Estado | Condición | Acción |
|--------|-----------|--------|
| 🟢 ERA DE CONSTRUCCIÓN | SOX ↑ y Cobre ↑ | Tesis completa en marcha |
| 🔴 DIVERGENCIA · ALERTA | SOX ↑ / Cobre ↓ | La IA miniaturiza — reducir metales |
| 🟡 ESCASEZ FÍSICA | SOX ↓ / Cobre ↑ | Metales fuertes, esperar rebote SOX |
| 🔴 CONTRACCIÓN | SOX ↓ y Cobre ↓ | Modo defensivo |

### 📊 Señales por pilar

**Autoreplicación IA**
- 📡 SOX Semiconductores — proxy K y γ, capex IA adelantado
- 💻 NASDAQ Tech — momentum tecnológico global
- 🤖 ROBO Robótica — Ola 2: automatización física
- ⚛ QTUM Computación Cuántica — Ola 3/4: post-silicio

**Escasez Digital**
- ₿ BTC momentum — reserva de valor programada
- ₿ BTC vs NASDAQ — fuerza relativa del bitcoin

**Energía / Grid**
- ⚛️ Uranio (Cameco) — energía firme 24/7 para IA
- ⚡ XLU Utilities — PPAs con hyperscalers

**Escasez Física**
- 🟠 Cobre — electrificación y robótica
- 🥇 Oro — refugio ante devaluación fiat

**Resiliencia**
- 📈 Spread 10Y−13W — salud de la curva de tipos
- 😰 VIX — volatilidad implícita del mercado

---

## Modelo matemático

```
V(t) = Capital × (1+r)ᵗ × Φ_L(t) / Φ_L(0)

Φ_L(t) = 1 + K / (1 + e^(−γ·(t−t₀)))
```

Donde `Φ_L(t)` es la función logística de adopción tecnológica que captura la aceleración no lineal del crecimiento cuando la IA entra en fase de autorreplicación.

---

## Actualización

El dashboard se regenera automáticamente con cada push mediante GitHub Actions. Los datos macro se descargan de Yahoo Finance.

---

*Jose Vilar · UOC Data Science · 2026*
