#!/usr/bin/env python3
"""
macro_recorder.py — Descarga indicadores macroeconómicos y los guarda en JSON.
════════════════════════════════════════════════════════════════════════════════
Descarga datos de Yahoo Finance (yfinance) para los principales indicadores
macro: VIX, S&P 500, NASDAQ, Euro Stoxx 50, tipos de interés EEUU, divisas,
materias primas y Bitcoin.

El resultado se guarda en `historico/macro_snapshot.json` y es leído por el
dashboard para mostrar la pestaña ⑨ MACRO.

Uso:
  python3 scripts/macro_recorder.py -d historico
  python3 scripts/macro_recorder.py -d historico --show
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ── Tickers a descargar ────────────────────────────────────────────────────────
# (ticker_yf, clave_json, nombre_display, unidad, decimales)
MACRO_TICKERS = [
    # Mercados
    ("^VIX",       "VIX",       "VIX Volatilidad",       "",       2),
    ("^GSPC",      "SP500",     "S&P 500",               "",       2),
    ("^IXIC",      "NASDAQ",    "NASDAQ Composite",      "",       2),
    ("^STOXX50E",  "STOXX50",   "Euro Stoxx 50",         "",       2),
    # Tipos de interés EEUU
    ("^TNX",       "US10Y",     "Bono EEUU 10 años",     "%",      3),
    ("^IRX",       "US13W",     "T-Bill 13 semanas",     "%",      3),
    # Divisas
    ("EURUSD=X",   "EURUSD",    "EUR / USD",             "",       4),
    ("DX-Y.NYB",   "USDIDX",    "Índice USD (DXY)",      "",       2),
    # Materias primas
    ("GC=F",       "GOLD",      "Oro (USD/oz)",          "",       2),
    ("CL=F",       "OIL",       "Petróleo WTI (USD/bbl)","",       2),
    ("HG=F",       "COPPER",    "Cobre (USD/lb)",        "",       4),
    # Energía
    ("CCJ",        "URANIUM",   "Uranio · Cameco (USD)", "",       2),
    ("NG=F",       "GAS",       "Gas Natural (USD/MMBtu)","",      3),
    # IA · Data Centers · Energía digital
    ("XLU",        "XLU",       "Utilities EEUU (XLU)",  "",       2),
    ("^SOX",       "SOX",       "Semiconductores (SOX)", "",       2),
    ("ROBO",       "ROBO",      "Robótica global (ROBO ETF)", "",  2),
    ("QTUM",       "QTUM",      "Computación Cuántica (QTUM)", "", 2),
    # Cripto
    ("BTC-USD",    "BTC",       "Bitcoin (USD)",         "",       0),
]

SNAPSHOT_FILE = "macro_snapshot.json"

# ── Series FRED (régimen macro) ────────────────────────────────────────────────
# La API key se lee de la variable de entorno FRED_API_KEY (secret de GitHub).
# (series_id, clave_json, nombre, unidad, decimales, modo_cambio, escala)
#   modo_cambio: "bp" (puntos básicos, para %) o "pct" (variación porcentual)
FRED_SERIES = [
    ("DFII10",       "REAL10Y",   "Tipos reales 10a (TIPS)", "%", 2, "bp",  1),
    ("T10YIE",       "BREAKEVEN", "Inflación esperada 10a",  "%", 2, "bp",  1),
    ("M2SL",         "M2",        "M2 EE.UU. (bn $)",        "",  1, "pct", 1),
    ("WALCL",        "FEDBS",     "Balance Fed (bn $)",      "",  0, "pct", 0.001),
    ("BAMLH0A0HYM2", "HYSPREAD",  "Spread High Yield",       "%", 2, "bp",  1),
]


def fetch_fred(result: dict):
    """Añade indicadores macro de FRED a result['indicadores'] (si hay API key)."""
    key = os.environ.get("FRED_API_KEY", "").strip()
    if not key:
        print("  (FRED_API_KEY no definido — se omiten los indicadores FRED)")
        return
    try:
        import requests
    except ImportError:
        print("  ⚠  requests no instalado — se omiten los indicadores FRED")
        return

    base = "https://api.stlouisfed.org/fred/series/observations"
    print(f"Descargando {len(FRED_SERIES)} indicadores FRED…")
    for sid, k, nombre, unidad, dec, modo, escala in FRED_SERIES:
        try:
            r = requests.get(base, params={
                "series_id": sid, "api_key": key, "file_type": "json",
                "sort_order": "desc", "limit": 400}, timeout=25)
            obs = r.json().get("observations", [])
            pts = [(o["date"], float(o["value"]) * escala)
                   for o in obs if o.get("value") not in (".", "", None)]
            if not pts:
                print(f"  ⚠  {k} ({sid}): sin datos")
                continue
            d0, v0 = pts[0]  # más reciente (orden desc)
            base_date = datetime.strptime(d0, "%Y-%m-%d").date()

            def val_atras(dias):
                objetivo = base_date - timedelta(days=dias)
                for ds, vv in pts:  # desc → primer punto con fecha <= objetivo
                    if datetime.strptime(ds, "%Y-%m-%d").date() <= objetivo:
                        return vv
                return None

            v1s, v1m = val_atras(7), val_atras(30)
            if modo == "bp":
                c1s = round((v0 - v1s) * 100, 1) if v1s is not None else None
                c1m = round((v0 - v1m) * 100, 1) if v1m is not None else None
                chg_unit = "bp"
            else:
                c1s = round((v0 - v1s) / abs(v1s) * 100, 2) if v1s else None
                c1m = round((v0 - v1m) / abs(v1m) * 100, 2) if v1m else None
                chg_unit = "%"

            result["indicadores"][k] = {
                "nombre": nombre, "unidad": unidad, "decimales": dec,
                "chg_unit": chg_unit, "valor": round(v0, max(dec, 2)),
                "fecha": d0, "chg_1d": None, "chg_1sem": c1s, "chg_1mes": c1m,
            }
            print(f"  ✓  {k:9s} {v0:>12.{dec}f}{unidad}  (FRED {sid})")
        except Exception as e:
            print(f"  ✗  {k} ({sid}): {e}")


def pct_change(new_val, old_val):
    """Calcula la variación porcentual (None si no hay datos)."""
    if old_val and old_val != 0 and new_val is not None:
        return round((new_val - old_val) / abs(old_val) * 100, 2)
    return None


def bp_change(new_val, old_val):
    """Variación en puntos básicos para tipos de interés."""
    if old_val is not None and new_val is not None:
        return round((new_val - old_val) * 100, 1)   # en bp
    return None


def fetch_macro_data() -> dict:
    """Descarga todos los indicadores con yfinance y devuelve el snapshot."""
    try:
        import yfinance as yf
    except ImportError:
        print("ERROR: yfinance no está instalado.")
        print("       pip install yfinance --break-system-packages")
        sys.exit(1)

    result = {
        "updated":     datetime.now().strftime("%Y-%m-%d %H:%M"),
        "indicadores": {},
    }

    print(f"Descargando {len(MACRO_TICKERS)} indicadores macro…")

    for yf_ticker, key, nombre, unidad, decimales in MACRO_TICKERS:
        try:
            t   = yf.Ticker(yf_ticker)
            df  = t.history(period="35d", auto_adjust=True)

            if df.empty or len(df) < 2:
                print(f"  ⚠  {key} ({yf_ticker}): sin datos")
                continue

            closes  = list(df["Close"].dropna())
            dates   = [d.strftime("%Y-%m-%d") for d in df.index]

            if not closes:
                continue

            val_hoy   = round(float(closes[-1]), max(decimales, 2))
            val_ayer  = round(float(closes[-2]), max(decimales, 2)) if len(closes) >= 2  else None
            val_1sem  = round(float(closes[-6]), max(decimales, 2)) if len(closes) >= 6  else None
            val_1mes  = round(float(closes[-22]), max(decimales, 2)) if len(closes) >= 22 else None

            # Variaciones
            if unidad == "%":
                # Tipos de interés → puntos básicos
                chg_1d   = bp_change(val_hoy, val_ayer)
                chg_1sem = bp_change(val_hoy, val_1sem)
                chg_1mes = bp_change(val_hoy, val_1mes)
                chg_unit = "bp"
            else:
                chg_1d   = pct_change(val_hoy, val_ayer)
                chg_1sem = pct_change(val_hoy, val_1sem)
                chg_1mes = pct_change(val_hoy, val_1mes)
                chg_unit = "%"

            result["indicadores"][key] = {
                "nombre":    nombre,
                "unidad":    unidad,
                "decimales": decimales,
                "chg_unit":  chg_unit,
                "valor":     val_hoy,
                "fecha":     dates[-1] if dates else "",
                "chg_1d":    chg_1d,
                "chg_1sem":  chg_1sem,
                "chg_1mes":  chg_1mes,
            }

            flecha = "↑" if (chg_1d or 0) >= 0 else "↓"
            print(f"  ✓  {key:8s}  {val_hoy:>12.{decimales}f}{unidad}  1d {flecha}{abs(chg_1d or 0):.1f}{chg_unit}")

        except Exception as e:
            print(f"  ✗  {key} ({yf_ticker}): {e}")

    # ── Spread 10Y − 13W (curva de tipos) ──────────────────────────────────────
    try:
        us10 = result["indicadores"].get("US10Y", {}).get("valor")
        us13 = result["indicadores"].get("US13W", {}).get("valor")
        if us10 is not None and us13 is not None:
            result["indicadores"]["SPREAD"] = {
                "nombre":    "Curva tipos 10Y−13W",
                "unidad":    "%",
                "decimales": 3,
                "chg_unit":  "bp",
                "valor":     round(us10 - us13, 3),
                "fecha":     result["indicadores"].get("US10Y", {}).get("fecha", ""),
                "chg_1d":    None,
                "chg_1sem":  None,
                "chg_1mes":  None,
            }
            print(f"  ✓  SPREAD   {us10 - us13:>+.3f}%  (10Y − 13W)")
    except Exception:
        pass

    # ── Régimen macro vía FRED ──────────────────────────────────────────────────
    fetch_fred(result)

    # ── Escasez física: inventario de cobre (LME) y uranio spot ────────────────
    fetch_inventarios(result)

    return result


def fetch_inventarios(result: dict):
    """Añade inventario de cobre (Westmetall/LME) y uranio spot (Yellowcake).
    Fuentes públicas gratuitas; si fallan, se omiten sin romper el pipeline."""
    try:
        import requests
    except ImportError:
        print("  ⚠  requests no instalado — se omiten inventarios")
        return
    hoy = datetime.now().strftime("%Y-%m-%d")

    # Cobre: stock LME en toneladas (Westmetall publica precio y stock)
    try:
        h = requests.get("https://www.westmetall.com/en/markdaten.php",
                         timeout=25, headers={"User-Agent": "Mozilla/5.0"}).text
        import re
        m = re.findall(r'>\s*Copper\s*</a>.*?<td>\s*<a[^>]*>\s*([\d,\.]+)\s*</a>'
                       r'.*?<td class="last">\s*<a[^>]*>\s*([+\-−–]?[\d,\.]+)', h, re.S)
        if len(m) >= 2:  # m[0] = precio, m[1] = stock
            stock = float(m[1][0].replace(",", ""))
            craw = m[1][1].replace("−", "-").replace("–", "-").replace(",", "")
            chg_t = float(craw) if craw not in ("", "-") else None
            chg_pct = round(chg_t / (stock - chg_t) * 100, 2) if chg_t else None
            result["indicadores"]["COPPER_STOCK"] = {
                "nombre": "Inventario cobre LME (t)", "unidad": "t", "decimales": 0,
                "chg_unit": "%", "valor": round(stock), "fecha": hoy,
                "chg_1d": chg_pct, "chg_1sem": None, "chg_1mes": None,
            }
            print(f"  ✓  COPPER_STOCK {stock:>12,.0f} t  ({chg_t:+.0f} t)")
        else:
            print("  ⚠  COPPER_STOCK: no se pudo parsear Westmetall")
    except Exception as e:
        print(f"  ✗  COPPER_STOCK: {e}")

    # Uranio: spot U3O8 (Yellowcake plc, texto)
    try:
        import re
        t = requests.get("https://www.yellowcakeplc.com/api/spotUraniumPrice.php",
                         timeout=25).text
        pr = re.search(r'US\$([\d.]+)/lb', t)
        cg = re.search(r'([+\-][\d.]+),\s*([+\-][\d.]+)%', t)
        if pr:
            result["indicadores"]["URANIUM_SPOT"] = {
                "nombre": "Uranio spot U3O8 ($/lb)", "unidad": "$", "decimales": 2,
                "chg_unit": "%", "valor": float(pr.group(1)), "fecha": hoy,
                "chg_1d": float(cg.group(2)) if cg else None,
                "chg_1sem": None, "chg_1mes": None,
            }
            print(f"  ✓  URANIUM_SPOT {float(pr.group(1)):>8.2f} $/lb")
        else:
            print("  ⚠  URANIUM_SPOT: no se pudo parsear Yellowcake")
    except Exception as e:
        print(f"  ✗  URANIUM_SPOT: {e}")


def save_snapshot(data: dict, hist_dir: Path) -> Path:
    """Guarda el snapshot en historico/macro_snapshot.json."""
    hist_dir.mkdir(parents=True, exist_ok=True)
    out = hist_dir / SNAPSHOT_FILE
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return out


def print_snapshot(data: dict):
    """Muestra un resumen del snapshot en consola."""
    print()
    print(f"  Actualizado: {data['updated']}")
    print()
    ind = data.get("indicadores", {})

    def fmt_chg(val, unit):
        if val is None: return "      "
        sign = "+" if val >= 0 else ""
        return f"{sign}{val:.1f}{unit}"

    ORDER = ["VIX","SP500","NASDAQ","STOXX50",
             "US13W","US10Y","SPREAD",
             "EURUSD","USDIDX","GOLD","OIL","BTC"]
    for k in ORDER:
        v = ind.get(k)
        if not v: continue
        dec   = v.get("decimales", 2)
        u     = v.get("unidad", "")
        chgu  = v.get("chg_unit", "%")
        c1d   = fmt_chg(v.get("chg_1d"), chgu)
        c1m   = fmt_chg(v.get("chg_1mes"), chgu)
        print(f"  {k:8s}  {v['nombre']:<30s} {v['valor']:>12.{dec}f}{u:1s}  "
              f"1d:{c1d:>8s}  1m:{c1m:>8s}")


def main():
    parser = argparse.ArgumentParser(
        description="Descarga indicadores macro y guarda macro_snapshot.json"
    )
    parser.add_argument("-d", "--dir",  default="historico",
                        help="Directorio donde guardar el snapshot (default: historico/)")
    parser.add_argument("--show", action="store_true",
                        help="Muestra el resumen tras guardar")
    args = parser.parse_args()

    hist_dir = Path(args.dir)
    if not hist_dir.is_absolute():
        hist_dir = Path.cwd() / hist_dir

    data = fetch_macro_data()
    out  = save_snapshot(data, hist_dir)
    print(f"\nSnapshot guardado: {out}")

    if args.show:
        print_snapshot(data)


if __name__ == "__main__":
    main()
