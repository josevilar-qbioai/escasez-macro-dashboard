#!/usr/bin/env python3
"""
Genera docs/index.html — Dashboard Validación Tesis Escasez y Resiliencia
Sin dependencias externas. Lee historico/macro_snapshot.json.
Uso: python3 scripts/generate_dashboard.py
"""
import json, math, os, sys
from datetime import datetime
from pathlib import Path

ROOT     = Path(__file__).parent.parent
SNAP     = ROOT / "historico" / "macro_snapshot.json"
OUT_DIR  = ROOT / "docs"
OUT_FILE = OUT_DIR / "index.html"

# ── Cargar datos ──────────────────────────────────────────────────────────────
if not SNAP.exists():
    print(f"ERROR: {SNAP} no existe. Ejecuta primero macro_recorder.py")
    sys.exit(1)

with open(SNAP, encoding="utf-8") as f:
    snap = json.load(f)

ind     = snap.get("indicadores", {})
updated = snap.get("updated", "—")

# ── Helpers ───────────────────────────────────────────────────────────────────
def gv(k):
    """(valor, chg_1m, nombre)"""
    v = ind.get(k, {})
    return v.get("valor"), v.get("chg_1mes"), v.get("nombre", k)

def fval(v, dec=2, unit=""):
    if v is None: return "—"
    return f"{v:,.{dec}f}{unit}".replace(",", ".")

def fchg(c, unit="%"):
    if c is None: return '<span style="color:#888">—</span>'
    col = "#5cc98d" if c >= 0 else "#d97a6b"
    sign = "+" if c >= 0 else ""
    return f'<span style="color:{col}">{sign}{c:.1f}{unit}</span>'

# ── Calcular señales ──────────────────────────────────────────────────────────
sox_v,   sox_1m,  _  = gv("SOX")
cop_v,   cop_1m,  _  = gv("COPPER")
nas_v,   nas_1m,  _  = gv("NASDAQ")
robo_v,  robo_1m, _  = gv("ROBO")
qtum_v,  qtum_1m, _  = gv("QTUM")
btc_v,   btc_1m,  _  = gv("BTC")
ur_v,    ur_1m,   _  = gv("URANIUM")
xlu_v,   xlu_1m,  _  = gv("XLU")
gold_v,  gold_1m, _  = gv("GOLD")
sp_v,    sp_1m,   _  = gv("SPREAD")
vix_v,   vix_1m,  _  = gv("VIX")

sox_up   = sox_1m  is not None and sox_1m  >= 2
cop_up   = cop_1m  is not None and cop_1m  >= 2
nas_ok   = nas_1m  is not None and nas_1m  >= 2
robo_ok  = robo_1m is not None and robo_1m >= 2
qtum_ok  = qtum_1m is not None and qtum_1m >= 3
btc_mom  = btc_1m  is not None and btc_1m  >= 5
btc_beat = btc_1m  is not None and nas_1m  is not None and btc_1m > nas_1m
ur_ok    = ur_1m   is not None and ur_1m   >= 2
xlu_ok   = xlu_1m  is not None and xlu_1m  >= 1
gold_ok  = gold_1m is not None and gold_1m >= 2
spr_ok   = sp_v    is not None and sp_v    > 0.3
vix_ok   = vix_v   is not None and vix_v   < 20

checks = [sox_up, nas_ok, robo_ok, qtum_ok, btc_mom, btc_beat, ur_ok, xlu_ok, cop_up, gold_ok, spr_ok, vix_ok]
score_n   = sum(1 for c in checks if c)
score_pct = score_n / len(checks) * 100

if score_pct >= 65:
    score_label = "TESIS EN MARCHA"
    score_col   = "#5cc98d"
elif score_pct >= 40:
    score_label = "SEÑALES MIXTAS"
    score_col   = "#e0b341"
else:
    score_label = "TESIS DÉBIL"
    score_col   = "#d97a6b"

# Correlación SOX/Cobre
if sox_up and cop_up:
    corr_icon, corr_label, corr_col, corr_msg = (
        "●", "ERA DE CONSTRUCCIÓN", "#5cc98d",
        "Mantener metales + IA — tesis completa en marcha")
elif sox_up and not cop_up:
    corr_icon, corr_label, corr_col, corr_msg = (
        "●", "DIVERGENCIA · ALERTA", "#d97a6b",
        "Vigilar rotación: reducir mineras, reforzar IA pura")
elif not sox_up and cop_up:
    corr_icon, corr_label, corr_col, corr_msg = (
        "●", "ESCASEZ FÍSICA", "#e0b341",
        "Metales fuertes — esperar confirmación de rebote en SOX")
else:
    corr_icon, corr_label, corr_col, corr_msg = (
        "●", "CONTRACCIÓN", "#d97a6b",
        "Modo defensivo — esperar estabilización")

bar_pct = int(score_pct)

# ── Modelo TESIS ───────────────────────────────────────────────────────────────
import math as _math

TESIS_CAPITAL = 10_000   # inversión ejemplo en €
TESIS_T0      = 5        # año de inflexión (2026 + 5 = 2031)
TESIS_YEARS   = 10

TESIS_SCEN = {
    "BASE":      {"r": 0.20, "K": 2.0, "gamma": 0.50, "col": "#5cc98d",  "col_bg": "#5cc98d22"},
    "ÓPTIMO":    {"r": 0.25, "K": 4.0, "gamma": 0.90, "col": "#e0b341",  "col_bg": "#e0b34122"},
    "ACELERADO": {"r": 0.30, "K": 6.0, "gamma": 1.50, "col": "#6f9bd0",  "col_bg": "#6f9bd022"},
}

def phi_L(t, K, gamma, t0=TESIS_T0):
    return 1.0 + K / (1.0 + _math.exp(-gamma * (t - t0)))

def tesis_proj(r, K, gamma, t):
    phi0 = phi_L(0, K, gamma)
    return TESIS_CAPITAL * ((1 + r) ** t) * phi_L(t, K, gamma) / phi0

# Proyecciones año a año
tesis_data = {}
for name, sc in TESIS_SCEN.items():
    tesis_data[name] = [tesis_proj(sc["r"], sc["K"], sc["gamma"], t)
                        for t in range(TESIS_YEARS + 1)]

# SVG líneas (multi-serie)
def svg_line_chart(series, w=640, h=220):
    """series = [(label, [values], color)] — eje X = años 0..N"""
    if not series: return ""
    n_pts = len(series[0][1])
    all_vals = [v for _, vals, _ in series for v in vals]
    mn, mx = min(all_vals), max(all_vals)
    rng = mx - mn or 1
    pad_l, pad_r, pad_t, pad_b = 60, 20, 20, 30

    def cx(i): return pad_l + i * (w - pad_l - pad_r) / (n_pts - 1)
    def cy(v): return pad_t + (1 - (v - mn) / rng) * (h - pad_t - pad_b)

    elems = []
    # Grid lines horizontales
    for frac in [0, 0.25, 0.5, 0.75, 1.0]:
        y = pad_t + (1 - frac) * (h - pad_t - pad_b)
        val = mn + frac * rng
        elems.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-pad_r}" y2="{y:.1f}" stroke="#26303f" stroke-width="1"/>')
        label = f"€{val/1000:.0f}K" if val >= 1000 else f"€{val:.0f}"
        elems.append(f'<text x="{pad_l-4}" y="{y+4:.1f}" text-anchor="end" font-size="9" fill="#6b7688">{label}</text>')
    # Eje X: años
    for i in range(n_pts):
        x = cx(i)
        yr = 2026 + i
        if i % 2 == 0:
            elems.append(f'<text x="{x:.1f}" y="{h-6}" text-anchor="middle" font-size="9" fill="#6b7688">{yr}</text>')
    # Curvas
    for lbl, vals, col in series:
        pts = " ".join(f"{cx(i):.1f},{cy(v):.1f}" for i, v in enumerate(vals))
        elems.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.5" stroke-linejoin="round"/>')
        # Punto final con etiqueta
        xf, yf = cx(n_pts-1), cy(vals[-1])
        elems.append(f'<circle cx="{xf:.1f}" cy="{yf:.1f}" r="4" fill="{col}"/>')

    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
            f'style="width:100%;height:{h}px;display:block">'
            + "".join(elems) + "</svg>")

tesis_svg = svg_line_chart([
    (name, tesis_data[name], sc["col"])
    for name, sc in TESIS_SCEN.items()
])

# Tabla de proyección HTML
def tesis_table_html():
    rows = ""
    for t in range(TESIS_YEARS + 1):
        yr = 2026 + t
        bold = ' style="font-weight:700"' if t in (0, 5, 10) else ""
        row = f'<tr{bold}><td style="padding:4px 10px;color:#8592a6">{yr}</td>'
        for name, sc in TESIS_SCEN.items():
            v = tesis_data[name][t]
            vs = f"€{v:,.0f}".replace(",", ".")
            mult = v / TESIS_CAPITAL
            row += (f'<td style="padding:4px 10px;text-align:right;color:{sc["col"]}">'
                    f'{vs} <span style="color:#6b7688;font-size:.8em">×{mult:.1f}</span></td>')
        rows += row + "</tr>\n"
    return rows

tesis_rows = tesis_table_html()

# Tabla parámetros
def tesis_params_html():
    rows = ""
    for name, sc in TESIS_SCEN.items():
        f5  = tesis_data[name][5]
        f10 = tesis_data[name][10]
        rows += (f'<tr>'
                 f'<td style="padding:6px 10px;color:{sc["col"]};font-weight:700">{name}</td>'
                 f'<td style="padding:6px 10px;text-align:right;color:#e6eaf0">{sc["r"]:.0%}</td>'
                 f'<td style="padding:6px 10px;text-align:right;color:#e6eaf0">{sc["K"]:.1f}</td>'
                 f'<td style="padding:6px 10px;text-align:right;color:#e6eaf0">{sc["gamma"]:.2f}</td>'
                 f'<td style="padding:6px 10px;text-align:right;color:{sc["col"]}">€{f5:,.0f}</td>'
                 f'<td style="padding:6px 10px;text-align:right;color:{sc["col"]}">€{f10:,.0f}</td>'
                 f'</tr>\n')
    return rows

tesis_params_rows = tesis_params_html()

# ── SVG helpers ───────────────────────────────────────────────────────────────
def svg_bar_chart(data, w=640, h=160):
    """data = [(label, value, color)] — valores pueden ser negativos."""
    if not data: return ""
    vals   = [d[1] for d in data if d[1] is not None]
    if not vals: return ""
    mn, mx = min(min(vals), 0), max(max(vals), 0)
    rng    = mx - mn or 1
    pad    = 40
    bw     = (w - pad*2) / len(data)
    zero_y = pad + (mx / rng) * (h - pad*2)

    bars = []
    for i, (lbl, v, col) in enumerate(data):
        if v is None: continue
        x      = pad + i * bw + bw * 0.1
        bw2    = bw * 0.8
        bar_h  = abs(v) / rng * (h - pad*2)
        y      = zero_y - max(v, 0) / rng * (h - pad*2)
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw2:.1f}" height="{bar_h:.1f}" '
            f'fill="{col}" rx="3"/>')
        lbl_y  = h - 4
        bars.append(
            f'<text x="{x+bw2/2:.1f}" y="{lbl_y}" text-anchor="middle" '
            f'font-size="9" fill="#888">{lbl}</text>')
        sign = "+" if v >= 0 else ""
        val_y = y - 4 if v >= 0 else y + bar_h + 10
        bars.append(
            f'<text x="{x+bw2/2:.1f}" y="{val_y:.1f}" text-anchor="middle" '
            f'font-size="9" fill="{col}">{sign}{v:.1f}%</text>')

    # Zero line
    bars.append(
        f'<line x1="{pad}" y1="{zero_y:.1f}" x2="{w-pad}" y2="{zero_y:.1f}" '
        f'stroke="#444" stroke-width="1"/>')

    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
            f'style="width:100%;height:{h}px;display:block">'
            + "".join(bars) + "</svg>")


# Datos para el gráfico de barras (variación 1M de los indicadores clave)
chart_data = []
for k, lbl in [("SOX","SOX"), ("COPPER","Cobre"), ("NASDAQ","NASDAQ"),
                ("BTC","BTC"), ("URANIUM","Uranio"), ("XLU","XLU"),
                ("GOLD","Oro"), ("SP500","S&P500")]:
    v = ind.get(k, {}).get("chg_1mes")
    col = "#5cc98d" if (v is not None and v >= 0) else "#d97a6b"
    chart_data.append((lbl, v, col))

chart_svg = svg_bar_chart(chart_data)

# ── Señales por pilar (HTML) ──────────────────────────────────────────────────
def signal_row(icon, label, val_s, chg_html, condition, ok):
    dot = '<span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#5cc98d;vertical-align:middle"></span>' if ok else \
          '<span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#d97a6b;vertical-align:middle"></span>'
    return f"""
        <tr>
          <td style="padding:6px 10px;color:#ccc">{icon} {label}</td>
          <td style="padding:6px 10px;color:#fff;text-align:right">{val_s}</td>
          <td style="padding:6px 10px;text-align:right">{chg_html}</td>
          <td style="padding:6px 10px;color:#666;font-size:.85em">{condition}</td>
          <td style="padding:6px 10px;text-align:center">{dot}</td>
        </tr>"""

signals_html = ""
# Autoreplicación IA
signals_html += f'<tr><td colspan="5" style="padding:8px 10px 2px;color:#cf8b4f;font-weight:bold;font-size:.8em;letter-spacing:.1em">AUTOREPLICACIÓN IA</td></tr>'
signals_html += signal_row("📡","SOX Semiconductores", fval(sox_v,2,""),  fchg(sox_1m),  "+2%/1M", sox_up)
signals_html += signal_row("💻","NASDAQ Tech",          fval(nas_v,0,""),  fchg(nas_1m),  "+2%/1M", nas_ok)
signals_html += signal_row("🤖","ROBO Robótica",        fval(robo_v,2,""), fchg(robo_1m), "+2%/1M", robo_ok)
signals_html += signal_row("⚛","QTUM Cuántica",         fval(qtum_v,2,""), fchg(qtum_1m), "+3%/1M", qtum_ok)

signals_html += f'<tr><td colspan="5" style="padding:8px 10px 2px;color:#e0b341;font-weight:bold;font-size:.8em;letter-spacing:.1em">ESCASEZ DIGITAL</td></tr>'
signals_html += signal_row("₿","BTC momentum",        fval(btc_v,0,"€"), fchg(btc_1m), "+5%/1M", btc_mom)
btc_beat_chg  = fchg(btc_1m) if btc_1m is not None else '—'
signals_html += signal_row("₿","BTC vs NASDAQ",       "—", btc_beat_chg, "BTC > NASDAQ 1M", btc_beat)

signals_html += f'<tr><td colspan="5" style="padding:8px 10px 2px;color:#fb923c;font-weight:bold;font-size:.8em;letter-spacing:.1em">ENERGÍA / GRID</td></tr>'
signals_html += signal_row("⚛️","Uranio (Cameco)",     fval(ur_v,2,"$"), fchg(ur_1m), "+2%/1M", ur_ok)
signals_html += signal_row("⚡","XLU Utilities",       fval(xlu_v,2,"$"), fchg(xlu_1m), "+1%/1M", xlu_ok)

signals_html += f'<tr><td colspan="5" style="padding:8px 10px 2px;color:#86efac;font-weight:bold;font-size:.8em;letter-spacing:.1em">ESCASEZ FÍSICA</td></tr>'
signals_html += signal_row("🟠","Cobre",               fval(cop_v,3,"$"), fchg(cop_1m), "+2%/1M", cop_up)
signals_html += signal_row("🥇","Oro",                  fval(gold_v,0,"$"), fchg(gold_1m), "+2%/1M", gold_ok)

signals_html += f'<tr><td colspan="5" style="padding:8px 10px 2px;color:#94a3b8;font-weight:bold;font-size:.8em;letter-spacing:.1em">RESILIENCIA</td></tr>'
signals_html += signal_row("📈","Spread 10Y-13W",      fval(sp_v,2,"%"), "—", ">0.3%", spr_ok)
signals_html += signal_row("😰","VIX Volatilidad",     fval(vix_v,1,""), "—", "<20", vix_ok)

# Contexto
def ctx_row(k, label, dec=2, unit=""):
    v, c1m, _ = gv(k)
    return f"""<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #26303f">
      <span style="color:#94a3b8">{label}</span>
      <span style="color:#fff">{fval(v,dec,unit)}&nbsp;&nbsp;{fchg(c1m)}</span>
    </div>"""

ctx_html  = ctx_row("SP500",  "S&P 500",    0)
ctx_html += ctx_row("VIX",    "VIX",        1)
ctx_html += ctx_row("SPREAD", "Spread 10Y-13W", 2, "%")
ctx_html += ctx_row("EURUSD", "EUR/USD",    4)
ctx_html += ctx_row("GOLD",   "Oro (USD)",  0, "$")
ctx_html += ctx_row("OIL",    "Petróleo WTI", 1, "$")

# ── Régimen macro (FRED) ───────────────────────────────────────────────────────
def fred_row(k, label, cond, ok_fn, dec=2, unit=""):
    v, c1m, _ = gv(k)
    u  = ind.get(k, {}).get("chg_unit", "%")
    ok = ok_fn(v, c1m) if v is not None else False
    return signal_row("", label, fval(v, dec, unit), fchg(c1m, u), cond, ok)

fred_present = ind.get("REAL10Y") is not None
fred_html = ""
if fred_present:
    fred_html += fred_row("REAL10Y",   "Tipos reales 10a (TIPS)", "cae = favorable",       lambda v, c: c is not None and c <= 0, 2, "%")
    fred_html += fred_row("M2",        "M2 EE.UU.",               "sube = favorable",      lambda v, c: c is not None and c >= 0, 1)
    fred_html += fred_row("FEDBS",     "Balance Fed",             "sube = favorable",      lambda v, c: c is not None and c >= 0, 0)
    fred_html += fred_row("HYSPREAD",  "Spread High Yield",       "< 4% = sano",           lambda v, c: v is not None and v < 4.0, 2, "%")
    fred_html += fred_row("BREAKEVEN", "Inflación esperada 10a",  "sube = activos reales", lambda v, c: c is not None and c >= 0, 2, "%")

fred_card = f"""
  <div class="card">
    <h2 style="color:#8592a6">RÉGIMEN MACRO · FRED</h2>
    <div style="overflow-x:auto">
    <table>
      <thead><tr style="border-bottom:1px solid #26303f">
        <th style="padding:6px 10px;text-align:left;color:#6b7688;font-weight:500;font-size:.8em">SEÑAL</th>
        <th style="padding:6px 10px;text-align:right;color:#6b7688;font-weight:500;font-size:.8em">VALOR</th>
        <th style="padding:6px 10px;text-align:right;color:#6b7688;font-weight:500;font-size:.8em">1 MES</th>
        <th style="padding:6px 10px;color:#6b7688;font-weight:500;font-size:.8em">CONDICIÓN</th>
        <th style="padding:6px 10px;text-align:center;color:#6b7688;font-weight:500;font-size:.8em"></th>
      </tr></thead>
      <tbody>{fred_html}</tbody>
    </table>
    </div>
    <p style="color:#55617a;font-size:.72rem;margin-top:8px">Fuente: FRED (Fed de San Luis). Los «gates» del régimen: tipos reales, liquidez (M2), balance de la Fed, crédito e inflación esperada.</p>
  </div>""" if fred_present else ""

# ── Escasez física: inventarios (cobre LME, uranio spot) ───────────────────────
fund_html = ""
if ind.get("COPPER_STOCK") is not None:
    fund_html += fred_row("COPPER_STOCK", "Inventario cobre LME", "cae = escasez", lambda v, c: c is not None and c < 0, 0, " t")
if ind.get("URANIUM_SPOT") is not None:
    fund_html += fred_row("URANIUM_SPOT", "Uranio spot U3O8",     "sube = déficit", lambda v, c: c is not None and c > 0, 2, "$")

fund_card = f"""
  <div class="card">
    <h2 style="color:#8592a6">ESCASEZ FÍSICA · INVENTARIOS</h2>
    <div style="overflow-x:auto">
    <table>
      <thead><tr style="border-bottom:1px solid #26303f">
        <th style="padding:6px 10px;text-align:left;color:#6b7688;font-weight:500;font-size:.8em">SEÑAL</th>
        <th style="padding:6px 10px;text-align:right;color:#6b7688;font-weight:500;font-size:.8em">VALOR</th>
        <th style="padding:6px 10px;text-align:right;color:#6b7688;font-weight:500;font-size:.8em">CAMBIO</th>
        <th style="padding:6px 10px;color:#6b7688;font-weight:500;font-size:.8em">CONDICIÓN</th>
        <th style="padding:6px 10px;text-align:center;color:#6b7688;font-weight:500;font-size:.8em"></th>
      </tr></thead>
      <tbody>{fund_html}</tbody>
    </table>
    </div>
    <p style="color:#55617a;font-size:.72rem;margin-top:8px">Inventario de cobre en almacenes LME (Westmetall) y precio spot del uranio U3O8 (Yellowcake plc). Stock de cobre cayendo o uranio al alza = escasez física.</p>
  </div>""" if fund_html else ""

# ── Generar HTML ──────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<title>⚡ Tesis Escasez y Resiliencia</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  :root{{
    --bg:#0e141d; --card:#161e2b; --card2:#1a2331; --border:#26303f;
    --text:#e6eaf0; --muted:#93a1b5; --faint:#69768a; --accent:#cf8b4f;
  }}
  body{{background:var(--bg);color:var(--text);
    font-family:'Inter',system-ui,-apple-system,sans-serif;min-height:100vh;
    -webkit-font-smoothing:antialiased;font-feature-settings:"tnum" 1}}
  .num,.val,.kpi .val,table td,table th{{font-variant-numeric:tabular-nums}}
  .wrap{{max-width:920px;margin:0 auto;padding:32px 18px 56px}}
  h1{{font-size:1.35rem;font-weight:700;letter-spacing:-.01em}}
  h2{{font-size:.72rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);margin-bottom:14px}}
  .card{{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:22px 24px;margin-bottom:16px}}
  .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
  @media(max-width:600px){{.grid2{{grid-template-columns:1fr}}.wrap{{padding:22px 14px 44px}}}}
  .kpi{{text-align:center}}
  .kpi .val{{font-size:1.9rem;font-weight:700;line-height:1.1;letter-spacing:-.02em}}
  .kpi .lbl{{font-size:.72rem;color:var(--faint);margin-top:5px;text-transform:uppercase;letter-spacing:.08em}}
  table{{width:100%;border-collapse:collapse;font-size:.9rem}}
  .bar-bg{{background:var(--border);border-radius:999px;height:8px;overflow:hidden;margin:10px 0}}
  .bar-fg{{height:8px;border-radius:999px;transition:width .4s}}
  .tag{{display:inline-block;padding:4px 12px;border-radius:999px;font-size:.75rem;font-weight:600;letter-spacing:.02em}}
  .upd{{color:var(--faint);font-size:.78rem}}
</style>
</head>
<body>
<div class="wrap">

  <!-- Header -->
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px;flex-wrap:wrap;gap:8px">
    <div>
      <h1>⚡ Tesis Escasez y Resiliencia</h1>
      <p style="color:#6b7688;font-size:.85rem;margin-top:4px">
        V(t) = Capital × (1+r)ᵗ × Φ_L(t) &nbsp;·&nbsp; Qmetrika Labs
      </p>
    </div>
    <div style="text-align:right">
      <span class="tag" style="background:{score_col}22;color:{score_col};border:1px solid {score_col}44">
        {score_label}
      </span>
      <p class="upd" style="margin-top:6px">Datos: {updated}</p>
    </div>
  </div>

  <!-- Score y correlación SOX/Cobre -->
  <div class="card">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap;gap:8px">
      <h2 style="margin:0;color:#cf8b4f">⚡ SCORE ESCASEZ</h2>
      <span style="font-size:1.5rem;font-weight:700;color:{score_col}">{score_pct:.0f}%
        <span style="font-size:.9rem;color:#8592a6">({score_n}/12)</span>
      </span>
    </div>
    <div class="bar-bg">
      <div class="bar-fg" style="width:{bar_pct}%;background:{score_col}"></div>
    </div>
    <div style="margin-top:16px;padding:14px;background:#0e141d;border-radius:8px;border-left:3px solid {corr_col}">
      <div style="font-size:1rem;font-weight:700;color:{corr_col}">
        {corr_icon} CORRELACIÓN SOX/COBRE — {corr_label}
      </div>
      <div style="color:#94a3b8;font-size:.85rem;margin-top:6px">{corr_msg}</div>
      <div style="color:#8592a6;font-size:.8rem;margin-top:8px">
        SOX {fval(sox_v,2)} ({fchg(sox_1m)}/1M) &nbsp;·&nbsp; Cobre {fval(cop_v,3,"$")} ({fchg(cop_1m)}/1M)
      </div>
    </div>
  </div>

  <!-- KPIs rápidos -->
  <div class="grid2">
    <div class="card kpi">
      <div class="val" style="color:#cf8b4f">{fval(sox_v,0)}</div>
      <div class="lbl">SOX Semiconductores</div>
      <div style="margin-top:6px">{fchg(sox_1m)} en 1 mes</div>
    </div>
    <div class="card kpi">
      <div class="val" style="color:#fb923c">{fval(cop_v,3,"$")}</div>
      <div class="lbl">Cobre (USD/lb)</div>
      <div style="margin-top:6px">{fchg(cop_1m)} en 1 mes</div>
    </div>
    <div class="card kpi">
      <div class="val" style="color:#e0b341">₿ {fval(btc_v,0,"€")}</div>
      <div class="lbl">Bitcoin (EUR)</div>
      <div style="margin-top:6px">{fchg(btc_1m)} en 1 mes</div>
    </div>
    <div class="card kpi">
      <div class="val" style="color:#94a3b8">{fval(vix_v,1)}</div>
      <div class="lbl">VIX Volatilidad</div>
      <div style="margin-top:6px;color:{'#5cc98d' if vix_ok else '#d97a6b'}">
        {'< 20 — entorno favorable' if vix_ok else '≥ 20 — precaución'}
      </div>
    </div>
  </div>

  <!-- Gráfico variación 1M -->
  <div class="card">
    <h2 style="color:#8592a6">VARIACIÓN 1 MES — INDICADORES CLAVE</h2>
    {chart_svg}
  </div>

  <!-- Señales por pilar -->
  <div class="card">
    <h2 style="color:#8592a6">SEÑALES POR PILAR</h2>
    <div style="overflow-x:auto">
    <table>
      <thead>
        <tr style="border-bottom:1px solid #26303f">
          <th style="padding:6px 10px;text-align:left;color:#6b7688;font-weight:500;font-size:.8em">SEÑAL</th>
          <th style="padding:6px 10px;text-align:right;color:#6b7688;font-weight:500;font-size:.8em">VALOR</th>
          <th style="padding:6px 10px;text-align:right;color:#6b7688;font-weight:500;font-size:.8em">1 MES</th>
          <th style="padding:6px 10px;color:#6b7688;font-weight:500;font-size:.8em">CONDICIÓN</th>
          <th style="padding:6px 10px;text-align:center;color:#6b7688;font-weight:500;font-size:.8em"></th>
        </tr>
      </thead>
      <tbody>{signals_html}</tbody>
    </table>
    </div>
  </div>

  <!-- Régimen macro (FRED) -->
  {fred_card}

  <!-- Escasez física · inventarios -->
  {fund_card}

  <!-- Contexto -->
  <div class="card">
    <h2 style="color:#8592a6">CONTEXTO DE MERCADO</h2>
    {ctx_html}
  </div>

  <!-- Tesis: proyección logística -->
  <div class="card">
    <h2 style="color:#8592a6">TESIS — V(t) = Capital × (1+r)ᵗ × Φ_L(t) / Φ_L(0)</h2>
    <p style="color:#6b7688;font-size:.8rem;margin-bottom:16px">
      Φ_L(t) = 1 + K / (1 + e<sup>−γ·(t−t₀)</sup>) &nbsp;·&nbsp;
      t₀ = {TESIS_T0} (año {2026 + TESIS_T0}) &nbsp;·&nbsp;
      Inversión ejemplo: €{TESIS_CAPITAL:,}
    </p>

    <!-- Leyenda -->
    <div style="display:flex;gap:20px;margin-bottom:12px;flex-wrap:wrap">
      {"".join(
        f'<span style="color:{sc["col"]};font-weight:700;font-size:.85rem">▬ {name}</span>'
        for name, sc in TESIS_SCEN.items()
      )}
    </div>

    <!-- Gráfico curvas -->
    {tesis_svg}

    <!-- Parámetros -->
    <div style="overflow-x:auto;margin-top:16px">
    <table>
      <thead>
        <tr style="border-bottom:1px solid #26303f">
          <th style="padding:6px 10px;text-align:left;color:#6b7688;font-size:.8em">ESCENARIO</th>
          <th style="padding:6px 10px;text-align:right;color:#6b7688;font-size:.8em">r</th>
          <th style="padding:6px 10px;text-align:right;color:#6b7688;font-size:.8em">K</th>
          <th style="padding:6px 10px;text-align:right;color:#6b7688;font-size:.8em">γ</th>
          <th style="padding:6px 10px;text-align:right;color:#6b7688;font-size:.8em">€ año 5</th>
          <th style="padding:6px 10px;text-align:right;color:#6b7688;font-size:.8em">€ año 10</th>
        </tr>
      </thead>
      <tbody>{tesis_params_rows}</tbody>
    </table>
    </div>

    <!-- Tabla año a año -->
    <details style="margin-top:16px">
      <summary style="color:#6b7688;font-size:.8rem;cursor:pointer;user-select:none">
        Ver proyección año a año ▸
      </summary>
      <div style="overflow-x:auto;margin-top:10px">
      <table>
        <thead>
          <tr style="border-bottom:1px solid #26303f">
            <th style="padding:4px 10px;text-align:left;color:#6b7688;font-size:.8em">AÑO</th>
            {"".join(f'<th style="padding:4px 10px;text-align:right;color:{sc["col"]};font-size:.8em">{name}</th>' for name, sc in TESIS_SCEN.items())}
          </tr>
        </thead>
        <tbody>{tesis_rows}</tbody>
      </table>
      </div>
    </details>
  </div>

  <!-- Footer -->
  <div style="text-align:center;color:#55617a;font-size:.75rem;margin-top:24px;line-height:1.8">
    V(t) = Capital × (1+r)ᵗ × Φ_L(t) &nbsp;·&nbsp; Φ_L(t) = 1 + K/(1+e^(−γ·(t−t₀)))<br>
    Fuente: Yahoo Finance · Actualizado: {updated}<br>
    Qmetrika Labs
  </div>

</div>
</body>
</html>"""

# ── Guardar ───────────────────────────────────────────────────────────────────
OUT_DIR.mkdir(exist_ok=True)
OUT_FILE.write_text(html, encoding="utf-8")
print(f"OK  {len(html):,} chars  →  {OUT_FILE}")
